# Testing the built game

## Layers

| Layer | What | How fast | Runs |
|---|---|---|---|
| logic tests | pure C# rules: formulas, economy, saves, limits invariants | seconds, in the editor by eval | after every compile |
| autotest scenarios | the built player plays itself: host + clients, `CHECK` lines | 1–10 min each | per card: own + smoke |
| render probe | frame cost of a map by modes | ~1 min | per map change |
| director's playtest | is it fun, does it read | — | per slice, batch, playtest |

Edit-mode/play-mode tests in the editor are not evidence for networked behaviour: the editor in the background does
not tick play mode, animators report T-poses, NavMesh carving does not refresh. Test the build.

## The harness contract

In-game side (`templates/unity/Dev/Autotest.cs`), turned on only by command-line arguments:

| Argument | Meaning |
|---|---|
| `-autohost -autoplayers N` | host its own session, start when N players are in |
| `-autojoin <ip> -joinport <port>` | join that host (the port comes from the host's log: a busy 7777 moves it) |
| `-scenario <name>` | run that scenario (host drives it; clients may run their own half) |
| `-profile <name>` | separate save profile per copy (`t_host`, `t_c1`…) |
| `-netsim <delayMs>,<jitterMs>,<loss%>` | bad network on this copy (transport simulator stage) |
| `-shots <dir>` | screenshots for visual checks |
| `-logFile <file>` | own log per copy (two copies sharing `Player.log` overwrite each other) |
| `-batchmode -nographics` | headless client (perf scenarios, or every copy when the GPU is hung) |

Log lines (the runner and the agent parse them):
```
[AUTOTEST] CHECK PASS <check_name>: <detail>
[AUTOTEST] CHECK FAIL <check_name>: <detail>
[AUTOTEST] SUMMARY <scenario> pass=N fail=M failed=[a, b]
[AUTOTEST] PERF <scenario> fps=… min=… ai=… syncBytes=… aiMs=…
```
A client writes its own `CHECK` lines in `c1.log`; a client with no `CHECK` line never got into the session.

Runner side (`templates/Tools/dev/autotest.sh`): one `case` per scenario, a comment above each line saying what it
proves; logs in `Builds/autotest/<scenario>/`; it stops only the game copies of its own build folder (other
sessions run theirs); it waits for `SUMMARY` (or `Exception`) up to a timeout, then prints the checks, client
results and exceptions, and the line `=== <scenario> after <s>s`.

## Writing a scenario

- One scenario proves one area. Its checks are the card's acceptance criteria, named `area_what_expected`
  (`door_locked_opens_with_pick`).
- Wait with timeouts, never fixed sleeps for game state: `yield return Until(() => cond, 10f, "check_name")`.
- Don't use fixed coordinates or object names of one map for generic checks: helpers find a street spot, a blind
  wall, a door building (`StreetSpot()`, `BlindWall()`, `DoorBuilding()` patterns).
- Projectiles take flight time: wait for the host's impact time, not the frame after `Fire`.
- A screenshot of state that changes right after an action needs one `yield return null` first (capture happens at
  end of frame).
- Closed doors carve the NavMesh: path checks open doors first, wait 1 s, then restore.
- Profiles survive runs: reset what the scenario depends on at its start.

## The registry: suites and smoke

`Tools/dev/autotests.txt`, one scenario per line:
```
# suite      scenario      tags          note
core         solo          smoke         single player: start, session, result, back to lobby
core         hostleave     -             host quits mid-session, client gets the message
net          coop          smoke         host + client, full flow
net          lanlag        -             same with client -netsim 60,15,2
net          lagaim        smoke         client hits by rewind at ~150 ms
crowd        squadh        smoke,slow    4 players, max AI, host >= 60 fps
render       renderprobe   smoke         reference map, frame by modes
map-hospital hospital      smoke         map 9: reachability, objective, evac
ui           uishots       smoke         every window in 1920x1080
```
Rules:
- every scenario is in exactly one suite; every suite has one or two `smoke` scenarios;
- a smoke scenario: ≤ 5 min, the suite's main path, no known flakes; the whole smoke set ≲ 30 min;
- `flaky:<check>@<date>` in tags records a check that failed once and passed on rerun;
- `manual` in tags: needs a human or the internet (Relay, voice) — `full` lists it but does not run it unless
  `RUN_MANUAL=1`;
- a new map or big system gets its own suite.

`bash Tools/dev/run-suite.sh list | smoke | full | suite <name> | dry <mode>` runs them one by one through
`autotest.sh` and prints one line per scenario plus a total; `dry` prints what would run.

## When to run what

| When | Run |
|---|---|
| after every compile | logic tests |
| after every card, before its PR | the card's own scenarios + `run-suite.sh smoke` |
| smoke fails in a suite the card did not touch | that suite: `run-suite.sh suite <name>` |
| closing a phase gate, an external build (playtest, release candidate), a Unity/Netcode/Transport upgrade, or the director asks | `run-suite.sh full` |

The full set is not run per card: it costs hours and blocks the machine, and the card's own scenario plus one smoke
per suite catch what a card breaks.

## Reading results

- The build must be newer than the code: build time = `Builds/Windows/<Game>_Data/globalgamemanagers` (the exe's
  date is old by design), compared with the last commit and with modified files in `Assets/`, `ProjectSettings/`.
- Machine free: another copy of THIS build running = someone's run, wait. Copies of other builds: allowed, but fps
  and probe numbers become unreliable — say so.
- Fewer checks than last time = the scenario died early: a failure even with `fail=0`.
- No `SUMMARY`: the log ends at `GfxDevice` → GPU hung, rerun with `NOGFX=1`; `participants=1`, "incompatible
  version" → a busy port sent the client to a foreign host, rerun once.
- Flaky: rerun the scenario once. Passed → report "flaky", record it in the registry; failed again → a failure.
- Known noise to ignore: NGO "NetworkVariable is written to, but doesn't know its NetworkBehaviour yet", a client's
  "Failed to bind UDP socket … 7777".
- Compare numbers with the budgets in the project's references (`net.md`, `host-perf.md`, render table).

The agent `autotest-runner` (template in `templates/agents/`) does all of this and returns one line per scenario.

## Report form

```
Build: <time>, commit <sha>, newer than edits: yes|no; machine: free|other copies (<n>)
<scenario>: PASS 44/44 (was 44/44) · 4 min
<scenario>: FAIL 2/40 (was 40/40): <check> — <detail>
<scenario>: FLAKY 41/41 after rerun (<check> failed first)
<scenario>: DID NOT RUN — <GPU / port / exception "<first line>">
Numbers: <PERF / RPROBE / lagaim vs budget>
Total: green | failures: <list> | run unreliable: <why>
```
