#!/usr/bin/env python
# Publishes the build to GitHub Releases: master and every branch have one permanent release build-<branch>.
#   publish-build.py publish <branch>   pack Builds/Windows of this checkout and upload it to the branch's release
#   publish-build.py built <branch>     print the commit of the published build (empty if none)
#   publish-build.py delete <branch>    delete the branch's release and its tag
#   publish-build.py pack [archive.zip] only pack Builds/Windows (default Builds/__GAME___Windows.zip;
#                                       Builds/publish/__GAME___Windows.zip stays the archive of the last publish)
# Env: MIN_BUILD_MB (default 100) — a smaller build is refused (LFS pointers instead of assets give a tiny build).
# Run with PYTHONIOENCODING=utf-8 and read the whole output.
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "Builds" / "Windows"
ZIP = ROOT / "Builds" / "publish" / "__GAME___Windows.zip"
SKIP = ("_DoNotShip", "_ButDontShipItWithYourGame")
MIN_BYTES = int(os.environ.get("MIN_BUILD_MB", "100")) * 1024 * 1024


def run(*args, check=True):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        sys.exit(f"{' '.join(args)}\n{r.stderr.strip()}")
    return r


def tag_of(branch):
    return "build-" + re.sub(r"[^A-Za-z0-9._-]+", "-", branch)


def built_sha(tag):
    r = run("gh", "api", f"repos/{{owner}}/{{repo}}/git/ref/tags/{tag}", "--jq", ".object.sha", check=False)
    return r.stdout.strip() if r.returncode == 0 else ""


def check_checkout(branch):
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    run("git", "fetch", "origin", branch)
    remote = run("git", "rev-parse", "FETCH_HEAD").stdout.strip()
    if head != remote:
        sys.exit(f"HEAD {head[:8]} differs from origin/{branch} {remote[:8]}: push or update this checkout first")
    # The exe's date is useless: Unity copies a prebuilt stub with an old date.
    data = BUILD / "__GAME___Data" / "globalgamemanagers"
    if not data.exists():
        sys.exit(f"no build: {data}")
    committed = int(run("git", "show", "-s", "--format=%ct", "HEAD").stdout.strip())
    if data.stat().st_mtime < committed:
        sys.exit("the build is older than the commit: rebuild first")
    return head


def pack(zip_path=ZIP):
    files = [p for p in BUILD.rglob("*") if p.is_file() and not any(s in part for part in p.parts for s in SKIP)]
    total = sum(p.stat().st_size for p in files)
    if total < MIN_BYTES:
        sys.exit(f"the build is suspiciously small: {total // 2**20} MB (forgot git lfs pull?)")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, Path("__GAME__") / p.relative_to(BUILD))
    with zipfile.ZipFile(zip_path) as z:
        infos = z.infolist()
        if z.testzip() is not None or len(infos) != len(files) or sum(i.file_size for i in infos) != total:
            sys.exit("the archive does not match the build")
    return len(files), total


def publish(branch):
    sha = check_checkout(branch)
    count, total = pack()
    tag = tag_of(branch)
    title = f"{branch} · {sha[:8]}"
    notes = f"Commit: {sha}\nBuilt: {datetime.now():%Y-%m-%d %H:%M}\nFiles: {count}, unpacked size: {total // 2**20} MB"
    channel = ["--latest"] if branch == "master" else ["--prerelease"]
    if run("gh", "release", "view", tag, check=False).returncode != 0:
        run("gh", "release", "create", tag, str(ZIP), "--target", sha, "--title", title, "--notes", notes, *channel)
    else:
        run("gh", "release", "upload", tag, str(ZIP), "--clobber")
        run("gh", "release", "edit", tag, "--title", title, "--notes", notes, *channel)
        # The tag moves last: `built` shows the new commit only after the archive is uploaded.
        run("gh", "api", "-X", "PATCH", f"repos/{{owner}}/{{repo}}/git/refs/tags/{tag}", "-f", f"sha={sha}", "-F", "force=true")
    print(run("gh", "release", "view", tag, "--json", "url", "--jq", ".url").stdout.strip())


def main():
    if len(sys.argv) in (2, 3) and sys.argv[1] == "pack":
        out = Path(sys.argv[2]) if len(sys.argv) == 3 else ROOT / "Builds" / "__GAME___Windows.zip"
        count, total = pack(out)
        print(f"{out} · files: {count}, unpacked: {total // 2**20} MB, archive: {out.stat().st_size // 2**20} MB")
        return
    if len(sys.argv) != 3:
        sys.exit("publish-build.py publish|built|delete <branch>  or  publish-build.py pack [archive.zip]")
    action, branch = sys.argv[1:]
    tag = tag_of(branch)
    if action == "publish":
        publish(branch)
    elif action == "built":
        print(built_sha(tag))
    elif action == "delete":
        if branch == "master":
            sys.exit("the master release is not deleted")
        if run("gh", "release", "view", tag, check=False).returncode == 0:
            run("gh", "release", "delete", tag, "--cleanup-tag", "--yes")
        # --cleanup-tag did not always delete the tag; `built` decides by the tag, so delete it separately.
        if built_sha(tag):
            run("gh", "api", "-X", "DELETE", f"repos/{{owner}}/{{repo}}/git/refs/tags/{tag}")
    else:
        sys.exit(f"unknown action: {action}")


if __name__ == "__main__":
    main()
