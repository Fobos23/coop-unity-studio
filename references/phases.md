# Phases in detail

The gate lists below are what `templates/docs/ROADMAP.md` starts with. A project may add gates; it never deletes
one silently (skip it with a reason written next to it).

## Phase 0 — Bootstrap

Goal: a Unity project this machine can drive without a screen.

1. **Facts first**: `unity editors --installed`, `unity status`, `dotnet --list-sdks`, Blender path
   (`D:/Blender Foundation/*/blender.exe` or `where blender`), `git lfs version`, `gh auth status`.
2. **Project**: `unity projects new <Name> --path <parent> --editor-version <installed 6000.x LTS> --template
   com.unity.template.universal` (URP). An existing project: work on a branch, fill CONCEPT/TECH from the code and
   show it to the director.
3. **Packages** (`Packages/manifest.json`): `com.unity.netcode.gameobjects` 2.x, `com.unity.transport` 2.x,
   `com.unity.services.multiplayer` (Relay, Sessions), `com.unity.inputsystem`, `com.unity.ai.navigation` if there is
   AI, `com.unity.test-framework`. Pick versions by a short research pass (release notes, known issues) and record
   them in `docs/ROADMAP.md` → "Stack".
4. **Editor automation**: the Unity Pipeline package (`unity pipeline install --project-path .`), then eval must
   answer (Overview, step 3 of the session start). Install the `unity:unity-cli` skill/plugin if missing.
5. **Project settings**: Force Text serialization, visible meta files, Linear colour space, Input System only,
   Windows graphics API list `Direct3D11, Direct3D12` (D3D11 first, see `render.md`), Graphics Jobs off.
6. **Git**: `git init`, LFS for binaries, `.gitattributes` with `*.sh text eol=lf` (with `core.autocrlf=true` a CRLF
   bash script dies on its first line), Unity YAML smart merge. `bash <skill>/scripts/init.sh <project> <Game>`
   copies `CLAUDE.md`, agents, `docs/`, `Tools/dev/` and the C# harness; then `bash Tools/dev/githooks/install.sh`.
7. **Packs**: `python <skill>/scripts/find-packs.py <project>`; show the director what is installed and what sits in
   the Asset Store cache, so asset decisions later start from facts.

Gates:
- [ ] eval in this checkout returns `<checkout>/Assets`
- [ ] `bash Tools/dev/recompile.sh` prints `no errors`
- [ ] `bash Tools/dev/githooks/pre-commit.test.sh` passes
- [ ] pack report shown to the director

## Phase 1 — Concept and GDD

Read `design.md`. Interview in 2–3 rounds, then a pitch the director approves. The GDD has numbered sections so
cards can cite them (`GDD §3.2`).

Gates:
- [ ] co-op verbs: what needs two or more players, what a lone player cannot do
- [ ] player count (min/max), session length, fail state, what the dead player does
- [ ] core loop at three scales (30 s, one session, a week of sessions)
- [ ] numeric gates for the first playtest (see `design.md`, "Gates with numbers")
- [ ] director approved the GDD v0

## Phase 2 — Style, art bible and look-dev

Read `style.md`. Directions with real references on a board (`refs.py`, `board.py`), 2–3 rounds of the director's
feedback, `docs/ART_BIBLE.md`, a look-dev scene shot from the build. Skipped in part when the director already brings
an art direction (write the bible from it anyway). Runs in parallel with phase 3: the look-dev scene needs only the
project from phase 0. Both phases close before the slice.

Gates:
- [ ] ≥ 3 directions with real references shown on a board (or skipped: the director gave an art direction)
- [ ] the director locked the style
- [ ] `docs/ART_BIBLE.md` complete (palette with roles, light, form, surface, ≥ 3 signature techniques, co-op readability, never-list)
- [ ] look-dev scene shot from the build and approved by the director

## Phase 3 — Net skeleton

