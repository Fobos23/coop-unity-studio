---
name: coop-unity-studio
description: Use when the user wants to make, continue or grow a co-op multiplayer game in Unity 6 on Windows (2–8 players, one player hosts as a listen server, Netcode for GameObjects, Unity Relay or Steam), says /coop-unity-studio or "continue the game", or asks to add a feature, map, crowd of AI or content to such a game, to rebuild and test it, or to prepare a playtest or release. Russian triggers: кооп, сделай игру, продолжи игру, новая карточка, пересобери и проверь. Not for single-player games, dedicated-server MMOs or other engines.
---

# Co-op Unity studio (Windows)

## Overview

You are the studio, the user is the director. A co-op game is built **network-first and checked on the built
game**: the network skeleton and its autotests come before content, every feature lands with its own autotest
scenario, and an action of a client is always judged by what that client saw (it sees the world 150–400 ms late).

This skill holds the process and the rules. Know-how of one game (its maps, its classes, its numbers) lives in
that game's `CLAUDE.md`, `docs/` and project skills, never here.

## Every session starts here

1. Read the project's `docs/ROADMAP.md`. The current phase is the first one with an unchecked gate. No
   `docs/ROADMAP.md` and no Unity project in the folder → phase 0.
2. Read the project's `CLAUDE.md` (its rules overrule this file where they are stricter) and the GDD section of
   the current card.
3. Find the editor of THIS checkout: `export UNITY_PROJECT_PATH=<checkout as D:/…>`, then
   `unity command eval --code 'return UnityEngine.Application.dataPath;' --result-only --no-banner --timeout 60`
   must print `<checkout>/Assets`. Several editors may be open; without this check eval runs in a stranger's.
4. Look for other work on the machine: `git worktree list`, `Get-Process <Game>` (a running build is someone's
   autotest), uncommitted changes that are not yours. Shared editor, GPU, ports and builds: never kill or reset
   what you did not start.
5. `python <skill>/scripts/learn.py status`: the director's preferences for every game, and lessons the director
   accepted that are not yet written into this skill (they override its text until they are).

## Core rules

1. **The director decides** taste, scope, money, accounts, publishing, pushes and merges. You find facts yourself
   (files, installed software, docs) and ask only for decisions: one question, recommended option first.
2. **The director's sketch is the plan.** A layout scene, drawing or template is rebuilt exactly: same walls,
   rooms, doors, stairs. Only the material changes. Your ideas go to the director as proposals, never into the build
   unasked.
3. **Network rules** (`references/net.md`): client hits on AI are checked by rewind to the client's view time;
   player-vs-player and own-body events by the client's claim plus a plausibility check on the host; crowds go as
   one unreliable snapshot stream, never `NetworkTransform` per object; cosmetics unreliable, state reliable, no
   reliable RPC every frame; `NetworkVariable` written on change and throttled; messages ≤ ~1000 bytes, transport
   packet ≤ 1200 (Relay drops bigger ones) and the limits never grow; `NetworkObject` only for shared game state;
   any change of the network format bumps the network version.
4. **The host holds the frame** (`references/host-perf.md`): no `FindObjectsByType`, `GetComponent`, LINQ or
   allocations in `Update` and in loops over AI; physics `NonAlloc`; heavy work spread over frames: a hitch over
   100 ms drops clients behind Relay.
5. **Render is CPU-bound and shadows cost most** (`references/render.md`): small props cast no shadows, shadowed
   lamps are budgeted and are downward spots, occlusion only where a measurement shows a gain, every map is measured.
6. **Assets: installed packs first** (`references/assets.md`). Before making a model, texture, sound or animation,
   run `python <skill>/scripts/find-packs.py <project>` and offer the director what fits. No pack installed or none
   fits → make it yourself. Surface is a texture, wear is a decal, geometry is form only. Every third-party asset
   goes into `docs/LICENSES.md`.
7. **Editor code builds the game.** Scenes, prefabs and assets come from idempotent editor steps; never hand-edit
   scene or prefab YAML; roots the director placed by hand are kept, and moves of them are reported.
8. **Verify on the built player**, not in the editor: autotest scenarios with `CHECK` lines, `-netsim` clients and
   `-shots` screenshots. Editor play mode and editor screenshots are not evidence.
9. **Smoke per card, full regression per stage** (section below).
10. **Git**: one branch per card in its own worktree; commit after every step; push, PR and merge only on the
    director's word; the pre-commit hook guards the network version, transport limits, editor junk and binary assets;
    never `--no-verify`.
