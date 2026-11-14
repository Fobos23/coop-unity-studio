# __GAME__ — roadmap

The current phase is the first one with an unchecked gate. Tick a gate only with evidence (a command result, a
scenario summary, the director's answer) and write it after the gate: `— 2026-11-20, coop 18/18 (a1b2c3d4)`.
A gate skipped on purpose: `[-]` and the reason. Going back to a phase reopens its gates.

## Stack
Unity: … · NGO: … · Transport: … · Multiplayer Services: … · URP: … · Input System: … (chosen on …, why)

## Phase 0 — Bootstrap
- [ ] eval in this checkout returns `<checkout>/Assets`
- [ ] `bash Tools/dev/recompile.sh` prints `no errors`
- [ ] `bash Tools/dev/githooks/pre-commit.test.sh` passes; hook installed
- [ ] pack report (`find-packs.py`) shown to the director

## Phase 1 — Concept and GDD
- [ ] co-op verbs: what needs two or more players
- [ ] players min/max, session length, fail state, what the dead player does
- [ ] core loop at 30 s / one session / a week of sessions
- [ ] numeric gates for the first playtest
- [ ] director approved GDD v0

## Phase 2 — Style (can run in parallel with phase 3)
- [ ] ≥ 3 directions with real references shown on a board (or `[-]` the director gave an art direction)
- [ ] the director locked the style
- [ ] `docs/ART_BIBLE.md`: palette with roles, light, form, surface, ≥ 3 signature techniques, co-op readability, never-list
- [ ] look-dev scene shot from the build and approved by the director

## Phase 3 — Net skeleton
- [ ] `solo`, `coop`, `hostleave` green
- [ ] `lanlag` green (client `-netsim 60,10,2`)
- [ ] `online` green through a real Relay join code
- [ ] another network version is refused with a clear message
- [ ] `Tools/dev/autotests.txt`: suites `core` and `net`, smoke marked

## Phase 4 — Core loop slice
- [ ] the core verb locked in its gym, played by the director as host and as a client (`-netsim`)
- [ ] full flow for max players green in one scenario, in the locked style
- [ ] client hits on running targets ≥ 90 % at ~150 ms (`lagaim`)
- [ ] crowd scenario: host ≥ 60 fps at max AI and max players
- [ ] render probe of the first map recorded as the reference row
- [ ] director played the slice; verdict in `docs/PLAYTESTS.md`
- [ ] full regression green

## Phase 5 — Feature cards
Repeats. Cards: <board or list>. Each card: own scenario + smoke set green before its PR; a felt mechanic is locked
in its gym first.

## Phase 6 — Content
Repeats. Each batch: packs checked first, own scenario, render probe, smoke set.

## Phase 7 — Playtest
- [ ] a stranger installs and starts the build alone
- [ ] first minute of play: gauntlet rounds done, the director accepted "before → after"
- [ ] metric lines in the host log answer the playtest gates
- [ ] full regression green on the playtest build
- [ ] playtest held; answers and numbers in `docs/PLAYTESTS.md`

## Phase 8 — Release
- [ ] store transport, lobby and invites (Steam) green in scenarios
- [ ] licences checked; credits from `docs/LICENSES.md`
- [ ] store art and trailer from build captures; capsule and trailer key frame through the gauntlet
- [ ] ship gates: no debug keys, test missions, placeholders; soak session; saves compatible
- [ ] the director decided to publish

## Not before release
- …

## Stop signals
| Signal | Action |
|---|---|
| two playtest rounds without "one more session" | rework the core before spending on the store page |
