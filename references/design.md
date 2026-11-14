# Design: GDD, cards, playtests

## The GDD format

- One file per design wave (`docs/GDD_<version>_<topic>.md`), sections numbered (`§3.2`) so cards and commits can
  cite them.
- Every section carries its status in the heading: `[approved]`, `[proposal]`, `[approved direction]`,
  `[rejected]`, `[later]`. Rejected sections stay, one line on why, so nobody proposes them again.
- Start of a wave: §0 task and promise — the input conditions, what an analysis of the current build showed, the
  one-sentence promise, three pillars.
- Mechanics get a "Technique" subsection only after approval: classes, network messages, the scenario that will
  prove it.
- Last sections: "How to check" (log metrics and numeric playtest goals) and "Open questions".

## Co-op design checks (ask in phase 1, recheck per wave)

- **Co-op verbs**: what needs two or more players (carry heavy cargo together, pass and catch, revive, hold a door,
  one lures while another loots)? A co-op game where every verb works alone is a single-player game with company.
- **Scale with squad size**: waves, loot and costs scaled by the number of players; check that deaths per player for
  1, 2 and 4 players stay within ±30 %.
- **The dead player**: downed → revive window → dead → spectate with something to do (marks, radio). Average time
  spent dead ≤ 2 min. All downed → the session ends quickly (≈ 2 s), not a frozen screen.
- **Join, leave, rejoin**: host leaves (session ends with a message), client leaves (its cargo drops), rejoin keeps
  state (a downed player stays downed).
- **Host advantage**: anything decided on live host positions favours the host; client actions are judged by what
  the client saw (`net.md`).
- **Greed vs safety**: a reason to stay longer (multiplier, cache) against a reason to leave (rising threat).
- **Readability at 150 ms**: enemy wind-ups longer than the delay; hits confirmed by sound and effect on the
  shooter's side at once.

## A card spec (5–10 lines in the GDD section)

```
### §3.4 Heavy crate [approved]
- hypothesis: two players carrying one crate talk and cover each other — seen in the playtest as calls and stops
- rule: one player tilts and drags (speed 1.2 m/s), two carry (3.0 m/s); dropping it makes noise radius 10 m
- numbers in data: crate mass, speeds, noise radius (BalanceConfig)
- network: carriers in a NetworkList on the crate; the claim pattern for "caught/hit by crate"
- feel: pick-up response ≤ 100 ms on the client's screen; reaching full carry speed 0.6 s; drop: thud + camera
  dip 120 ms with decay; anti-reference: "floating box"
- acceptance (scenario `heavycrate`): one drags at ≤ 1.3 m/s; two carry ≥ 2.8 m/s; drop wakes AI within 10 m;
  a client with -netsim joins the carry; disconnect of a carrier drops it
```
Words without numbers are not specs: "smooth", "heavy", "responsive", "fast" become ms, m/s, frames, percent. A felt
mechanic gets a gym (`gyms.md`) where these numbers are tuned by playing.

## Feel in numbers

Translate every feel word into a number before the gym. Starting points, then check against a reference game's
frames (count frames from input to the first reaction) and tune in the gym. One frame at 60 fps is 16.7 ms.

| Feel word | Measure | Starting point |
|---|---|---|
| responsive | input → first visible reaction on the actor's own screen | ≤ 100 ms, better 2–4 frames |
| snappy / heavy attack | startup / active / recovery frames | light 4–7 / 2–4 / 8–14; heavy 12–20 / 3–6 / 18–30 |
| impactful hit | hit-stop | 30–100 ms (2–6 frames); stronger hit = longer |
| punchy camera | shake duration, amplitude, decay; follow lag | 80–200 ms, always decaying, never constant; lag 0.1–0.2 s |
| weighty movement | time to full speed and to a stop | 0.1–0.3 s for an agile character; 3–6 s for an arcade vehicle |
| floaty / tight jump | time to apex, coyote time, input buffer | 0.3–0.45 s to apex; coyote and buffer ~0.1 s |
| air control | share of ground control in the air | 50–100 % |
| readable threat | enemy wind-up before damage | longer than the client's view delay: ≥ 0.3–0.45 s at ~150 ms ping |
| fair hit (co-op) | client hits on a moving target at real ping | ≥ 90 % with rewind at ~150 ms (`lagaim`) |
| instant feedback (co-op) | own muzzle flash, hit marker, sound on the client | same frame, predicted locally; the host's verdict follows |
| juice chord | motion + flash + particles + sound of one action | all within the same 2–3 frames |

Parameters come in three kinds: **feel** (on the gym panel, the director turns them), **curves** (damage, prices,
scaling with squad size — in data, checked by logic tests), **gates** (session length, event frequency — in the GDD's
"How to check"). The general rows follow studioigor-skill's mechanics guide; the co-op rows are measured in Zombolic.

## Gates with numbers

A wave or a playtest has gates the director approves before work starts, each a number read from the host log or
the playtest:
```
| What | Goal |
| first contact with the threat | ≤ 90 s, even playing quietly |
| sessions where the squad stayed after the goal for the bonus | 30–50 % |
| average time dead | ≤ 2 min |
| groups that start a third session unasked | 3 of 4 |
```
Write the metric lines into the host log in the same card that adds the mechanic.

## Playtests

- Before: the validation question and the three questions for after, written down (e.g. "When was it scary?",
  "Did you want to stay longer?", "Were you bored when you died?").
- During: screen and voice recording, at least one group that has never seen the game.
- After: answers verbatim in `docs/PLAYTESTS.md`, metric numbers against the gates, a verdict: continue / rework
  (what exactly) / pivot.
- Stop signals: two playtest rounds without "one more session" → rebuild the core before spending on store page or
  trailer.

## Proposals

You are also a designer: at the start of a wave, after a slice, after a "boring" playtest, propose 3–4 ideas as
short cards (hook, what it changes for the squad, cost S/M/L, how a scenario would prove it). Nothing goes into the
build without the director's yes. A scope list "what not to do before release" protects the release date.