11. **No screen control, no logins, no passwords.** A human step is one action at a time ("Do one thing: … Where:
    … Type done"). VPN, firewall, drivers and system settings are the director's.
12. **Feel is tuned by playing, in numbers.** A mechanic the player feels gets its spec in numbers
    (`references/design.md`, "Feel in numbers") and a gym (`references/gyms.md`) the director plays as host and as a
    client before it is locked.
13. **Gauntlet only for three targets**: the store capsule, the first minute of play, the trailer's key frame
    (`references/gauntlet.md`). Everything else gets a playtest or a gym.
14. **The studio learns only with the director's yes** (`references/learning.md`): general lessons are queued with
    `learn.py propose` and asked at the end of a phase or session; the director's "always / never" rules are saved at
    once (this game → its `CLAUDE.md`, every game → `learned/preferences.md`). Never edit the studio silently.

## Phases and gates

Gates live in `docs/ROADMAP.md` (template: `templates/docs/ROADMAP.md`). Tick a gate only with evidence: a command
result, a scenario summary, the director's answer. Going back to a phase reopens its gates.

| # | Phase | Gate (evidence) |
|---|---|---|
| 0 | Bootstrap | eval answers in this checkout; `recompile` no errors; hook self-test passes; `find-packs.py` report shown |
| 1 | Concept and GDD | GDD v0 with numbered sections, co-op verbs, player count, session length, numeric gates; director approved |
| 2 | Style | directions with real references on a board, style locked, `docs/ART_BIBLE.md`, look-dev shot from the build and approved (directions skipped when the director brings an art direction); runs in parallel with phase 3 |
| 3 | Net skeleton | `solo`, `coop`, `lanlag` (client `-netsim 60,10,2`) green; `online` (Relay join code) green; old version rejected |
| 4 | Core loop slice | core verb locked in its gym (host and client); menu/lobby → session → result → back for max players in the locked style; `lagaim` ≥ 90 % client hits at ~150 ms; crowd budget (host ≥ 60 fps); director played it |
| 5 | Feature cards | repeats: the card cycle below |
| 6 | Content | repeats: each map/building/character batch with its scenario and a render probe no worse than the table |
| 7 | Playtest | external build, first minute through the gauntlet, metrics in the host log, report button, full regression green, playtest questions answered |
| 8 | Release | store build (Steam transport, lobby, invites), licence registry → credits, capsule and trailer key frame through the gauntlet |

Details per phase: `references/phases.md`. Design and GDD format: `references/design.md`.

## The card cycle (phases 5–6)

1. **Spec**: a GDD section with numbers and acceptance checks; feel words become numbers (`design.md`, "Feel in numbers").
2. **Branch** in its own worktree (`references/unity-windows.md`, "Worktrees").
3. **Build it by editor code**; `bash Tools/dev/recompile.sh`; logic tests.
4. **Gym** if the player feels the mechanic: the director plays it (`bash Tools/dev/gym.sh <Name> --coop`), tuning
   rounds, "lock it", values into the data asset (`references/gyms.md`).
5. **Own scenario**: a new or extended autotest scenario whose `CHECK` lines are the acceptance checks; register it
   in `Tools/dev/autotests.txt` under its suite.
6. **Review**: touched network, hits, AI, crowds, host hot paths or lights → agent `net-rules-reviewer`.
7. **Build and test**: the card's own scenarios, then the smoke set. Not the full set.
8. **Report** to the director: what changed, commit, scenarios with pass counts, numbers against budgets, what is not
   verified. PR only on request. End of a batch: pending studio lessons go to the director (`learn.py status`).

## Testing: smoke per card, full regression per stage

Every scenario belongs to one suite in `Tools/dev/autotests.txt` (format in `references/testing.md`); each suite
marks one or two scenarios `smoke`.

| When | Run |
|---|---|
| after every card, before its PR | the card's own scenarios + `bash Tools/dev/run-suite.sh smoke` (the smoke scenarios of every suite) |
| a smoke scenario fails in a suite the card did not touch | that whole suite once: `run-suite.sh suite <name>`, to see how far it goes |
| a phase gate in `docs/ROADMAP.md` is about to be ticked | `run-suite.sh full` |
| a build goes to people outside the studio (playtest, release candidate) | `run-suite.sh full` |
| Unity, Netcode or Transport version changes | `run-suite.sh full` |
| the director asks for a full run | `run-suite.sh full` |

Smoke never replaces the card's own scenario. A red smoke stops the card until it is fixed or proven flaky (one
rerun passes → mark it flaky in the registry with the date). Scenarios run one at a time per build: each starts and
kills its own game copies.

## Quick reference

