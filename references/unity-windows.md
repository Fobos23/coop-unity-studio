# Driving Unity on Windows without a screen

## The editor through the CLI

- `unity command eval --code '<C#>; return "ok";' --result-only --no-banner --timeout N` runs C# in the open editor
  (needs the Pipeline package). No `--file` option: pass `--code "$(cat file.cs)"`. Write C# or Python helper
  files with the Write tool: bash heredocs mangle apostrophes and `\n`.
- **Which editor**: `export UNITY_PROJECT_PATH=<checkout as D:/…>` and check
  `return UnityEngine.Application.dataPath;` first. With several editors open, plain eval attaches to another one.
- **Recompile**: `bash Tools/dev/recompile.sh` (refresh, wait for `recompile_status`, print console errors, exit 1
  on errors). `unity recompile` also exists in newer CLIs.
- **Output to a file, then read it whole.** `eval … | grep` hid a failed rebuild once and the player was built from
  a stale scene; all tests passed on it. Require the expected line (`scene saved`, `Succeeded errors=0`).
- **Long work**: an eval that hits its timeout only stops the client; the editor keeps running the code and answers
  nothing until it ends. Split long work into evals of a few minutes, driven by a background script that writes each
  answer to a file.
- **Modal dialogs block eval** (it times out while `recompile_status` still answers): "Packages with Errors"
  (Dismiss), "Enter Safe Mode?" (Ignore — closing it means Quit and the editor exits), "modified externally"
  (Reload — closing means Ignore and a later save writes stale data). `Tools/dev/unity-dialogs.ps1 -Project <path>
  -Press` finds the editor of that project by pid and presses only these buttons. Run PowerShell scripts with
  `-NoProfile -ExecutionPolicy Bypass`, or the policy refuses them and a grep hides the error. Never press
  "Dismiss Forever" (it writes ProjectSettings).
- **Editor "Not Responding" at idle CPU** for a minute or two under load: retry with a longer timeout before
  thinking of killing it.
- **No usable editor**: batchmode with the project closed:
  `"<Editor>/Unity.exe" -batchmode -projectPath <proj> -executeMethod <Game>.EditorTools.Batch.Run -zstep <Step>
  [-zstep …] -quit -logFile <log>`; each step is a parameterless public static method returning a string, logged as
  `[ZBATCH] <step>: …`. Or `unity run <proj> --no-tail -l <log> -- -executeMethod …` (don't add `-quit` after `--`:
  `unity run` adds it and exits 6 on a duplicate). Unity wipes `Temp/` on exit: write dumps elsewhere.
- **The director may be in the same editor.** Before an eval that opens a window, switches the open scene or resets
  editor state, note what was open and restore it in `finally`. Tell the director at once if something of theirs may
  be lost. Never `git checkout` or overwrite a scene file that is open: open another scene first.
- Edit-mode registries filled in `OnEnable`/`OnNetworkSpawn` are empty in eval: use `FindObjectsByType` there
  (editor code only).
- `EditorApplication.hierarchyChanged` does not fire for eval-made changes in a background editor;
  `ObjectChangeEvents.changesPublished` and `EditorApplication.update` do, on the next tick.
- Editor previews: a `HideAndDontSave` camera rendering into a `RenderTexture`, one frame per eval, saved as PNG.
  `ShaderUtil.allowAsyncCompilation = false` first or the frame is cyan; post-processing off. Final look only from
  the build's `-shots`.

## Editor steps build the game

Generated content comes from editor code (`<Game>.EditorTools`, a partial builder class): prefabs, materials, sound
bank, maps' `[Generated]` roots, build settings. Steps are idempotent (rerun = same output; compare report counts
after a refactor) and have menu wrappers (`[MenuItem("<Game>/Steps/N …")]`, parameterless). Balance values living in
an asset do not change when only C# defaults change: update the asset too.

## Worktrees for parallel work

- The main checkout has the director's editor and other sessions: never switch its branch. A branch gets its own
  worktree: `git worktree add -b <branch> ../<Game>_<name> origin/master`.
- Copy `Library` from a checkout whose editor is closed (an open editor writes into it):
  `robocopy <from>\Library <to>\Library /E /MT:16` (exit code < 8 = success), delete `Library/EditorInstance.json`,
  then `unity open <path>`. The first import from an empty Library takes ~15 min.
- `git lfs pull` in a fresh worktree: bare LFS pointers build an empty player (133 MB instead of 640) and break
  avatars ("Avatar is not of type humanoid").
- A light worktree for tools or docs only: `git worktree add --no-checkout --no-track -b <br> ../<x> origin/master`,
  `MSYS_NO_PATHCONV=1 git sparse-checkout set --no-cone /CLAUDE.md /Tools/...`, `git read-tree -mu HEAD`.

## Git and LFS traps

- `core.autocrlf=true`: an extensionless bash script is checked out with CRLF and dies. Name scripts `*.sh` and
  keep `*.sh text eol=lf` in `.gitattributes`.
- A rule like `*.asset … eol=lf` without `text` (common Unity templates) converts line endings without looking at
  the content: every CR LF pair inside a baked binary NavMesh loses its CR and the build log says "Unknown error
  occurred while loading". Keep `*NavMesh.asset binary`, `NavMesh-*.asset binary`, `LightingData.asset binary`
  (init.sh adds them; the hook's `bin` check blocks a binary `.asset` committed as text). A damaged file: a binary
  SerializedFile declares its size at offset 24 (8 bytes big-endian, format ≥ 22) — compare it with the blob
  size, and take an intact copy from the checkout that baked it or re-bake.
- Git Bash rewrites `/path` arguments into `C:/Program Files/Git/path`: prefix with `MSYS_NO_PATHCONV=1`.
- A VPN's DNS may not resolve `github-cloud.s3.amazonaws.com`: pushes with new LFS objects fail ("LFS: Put … no
  such host") and the ref is not pushed (`gh pr create` then says "Head sha can't be blank"). Check
  `git lfs push --dry-run origin <branch> | wc -l` and `nslookup github-cloud.s3.amazonaws.com`; ask the director to
  switch the VPN off for the push. Never `--no-verify`.
- After a build in an open editor some generated files re-save themselves (TMP fallback font asset, generated
  materials, performance test info): restore them unless the change is wanted; the hook blocks known junk.

## Builds

`<Game>.EditorTools.Builder.BuildPlayer()` builds every scene of the build settings into `Builds/Windows`, returns
`Succeeded errors=0 size=… ` or the error. 5–15 min: run in the background, wait for the result file. "Build was
canceled" with no visible dialog: delete `Assets/Resources/PerformanceTestRunInfo.json(.meta)` and retry once.
Details: `ship.md`.

## Other tools on this kind of machine

- Blender headless: `"<Blender>/blender.exe" -b --factory-startup --python <script> -- <args>`.
- Codex CLI for images and batches of models: use the desktop app's binary
  (`%LOCALAPPDATA%/OpenAI/Codex/bin/<hash>/codex.exe`; pick the folder that contains `codex.exe`):
  `codex.exe exec --skip-git-repo-check -s workspace-write -C <dir> --json -o <last.txt> - < prompt.txt`;
  `exec resume` is read-only unless `-c sandbox_mode='"workspace-write"'`. Its own review misses things: always
  import into Unity and look.
- C# language server for Claude Code: `csharp-ls` (pin a version that matches the installed .NET SDK).
