# Phase 2 — Style, art bible and look-dev

The director often has no finished art direction. This phase turns "something grim, like X" into a locked style:
real references on a board, rounds of feedback, an art bible and a look-dev scene in the build. It can run in
parallel with phase 3 (the net skeleton): both must close before the core slice.

**Skip condition:** the director already gives an art direction (a style guide, a mood board, finished concept art).
Then the gates "directions on a board" and "rounds" are skipped with that reason, and you still write
`docs/ART_BIBLE.md` from what they gave and build the look-dev scene.

Paths: references in `art/refs/<set>/`, boards in `art/boards/<board>/`, the bible in `docs/ART_BIBLE.md`, look-dev
shots in `Builds/autotest/lookdev/shots`. Reference images are a private moodboard: never in the build, never
published, ignored by git (`art/refs/**` except `sources.json`; `art/boards/**` except `board.json`).
`<skill>/scripts` = `$SK`. The scripts need Python 3.9+; Pillow (`python -m pip install pillow`, ask first) for
resizing and palettes; yt-dlp and ffmpeg only for video frames.

## Round 1 — directions

Make 3–4 directions from the GDD (genre, references, mood, camera). Mandatory:
- **close to the references** the director named, with a twist;
- **bold**: one axis pushed far (monochrome plus one colour, huge scale, grotesque silhouettes);
- **from another medium**: a film, poster school, album covers, architecture, engraving, animation school;
- **from the installed packs** when `find-packs.py` shows art packs: what the game looks like if we lean on them.
  Cheapest to produce; say so in its pros.

A direction card, one line per field, written into the set before the hunt (`refs.py meta`):
- **name with an opinion** an artist could paint from alone ("sodium-lit suburb after the evacuation", not
  "stylized and dark");
- **visual rule** that settles arguments ("danger is the only saturated colour");
- **mood and light**: the emotion, warm/cold, contrast, time of day;
- **shape**: what silhouettes are made of and what is absent;
- **colour**: palette direction and the one meaning of the accent;
- **can we make it**: players, AI and pickups read at 30 m in dusk; the render budget (`render.md`: CPU-bound,
  shadows cost most); which packs cover it; what we would have to model or texture ourselves.

Collect 6–10 real references per direction:
```bash
python $SK/refs.py meta art/refs/sodium --title "…" --text "Rule: … Mood: … Shape: … Colour: …" --tags "3D,dusk" --pros "…" --cons "…"
python $SK/refs.py steam "<reference game or appid>" --out art/refs/sodium --n 6
python $SK/refs.py wikimedia "<photo theme>" --out art/refs/sodium --n 4
python $SK/refs.py urls links.txt --out art/refs/sodium      # lines: URL | page | credit | licence | note
python $SK/refs.py youtube "<gameplay video url>" --out art/refs/sodium --frames 6   # needs yt-dlp + ffmpeg
python $SK/refs.py add art/refs/sodium shot.png --note "our pack lit this way"         # local files, pack renders
python $SK/refs.py note art/refs/sodium steam-ab12 "take: wet asphalt reflections"
python $SK/refs.py drop art/refs/sodium steam-cd34                                    # junk, never again
```
Sources: Steam screenshots (games), Wikimedia Commons (architecture, places, photos), pages found by web search
through `urls` (takes the page's og:image), Are.na mood boards, ArtStation covers, video frames. Openverse may sit
behind a bot check on some networks: do not try to pass it, use the other sources. Pack renders of our own assets
are references too (`add`). Generated concepts are additions, marked `--generated`, never the main material in
round 1.

Build and show the board:
```bash
python $SK/board.py from-refs art/refs/sodium art/refs/poster art/refs/packs --out art/boards/style-r1 \
  --title "Style, round 1" --question "Which direction is closer?" --lang ru
python $SK/board.py serve art/boards/style-r1 --until-feedback --timeout 3600    # in the background
```
In the Claude desktop app open the printed URL in the browser pane (`preview_start` with the url) so the director
sees it next to the chat; elsewhere add `--open`. Tell the director: look, mark "like" / "not it", comment, press
Send. The server prints the feedback and exits; the full record is `art/boards/<board>/feedback.json`.

## Round 2 — variations inside the chosen direction

Palette, light (time of day, interior darkness), camera height and FOV, density of detail. Same board flow. Palette
from what the director liked: `python $SK/refs.py palette art/refs/<set> --liked art/boards/style-r2/feedback.json`.

## Round 3 — game-screen frames

Frames of THIS game in the style: a greybox or pack scene in Unity lit by the bible, shot from the build
(`-shots`), plus generated paint-overs if an image tool exists (marked generated). The director picks
"lock it" or another round. 2–3 rounds are usually enough; record the decision in the GDD and the roadmap.

## The art bible — `docs/ART_BIBLE.md` (template in `templates/docs/ART_BIBLE.md`)

- **Palette** in hex with roles: dominant, secondary, supports, one accent with one meaning.
- **Light**: key and ambient per space (street, doorway, interior), time of day, fog; ambient values are set in
  gamma but the project is linear (`unity-windows.md`): check the real value in the build.
- **Form**: silhouettes, proportions, building scale vs characters, what is never round / never sharp.
- **Surface**: texture style (measured from the packs if we use them: outline, tones, noise), decals for wear.
- **At least 3 signature techniques** that must be on screen at full strength.
- **Readability for co-op**: teammates vs AI at 30 m in dusk, pickups and interactables, threat cues.
- **Never**: the list of what breaks the style.
- **How we make it**: which packs, what we model, texture or generate, what the render budget allows.

## Look-dev — "this is how the game will look"

A small scene in the build: light and post-processing per the bible, 2–3 hero assets, a player character, an AI
type, a HUD mock-up, one interior and one street view. Scenario `lookdev` shoots fixed views (same camera, time and
seed every run) into `shots`. The director approves it before mass content. If the director is not convinced after
a round of fixes, the key frame goes through the gauntlet (`gauntlet.md`).

## Gates (in `docs/ROADMAP.md`)
- [ ] ≥ 3 directions with real references shown on a board (or skipped: the director gave an art direction)
- [ ] the director locked the style
- [ ] `docs/ART_BIBLE.md`: palette with roles, light, form, surface, ≥ 3 signature techniques, co-op readability, never-list
- [ ] look-dev scene shot from the build and approved by the director

## Traps
| Symptom | Fix |
|---|---|
| every direction looks "like every AI game" | opinionated names and rules; a direction from another medium; real references, not generated ones |
| the style needs art nobody can make | "can we make it" line per card; a direction from the installed packs |
| the director cannot say what is wrong | variations in round 2 instead of a new set of directions; ask for one like and one "not it" per row |
| the bible drifts during production | change it only by the director's decision, with a line in the GDD changelog |
| reference images got committed | `art/refs/**` and `art/boards/**` images stay out of git; only `sources.json` and `board.json` |
