# Playtest and release

## Before the first external playtest (phase 7)

- **Freeze new systems.** Only fixes, settings and measurement.
- **Settings minimum**: mouse sensitivity, field of view, graphics quality, window mode, frame cap (default 60).
- **Metrics in the host log**: the lines the playtest gates need (`design.md`), one line per event, parseable.
- **Report button** in the menu: an archive with logs and crash data on the desktop; the tester sends the file
  (network upload needs a server and a key in the build).
- **Showcase map**: the map a newcomer sees first is the best one.
- **Install test**: a person who never saw the game installs and starts the build without help.
- **Full regression** green on the exact playtest build.
- Remove test-only missions and debug menus from what players see.

## Playtest program

3–4 groups of 3–4 players, at least one group new to the game, screen and voice recorded, a dev build with join
codes. After: the three questions, metrics vs gates, 5 moments for a trailer from an hour of recording. Two rounds
without "one more session" → rework the core before money goes into the store page.

## Store and release (phase 8)

- **Steamworks** early: the fee and the tax/payout forms take weeks.
- **Network**: Steam transport, lobby, invites, join from the friends list, Steam relays; Relay + join codes stay in
  dev builds (`online.md`).
- **One promise and three verbs** for the trailer and the capsule.
- **Store art from real build captures** (`-shots` from scripted views), plus generated key art if available; all
  sizes produced by a script. Trailer 45–60 s from playtest recordings, 5 screenshots, short GIFs.
- **Licences**: every pack, sound and music track checked for commercial use from `docs/LICENSES.md`; credits built
  from it; AI-generated content (art, music, text) declared in the store form.
- **Ship gates**: no debug keys, cheats, test missions or placeholder text; a soak session without leaks; save
  compatibility across the last versions; builds per platform; the final report starts with what was skipped.
- **Publishing and uploading only on the director's explicit decision.**

## Stop signals (write the project's own into its roadmap)

| Signal | Action |
|---|---|
| two playtest rounds without "one more" | rebuild the core, no spending on page and trailer |
| wishlist goal missed by the festival date | redo trailer and page, move the festival |
| a system not ready by its gate | ship without it, don't move the date |
| < 70 % positive reviews in week one | stop content, fix the top complaints |
