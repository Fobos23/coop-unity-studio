# Host frame

The host is a player's PC that also simulates everything. NGO reads incoming messages once per frame: a host at
30 fps adds up to 33 ms to every direction. A frame over 100 ms drops clients behind Relay.

## Rules

- In `Update`, `FixedUpdate`, frequent RPC handlers and loops over AI: no `FindObjectsByType`, no `GetComponent` in
  the loop, no LINQ, no `new List`/`new T[]`/closures per call, no string building except behind a log flag.
  Cache components; keep static registries filled in `OnEnable`/`OnNetworkSpawn`.
- Physics queries: `…NonAlloc` with a shared buffer, explicit layer masks, `QueryTriggerInteraction.Ignore`.
- `Physics.autoSyncTransforms` off: queries see colliders as of the last physics step. Call
  `Physics.SyncTransforms()` only where you move colliders and query at once (rewind does).
- Mass spawn, map setup, loading: spread over frames (a budget of N per frame or a time slice of a few ms).
- Do not write transforms of hundreds of objects that did not move.
- AI ticks staggered: not all AI think in the same frame; far AI think less often.
- Pool effects and projectiles (`UnityEngine.Pool.ObjectPool<T>`).
- The frame cap is a player setting (default 60). Autotests run uncapped (a dev override) so fps numbers show the
  headroom; game code never writes `Application.targetFrameRate` directly.

## Budgets to set in phase 4 and keep

| What | Budget | Scenario |
|---|---|---|
| host frame at max players and max AI | ≥ 60 fps | heavy crowd scenario (`squadh` pattern) |
| AI tick | ≲ 1 ms for the whole crowd | `PERF` line field `aiMs` |
| moving AI near players (≤ 20 m) at once | ≲ 150 | design of waves and spawns |
| frame hitch | < 100 ms | `hitch=` in the runner's monitor line |
| one-off spawn on session start | spread, no hitch over budget | session start scenario |

The heavy scenario pattern: host with graphics plus 3 clients `-batchmode -nographics -fps 30` (four graphical
windows on one PC measure the PC, not the game), max AI, 60–90 s, then a `PERF` line: fps avg/min, AI count,
stream bytes per tick, `aiMs`, and a `CHECK perf_60fps`.

## Measuring

- Host log lines (`PERF …`) written by the scenario: easier to compare than the profiler.
- `perf_60fps`-type checks fail when other sessions load the machine: judge them on a quiet machine, and say in the
  report when other game copies were running.
- Profile before optimizing: Unity Profiler on a development build attached to the host, or `ProfilerRecorder`
  counters logged by the scenario.