Read `net.md`, `online.md`, `testing.md`. Before any content:
- host/client start, approval with a network version string (`GameNet.Version` pattern), player cap;
- transport driver with `maxMessageSize = 1200` and the `-netsim` simulator (`templates/unity/Net/TransportLimits.cs`);
- NGO batch under one packet: `NetworkManager.MaximumTransmissionUnitSize = 1088` (1200 minus Relay/DTLS headers),
  `UnityTransport.MaxPayloadSize` large (64000) only for one-off fragmented sends; a logic test pins
  `snapshot chunk + 64 ≤ NGO MTU` and `NGO MTU + 100 ≤ transport max message`;
- LAN join by address and port, Relay join by code (Sessions API, idempotent network handler);
- the autotest harness (`templates/unity/Dev/Autotest.cs`) and the runner (`Tools/dev/autotest.sh`) with scenarios
  `solo`, `coop`, `lanlag`, `online`, `hostleave`, plus `connect` for bad codes and dead hosts;
- logic tests (pure C# rules) run by eval.

Gates:
- [ ] `solo`, `coop`, `hostleave` green
- [ ] `lanlag` green with the client on `-netsim 60,10,2`
- [ ] `online` green through a real Relay join code
- [ ] a client with another network version is refused with a clear message
- [ ] registry `Tools/dev/autotests.txt` has suites `core` and `net` with smoke marked

## Phase 4 — Core loop slice

The 30-second verb in co-op, at real quality, wrapped in the whole flow: menu or lobby → session → result → back.
- The core verb first in its gym (`gyms.md`): spec with feel numbers (`design.md`), played by the director as host
  and as a client with `-netsim`, locked before the slice is assembled.
- Real quality = the art bible and the look-dev assets, not grey boxes.
- Player movement owner-driven; combat, AI and damage on the host; client hits by rewind (`net.md`).
- Crowds (if any) as a snapshot stream; set the crowd budget now (max AI, max players, host fps) and add a
  heavy scenario that holds it (`squadh` pattern: 4 players, max AI, headless clients).
- First map from the director's sketch (`maps.md`), render probe on it (`render.md`).

Gates:
- [ ] the core verb locked in its gym, played as host and as a client
- [ ] full flow for max players green in one scenario, in the locked style
- [ ] `lagaim` pattern: ≥ 90 % client hits on running targets at ~150 ms ping, with and without rewind compared
- [ ] crowd scenario: host ≥ 60 fps at max AI and max players
- [ ] render probe of the first map recorded as the reference row
- [ ] director played the slice: verdict continue / rework / pivot written in `docs/PLAYTESTS.md`
- [ ] full regression green

## Phase 5 — Feature cards

The card cycle in SKILL.md. Cards come from the director (a board, a list, a message). One card = one branch = one
PR. A batch of cards from one message may share a branch when the director says so. A card with a felt mechanic goes
through its gym before its PR. At the end of a batch: pending studio lessons go to the director (`learning.md`).

## Phase 6 — Content

Maps, buildings, characters, props, sounds, music. Each batch: packs first (`assets.md`), its own scenario (map
reachable, bounds hold, objective → exit → back), render probe against the table, smoke set.

## Phase 7 — Playtest

Read `release.md`. Settings menu minimum, crash/report button, metrics in the host log, a build installed and
started by a person without help.

Gates:
- [ ] a stranger installs and starts the build alone
- [ ] first minute of play through the gauntlet (`gauntlet.md`), the director accepted "before → after"
- [ ] metrics lines in the host log answer the playtest questions
- [ ] full regression green on the playtest build
- [ ] playtest held, answers in `docs/PLAYTESTS.md`, numbers vs gates written

## Phase 8 — Release

Read `release.md`. Store page, Steam transport and lobby, licences, credits, store art from build shots; the store
capsule and the trailer's key frame go through the gauntlet (`gauntlet.md`). Publishing and uploading only on the
director's explicit decision. At release: 1–3 main lessons of the project proposed to the studio (`learning.md`).