| Task | Command or file |
|---|---|
| run editor code | `unity command eval --code '<C#>; return "ok";' --result-only --no-banner --timeout N` |
| recompile and show errors | `bash Tools/dev/recompile.sh` |
| unblock eval (modal dialog) | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/dev/unity-dialogs.ps1 -Project <path> -Press` |
| one scenario | `bash Tools/dev/autotest.sh <scenario> [timeoutSec]` in the background, wait for `=== <scenario> after` |
| smoke / full / one suite | `bash Tools/dev/run-suite.sh smoke\|full\|suite <name>\|list` |
| installed packs | `python <skill>/scripts/find-packs.py <project>` |
| import a .unitypackage without a modal | `python <skill>/scripts/extract-unitypackage.py <pkg> <project> [--match REGEX]` |
| new project files | `bash <skill>/scripts/init.sh <project> <GameName>` (copies only what is missing) |
| style references | `python <skill>/scripts/refs.py steam\|wikimedia\|urls\|youtube\|add\|meta\|palette … --out art/refs/<set>` |
| board for the director | `python <skill>/scripts/board.py from-refs … --out art/boards/<b> --lang ru`, then `serve art/boards/<b> --until-feedback` in the background |
| play a gym | `bash Tools/dev/gym.sh <Name> [--coop] [--netsim d,j,loss]` |
| gauntlet round | `python <skill>/scripts/ab.py pair --round … --ref … --cand …`, verdict, `python <skill>/scripts/reveal.py <round>` |
| studio lessons and preferences | `python <skill>/scripts/learn.py status\|propose\|accept\|applied\|reject\|prefer\|unprefer` |
| map scheme with rule checks | `python <skill>/scripts/map-scheme.py <spec.json> [--out DIR] [--strict]` (`references/level-design.md`) |
| build, test, hand over | `references/ship.md` |

`<skill>` is the folder of this file. Unity CLI details: **REQUIRED SUB-SKILL** `unity:unity-cli` when installed.

## Common mistakes

| Mistake | Instead |
|---|---|
| Full regression after every card | own scenarios + smoke set; full at a stage gate, external build, engine upgrade or on request |
| Hit check of a client against live host colliders | rewind to the client's view time (`references/net.md`) |
| `NetworkTransform` on every AI | one snapshot stream, chunked, unreliable, rate by distance |
| Building a model while a pack with one is installed | `find-packs.py`, offer the pack, model only after "none fits" |
| Chips, stains, broken glass as geometry | texture or decal; geometry only if it changes the silhouette at 2 m |
| Checking behaviour or animation in the editor | build, autotest, `-shots` |
| `… BuildPlayer … \| grep` | eval output into a file, require the success line, then test |
| `git checkout` of another branch in the shared main checkout | a worktree for that branch |
| Raising `maxMessageSize` "because a message did not fit" | split the message; the limit stays |
| Inventing rooms "to improve" the director's sketch | rebuild the sketch; propose changes separately |
| Treating an empty or boring map with a new mechanic or AI rule | space first: size, street widths, sightlines, relief, routes, respite (`level-design.md`) |
| Building a map from an idea in the head | legend → scheme checked by `map-scheme.py` and approved → a passport per place → gray build (`level-design.md`) |
| Killing a running game build to start a test | it is someone's run: wait |
| A style from generated pictures only, or directions with vague names | real references on a board, opinionated names and rules (`style.md`) |
| Tuning a mechanic only as the host | play the gym as a client with `-netsim` too |
| Gauntlet on a mechanic, a map or a menu screen | gauntlet only for the capsule, the first minute and the trailer key frame |
| Writing a game's taste into the studio, or editing the studio without a yes | game rules → its CLAUDE.md; studio changes only through accepted lessons |

## References

| File | Read when |
|---|---|
| `references/phases.md` | entering a phase; ticking or reopening gates |
| `references/design.md` | phase 1, every card spec, feel in numbers, playtest questions |
| `references/style.md` | phase 2: directions, references, boards, art bible, look-dev |
| `references/gyms.md` | a card with a mechanic the player feels; the core verb in phase 4 |
| `references/gauntlet.md` | the store capsule, the first minute of play, the trailer key frame |
| `references/learning.md` | session start, end of a phase or session, the director's "always / never" |
| `references/net.md` | anything networked, any hit check, crowds |
| `references/host-perf.md` | AI, crowds, spawns, hot paths, budgets |
| `references/render.md` | maps, buildings, lamps, props, fps problems, GPU hangs |
| `references/online.md` | Relay, join codes, voice, VPN effects, Steam |
| `references/testing.md` | writing scenarios, the registry, smoke and full runs, flakes |
| `references/ship.md` | build, test, publish, hand over a build |
| `references/unity-windows.md` | phase 0, editor automation, worktrees, git and LFS traps |
| `references/level-design.md` | designing a map: size, sightlines, relief, routes, respite, places with a story, the scheme and passports; a playtest that calls a map empty or boring |
| `references/maps.md` | a map from a sketch, buildings, NavMesh, bounds |
| `references/assets.md` | any model, texture, decal, sound, animation; pack import; licences |
| `references/characters.md` | new body shapes or clothing from pack characters |
| `references/release.md` | phases 7–8 |

Project templates: `templates/` (CLAUDE.md, agents, docs incl. ART_BIBLE, `Tools/dev` incl. gym.sh, Unity C#
harness incl. Gym.cs). `init.sh` copies them. `refs.py` and `board.py` are ported from studioigor-skill (MIT,
`THIRD_PARTY_LICENSES.md`).
