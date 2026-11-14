#!/usr/bin/env python
"""Installed content packs of a Unity project, for the "packs first" rule.

  python find-packs.py <project> [--own Game,Scenes,Settings] [--store <Asset Store dir>] [--json]

Prints three groups:
  1. packs inside Assets/ (top folders, or publisher/pack two levels deep) with counts of models, prefabs,
     textures, materials, animations and audio — usable right now;
  2. Asset Store downloads (.unitypackage) not imported into this project — one import away
     (extract-unitypackage.py imports without the editor's modal dialog);
  3. UPM packages from Packages/manifest.json that usually carry content (samples, art, audio).
The game's own folders are skipped: --own lists them (default: Game, Scenes, Settings, Resources, Plugins,
Editor, StreamingAssets, TextMesh Pro, TutorialInfo).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

KINDS = {
    "models": {".fbx", ".obj", ".blend", ".dae", ".3ds", ".gltf", ".glb"},
    "prefabs": {".prefab"},
    "textures": {".png", ".tga", ".psd", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".hdr"},
    "materials": {".mat"},
    "anims": {".anim", ".controller"},
    "audio": {".wav", ".ogg", ".mp3", ".aiff", ".aif", ".flac"},
    "scenes": {".unity"},
}
DEFAULT_OWN = ["Game", "Scenes", "Settings", "Resources", "Plugins", "Editor", "StreamingAssets",
               "TextMesh Pro", "TutorialInfo", "Samples", "Tests"]
for _s in (sys.stdout, sys.stderr):  # UTF-8 into pipes and files (the agent reads them); never crash in a console
    try:
        _s.reconfigure(encoding="utf-8" if not _s.isatty() else _s.encoding, errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

CONTENT_UPM = re.compile(r"(art|asset|audio|sound|music|sfx|model|anim|character|environment|prop|texture|vfx|fx)", re.I)


def count(folder):
    c = {k: 0 for k in KINDS}
    size = 0
    for root, _, files in os.walk(folder):
        for f in files:
            if f.endswith(".meta"):
                continue
            ext = os.path.splitext(f)[1].lower()
            for k, exts in KINDS.items():
                if ext in exts:
                    c[k] += 1
            try:
                size += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    c["mb"] = round(size / 2**20, 1)
    return c


def content(c):
    return sum(v for k, v in c.items() if k != "mb")


def project_packs(assets, own):
    out = []
    for top in sorted(p for p in assets.iterdir() if p.is_dir() and p.name not in own):
        c = count(top)
        if content(c) == 0:
            continue
        subs = [s for s in sorted(top.iterdir()) if s.is_dir()]
        # Publisher folder (several packs inside, e.g. Synty/PolygonX, ithappy/Zombies_Pack): list them one by one.
        packs = [(s, count(s)) for s in subs]
        packs = [(s, sc) for s, sc in packs if content(sc) > 0]
        looks_like_publisher = len(packs) >= 2 and all(sc["prefabs"] + sc["models"] > 0 for _, sc in packs[:2])
        if looks_like_publisher:
            for s, sc in packs:
                out.append({"pack": f"{top.name}/{s.name}", **sc})
        else:
            out.append({"pack": top.name, **c})
    return out


STOP = {"pack", "packs", "free", "asset", "assets", "the", "of", "and", "low", "poly", "set", "sets", "3d", "hd",
        "lite", "mega", "kit", "v2", "objects", "collection"}


def tokens(name):
    # "HorrorBundleSFX" -> horror bundle sfx; "CRT_&_Slimline_Monitors_Pack" -> crt slimline monitor
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    out = set()
    for t in re.split(r"[^A-Za-z0-9]+", s.lower()):
        t = t[:-1] if len(t) > 3 and t.endswith("s") else t
        if t and t not in STOP:
            out.add(t)
    return out


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def store_cache(store, folders):
    """folders: names of pack folders in Assets (top and publisher/pack)."""
    out = []
    if not store or not store.is_dir():
        return out
    folder_tokens = [(f, tokens(f)) for f in folders]
    folder_keys = {norm(f) for f in folders}
    for pkg in sorted(store.rglob("*.unitypackage")):
        rel = pkg.relative_to(store)
        publisher = rel.parts[0] if len(rel.parts) > 1 else ""
        category = rel.parts[1] if len(rel.parts) > 2 else ""
        name = pkg.stem
        why = ""
        pt = tokens(name)
        for f, ft in folder_tokens:
            if norm(f) in norm(name) or len(pt & ft) >= 2:
                why = f"looks imported as Assets/{f}"
                break
        if not why and norm(publisher) in folder_keys:
            why = f"publisher folder Assets/{publisher} exists: check whether this pack is in it"
        out.append({"package": name, "publisher": publisher, "category": category,
                    "mb": round(pkg.stat().st_size / 2**20, 1), "imported": why, "path": str(pkg)})
    return out


def upm_content(project):
    man = project / "Packages" / "manifest.json"
    if not man.exists():
        return []
    try:
        deps = json.loads(man.read_text(encoding="utf-8")).get("dependencies", {})
    except (ValueError, OSError):
        return []
    return [{"package": k, "version": v} for k, v in sorted(deps.items())
            if not k.startswith("com.unity.modules.") and CONTENT_UPM.search(k)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--own", default=",".join(DEFAULT_OWN), help="comma list of the game's own Assets folders")
    ap.add_argument("--store", default=None, help="Asset Store download folder")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    project = Path(a.project).resolve()
    assets = project / "Assets"
    if not assets.is_dir():
        sys.exit(f"no Assets folder in {project}")
    own = {s.strip() for s in a.own.split(",") if s.strip()}
    store = Path(a.store) if a.store else Path(os.environ.get("APPDATA", "")) / "Unity" / "Asset Store-5.x"

    packs = project_packs(assets, own)
    folders = {p["pack"] for p in packs} | {p["pack"].split("/")[0] for p in packs} | {p["pack"].split("/")[-1] for p in packs}
    cache = store_cache(store, sorted(folders))
    upm = upm_content(project)

    if a.json:
        print(json.dumps({"project": str(project), "in_project": packs, "asset_store_cache": cache, "upm": upm},
                         ensure_ascii=False, indent=1))
        return

    print(f"Project: {project}")
    print(f"\n1. Packs in Assets/ ({len(packs)}), usable now:")
    if not packs:
        print("   none — no third-party content installed")
    for p in packs:
        print(f"   {p['pack']:<44} models {p['models']:>4}  prefabs {p['prefabs']:>4}  textures {p['textures']:>4}"
              f"  materials {p['materials']:>4}  anims {p['anims']:>4}  audio {p['audio']:>4}  {p['mb']:>7} MB")
    not_imported = [c for c in cache if not c["imported"].startswith("looks imported")]
    print(f"\n2. Asset Store downloads not imported here ({len(not_imported)} of {len(cache)} in {store}):")
    if not cache:
        print("   none found" + ("" if store.is_dir() else " (folder missing; pass --store)"))
    for c in not_imported:
        note = f"  - {c['imported']}" if c["imported"] else ""
        print(f"   {c['publisher']} / {c['category']} / {c['package']}  ({c['mb']} MB){note}")
    seen = [c for c in cache if c["imported"].startswith("looks imported")]
    if seen:
        print("   already in the project: " + "; ".join(
            f"{c['package']} -> {c['imported'].replace('looks imported as ', '')}" for c in seen))
    print(f"\n3. Content-looking UPM packages ({len(upm)}):")
    for u in upm:
        print(f"   {u['package']} {u['version']}")
    if not packs and not not_imported and not upm:
        print("\nNo packs installed: make the asset yourself (Blender headless, image generation, procedural).")


if __name__ == "__main__":
    main()
