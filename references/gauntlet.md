# Gauntlet — blind A/B against a bar, only for three targets

The usual "build → show → fix" loop stalls at "fine": you grade your own work softly, and the director cannot always
say what is wrong. The gauntlet breaks that with a bar you can open, a blind comparison where the verdict is written
before you know which side is ours, and one gap per round. It is expensive, so it is used **only** for:

| Target | When |
|---|---|
| **store capsule** (and the header/logo art of the store page) | before the store page opens, and when the director is unimpressed |
| **the first minute of play** (launch → menu → lobby or join → first verb) | before an external playtest and before release |
| **the trailer's key frame** (the frame the trailer and store screenshots rest on) | before cutting the trailer |

Mechanics, maps, ordinary content and utility screens get a playtest or a gym, never the gauntlet.

## Bars and lenses

| Target | Bar (what to open) | Lenses, one per round, in rotation |
|---|---|---|
| store capsule | capsules of 3–5 strong games of the genre on the store (`refs.py steam` gives their art pages; save the capsule images into `ref/`) | readable at the smallest store size (shrink both to ~120 px wide) · title legible at that size · what you DO in this game is visible · style matches the game's real frames |
| first minute | a contact sheet of a reference game's first minute (frames every 5 s from a recording: `refs.py youtube <url> --at 0:00,0:05,…` or the director's own recording) | the next action is always the most visible thing · steps from launch to the first verb (count them) · UI response (motion + sound on every press) · a friend can join in ≤ N steps · style |
| trailer key frame | 1–3 key frames of reference trailers or the style board, same framing | value structure (squint / greyscale: one focal shape) · the promise and its verbs read in one frame · light and material per the art bible · the bible's signature techniques at full strength · layer density (light, fog, particles, background) |

Never compare across classes: a stylized frame against a stylized bar, a capsule against capsules. Photoreal AAA
against our style always wins and teaches nothing.

## Setup, once per target

```
art/gauntlet/<target>/          capsule | firstminute | keyframe
  BAR.md        the bar, its source, the lenses, the frozen capture command
  ref/          bar images (or the bar's contact sheet)
  rounds/NN/    candidate.png, ab/ (A.png, B.png, pair.png, key.bin), verdict.md, outcome.json
  LEDGER.md     written by reveal.py
```
The capture command is frozen in `BAR.md`: same scenario, camera, time of day, seed and resolution every round
(`-scenario keyframe -shots …` or `-scenario firstminute -shots …` driving a newcomer's path with fixed inputs).
Otherwise an improvement cannot be told from a re-framing. For the first minute, make the candidate a sheet of the
same seconds as the bar: `python $SK/ab.py sheet rounds/NN/candidate.png <frames…> --labels 0s,5s,…`.

## A round

1. **Capture** with the frozen command → `rounds/NN/candidate.png`.
2. **Blind pair**: `python $SK/ab.py pair --round art/gauntlet/<target>/rounds/NN --ref art/gauntlet/<target>/ref/<file>
   --cand art/gauntlet/<target>/rounds/NN/candidate.png`. Do not decode `key.bin`, do not list file sizes.
3. **Judge through one lens.** Read only the lens, `docs/ART_BIBLE.md` and `pair.png`. Do not reread the code or your
   own plans: "that is what I intended" is exactly what an outside critic does not have. By default the bar wins; our
   side wins only if you can point to how it wins under this lens.
4. **Verdict** `rounds/NN/verdict.md`, up to 10 lines:
   ```
   LENS: <lens>
   WINNER: A|B
   GAP: <the single biggest gap as an observable difference: "the bar has X, we have Y">
   FIX: <the one change this round>
   ```
5. **Reveal**: `python $SK/reveal.py art/gauntlet/<target>/rounds/NN` (refuses without WINNER and GAP; reveals once;
   appends to `LEDGER.md`). If ours won, reread the lens; a reason that does not survive counts as a win for the bar.
6. **One change** per FIX. Everything else you noticed goes to the backlog.
7. Commit `gauntlet <target> NN: <gap>`.

## Stop and show

- After 3–6 rounds, or when ours has won under every lens at least once: show the director "before → after" on a
  board (`board.py`, round 00 and the latest) and let them decide.
- Two rounds without a visible difference: the gap was a feeling, not an observable difference. Rephrase it or switch
  the lens.
- The director is still not convinced: offer a longer refinement of that one target with the same frozen command,
  2–3 rounds per run, only with their consent.
