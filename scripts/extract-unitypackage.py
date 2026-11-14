#!/usr/bin/env python
"""Import a .unitypackage into a Unity project without the editor's modal import dialog.

  python extract-unitypackage.py <package.unitypackage> <project> [--match REGEX] [--list] [--force]

A .unitypackage is a tar.gz of <guid>/asset, <guid>/asset.meta and <guid>/pathname. This writes the chosen assets
and their .meta files (GUIDs kept, so references between them survive) plus .meta files of parent folders that the
package carries. Existing files are skipped unless --force. Afterwards refresh the editor:
  unity command eval --code 'UnityEditor.AssetDatabase.Refresh(); return "ok";' --result-only --no-banner
--list prints the package's paths (filtered by --match) and writes nothing.
"""
import argparse
import re
import sys
import tarfile
from pathlib import Path, PurePosixPath


def read_entries(pkg):
    entries = {}
    with tarfile.open(pkg, "r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            parts = PurePosixPath(m.name.lstrip("./")).parts
            if len(parts) != 2:
                continue
            guid, kind = parts
            entries.setdefault(guid, {})[kind] = m
        names = {}
        for guid, e in entries.items():
            if "pathname" in e:
                raw = tar.extractfile(e["pathname"]).read().decode("utf-8", "replace")
                names[guid] = raw.splitlines()[0].strip()
    return entries, names


def safe_target(project, rel):
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] not in ("Assets", "Packages"):
        return None
    return project.joinpath(*p.parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("project")
    ap.add_argument("--match", default=None, help="regex on the asset path (Assets/...)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    a = ap.parse_args()

    project = Path(a.project).resolve()
    if not (project / "Assets").is_dir():
        sys.exit(f"no Assets folder in {project}")
    rx = re.compile(a.match) if a.match else None
    entries, names = read_entries(a.package)
    chosen = sorted((p, g) for g, p in names.items() if rx is None or rx.search(p))
    # Parent folders of chosen assets that the package also carries (folder entries have a .meta and no asset).
    folders = {str(PurePosixPath(p).parent) for p, _ in chosen}
    parents = set()
    for f in folders:
        q = PurePosixPath(f)
        while str(q) not in ("", ".", "Assets"):
            parents.add(str(q))
            q = q.parent
    folder_entries = [(p, g) for g, p in names.items() if p in parents and "asset" not in entries[g]]

    if a.list:
        for p, g in chosen:
            kind = "file" if "asset" in entries[g] else "folder"
            print(f"{kind:6} {p}")
        print(f"{len(chosen)} paths")
        return

    written = skipped = refused = 0
    with tarfile.open(a.package, "r:gz") as tar:
        for p, g in chosen + folder_entries:
            target = safe_target(project, p)
            if target is None:
                refused += 1
                print(f"refused path: {p}", file=sys.stderr)
                continue
            e = entries[g]
            if "asset" in e:
                if target.exists() and not a.force:
                    skipped += 1
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(e["asset"]).read())
                    written += 1
            else:
                target.mkdir(parents=True, exist_ok=True)
            if "asset.meta" in e:
                meta = target.with_name(target.name + ".meta")
                if not meta.exists() or a.force:
                    meta.write_bytes(tar.extractfile(e["asset.meta"]).read())
    print(f"written {written}, skipped existing {skipped}, refused {refused}; now refresh the editor (AssetDatabase.Refresh)")


if __name__ == "__main__":
    main()
