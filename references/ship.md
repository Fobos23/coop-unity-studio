# Build, test, hand over

Modes from the director's words: `zip` ("rebuild, zip and send" — default: build → tests → archive, no commit or
push), `publish` ("publish the branch build": commit → build → tests → push → release → link and archive), `test`
(build → tests). Commit and push only in `publish` or on request.

## 0. Where to build
- `W` = the checkout of this branch (`git -C W branch --show-current`, `git -C W status --short`).
- Never switch the main checkout to another branch: another branch gets its own worktree (`unity-windows.md`).
- The editor of exactly this checkout: `UNITY_PROJECT_PATH=W`, check `Application.dataPath`.
- eval silent or "Invalid response" → a modal: `unity-dialogs.ps1 -Project W -Press`.
- The build is free: `Get-Process <Game>` with a path in `W/Builds/Windows` = someone's run. Wait, don't kill.

## 1. Compile and logic tests
`bash Tools/dev/recompile.sh` must print `no errors`; logic tests by eval with a long timeout (right after the editor
opens, a 120 s timeout is too short), output to a file, require `fail=0`.

## 2. Commit (publish: before the build)
- `publish-build.py` requires the build newer than the commit and HEAD = origin/<branch>: commit → build → tests →
  push → publish.
- Commit only your own changes; other uncommitted edits in the checkout → ask the director.
- The pre-commit hook checks network version, transport limits, junk, binary assets: fix the cause.
- A map with baked occlusion changed: check/bake before the commit so the baked data goes into the same commit.

## 3. Build
```bash
unity command eval --code 'return <Game>.EditorTools.Builder.BuildPlayer();' --result-only --no-banner --timeout 1500 > "$S/build.txt"
```
- Background; read the whole file; require `Succeeded errors=0`, a plausible `size=` (LFS pointers give a tiny
  build), no stale occlusion.
- Editor closed or stuck: batchmode with the project closed (`unity-windows.md`).
- After the build: `git status --short`; restore self-resaved junk.
- The game hangs at start (log ends at `GfxDevice`): the GPU driver. Don't reset it — tell the director; tests with
  `NOGFX=1` (light and shots then are not checked).

## 4. Tests
Through the agent `autotest-runner`, one scenario at a time: the card's own scenarios, then
`bash Tools/dev/run-suite.sh smoke`. `full` only at a stage gate, for an external build, after an engine/netcode
upgrade, or when the director asks (`testing.md`). A real failure → fix and repeat steps 1–4.

## 5. Push (publish)
New LFS objects + VPN DNS trap (`unity-windows.md`). `git push -u origin <branch>`.

## 6. Publish (publish)
```bash
PYTHONIOENCODING=utf-8 python Tools/dev/publish-build.py publish <branch>   # background, 10–40 min
PYTHONIOENCODING=utf-8 python Tools/dev/publish-build.py built <branch>     # must equal HEAD
```
One permanent GitHub release per branch (`build-<branch>`; master is "latest", others pre-release); the tag moves
last, so `built` shows the new commit only after the archive is uploaded. Read the whole output (cp1251 without
`PYTHONIOENCODING`). One publish per checkout at a time.

## 7. Hand over
- `zip`: `python Tools/dev/publish-build.py pack` → `Builds/<Game>_Windows.zip` (top folder `<Game>/`, without
  `*_DoNotShip`), verified by `testzip`, file count and byte total.
- Send with `SendUserFile`. Over Remote Control (phone/web) files over 30 MiB do not arrive: split into equal
  27 MiB parts (`split -b 27m --numeric-suffixes=1 -a 3 x.zip x.zip.`), check the rejoin hash; the director
  opens `.001` in 7-Zip or runs `copy /b x.zip.0* x.zip`.
- Report: commit, build size, the agent's lines per scenario, numbers vs budgets, what was not checked and why.
