# Gyms — one mechanic, one scene, tuned by playing

A gym is a separate scene for one mechanic the player FEELS (shooting, melee, carrying, a vehicle, a revive, a crowd
rush). The director plays it, says what is wrong, you turn the numbers, and the slice is later assembled from
mechanics already proven in gyms. Cards that change data, UI, maps or flow do not need a gym; their own autotest
scenario is enough.

## Where the gym sits in the card cycle

For a card that adds or changes a felt mechanic: spec with feel numbers (`design.md`, "Feel in numbers") → gym →
self-check (shots, numbers) → the director plays → tuning rounds → "lock it" → values into the data asset → the
card's own autotest scenario turns the acceptance numbers into `CHECK` lines → smoke set → PR.

## What a gym contains

- **A scene built by an editor step** (`Assets/<Game>/Scenes/Gyms/<Mechanic>Gym.unity`), in the build settings of
  dev builds, loaded directly with `-gym <Name>`: the host starts its session straight in the gym, clients join it.
- **The mechanic in production code** with parameters in a data asset; only the gym's scaffolding may be rough, and
  game code never references gym code.
- **Markers**: distances, lane speeds, heights and angles labelled in the scene, so both the director and your shots
  read numbers without guessing.
- **The harness** `templates/unity/Dev/Gym.cs`: `[Tune(min, max, hostOnly)]` fields get sliders; the same keys in
  every gym — R restart, Tab panel, O overlay, P save, 1/2 load preset A/B, Shift+1/2 save preset A/B, T slow motion
  ×0.25 (host only). Keys are physical positions (Input System), so a Russian layout works.
- **An overlay** with the numbers that matter for feel: ping, rewind ms, hits/shots, speed, time to target.
- **Minimal juice from day one**: a sound on the main action (a placeholder is fine), a flash or particles on
  contact, one camera reaction (shake with decay, FOV kick), a scale punch on the acting object. A silent mechanic is
  called boring even when its rule is good.
- **Fixed seed and timestep** so shots repeat.

## Co-op: feel is judged as a client

The host feels everything at zero latency; three of four players are clients. Every gym of a networked mechanic is
played at least once as a client with a realistic delay:
```bash
bash Tools/dev/gym.sh ShootingRange --coop              # host + client window on this PC, client -netsim 60,10,2
bash Tools/dev/gym.sh ShootingRange --coop --netsim 100,20,3
```
- Host-authoritative parameters (`hostOnly`, the default) are turned on the host; the client panel shows them
  read-only. Client-side feel (camera, recoil visuals, local effects) is turned on the client (`hostOnly: false`).
- What the client must see at once (its own muzzle flash, its own hit marker from its local trace) is predicted
  locally; the host's verdict follows by rewind (`net.md`). If a mechanic feels late only on the client, look at what
  waits for the host before blaming the numbers.
- AI wind-ups longer than the client's delay (≥ 0.3–0.45 s at 150 ms ping), or hits come "from nowhere".

## Gym catalog for co-op action games

| Mechanic | Gym |
|---|---|
| shooting | range with lanes at 5/10/20/40 m, dummies crossing at 2/4/6 m/s, armour plates, a headshot sphere marker |
| melee | pit with standing, walking (1.9 m/s) and running (4.6 m/s) dummies, a wall to pin against |
| crowd pressure | pen with a spawn slider (10–300 AI), a choke door, a fps and stream-bytes overlay |
| carrying cargo | track with slopes, stairs, a door, a gap to throw over, a second carrier spot |
| vehicle or cart | loop with a ramp, a wall to ram, a crowd strip to plough |
| revive and downed | arena with a timer, AI pressure on/off, a spectator camera check |
| stealth / noise | yard with sleeping AI, noise sources with radius rings drawn on the ground |

## Feedback and tuning

- After the director plays: one `AskUserQuestion` — "Is it fun?" first, then the specific axis (pace, weight,
  response, readability). Record the answer verbatim in `docs/PLAYTESTS.md` as `PT-<n> gym <Name>`.
- One tuning round = change 1–3 numbers that the feedback names, rebuild, play again. The saved values come from the
  log (`[GYM] saved <gym> group.field=value …`) or `%USERPROFILE%/AppData/LocalLow/<Company>/<Game>/gyms/*.tune`.
- "Lock it": values into the data asset by an editor step, the GDD section marked `[approved]` with the final
  numbers, commit. The gym stays as a regression scene.

## Self-check before showing

Shots from the build of the gym's fixed views; numbers from the overlay logged by a gym scenario (`-scenario
gym_<name>` can drive the dummies and print `CHECK` lines for the spec's numbers). Never show a gym you have not
played through in a scenario yourself.
