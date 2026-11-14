# The studio learns — with the director's yes

The studio is the director's own repository, so it can grow: better techniques, traps of Unity, NGO, Relay or
Windows, script fixes, process changes. It grows only through the director's approval, and a game's own taste never
leaks into it. Tool: `python <skill>/scripts/learn.py` (data in `<skill>/learned/`).

## Read at session start

`learn.py status`: accepted lessons that are not yet written into the skill (they override the general text until
they are), pending proposals, and the director's global preferences (`learned/preferences.md`).

## What is a lesson

A lesson works in any co-op Unity game on Windows: a trap that cost time, a technique that worked at the first
playtest, a failure that repeated, a better tool or a newer version, a fix to a studio script or template.
Not a lesson: this game's look, sound, feel, content, numbers or layout — those stay in the game's GDD, art bible,
CLAUDE.md and memory.

Record it the moment you notice it, one line of substance:
```bash
python $SK/learn.py propose --title "…" --kind technique|tool|process|fix --phase N \
  --what "the rule or change" --when "the situation it applies to" --why "what happened" --source "<game, commit, link>"
```
Similar lessons (pending, applied or rejected) are refused, so a rejected idea is not raised again.

## Ask at the right moment

At the end of a phase or a session (never mid-work, never in an autonomous run), if proposals are pending: one
`AskUserQuestion`, multiSelect, "What should the studio keep?", one option per lesson, at most 4 per call.
- chosen → `learn.py accept <ID>`, then write it into the studio: the smallest edit in the right file (a reference,
  a script, a template, a common-mistakes row), check it (run the script's test, compile the C#), commit in the studio
  repository `learn <ID>: <title>`, and `learn.py applied <ID> --where <file> --commit <sha>`. The director's yes
  covers that commit. If the studio repository holds someone else's uncommitted changes, ask first.
- not chosen → `learn.py reject <ID> --why "<the director's reason or 'not chosen'>"`.

## The director's preferences

When the director says "always do it this way" or "I don't like X", save it at once, without asking:
- **for this game** (the default; taste, content, delivery of this game's builds) —
  `learn.py prefer "<rule>" --project <game folder>`: a line in the game's `CLAUDE.md`, section "Director's
  preferences";
- **for every game** (how to work with the director: how to ask, when to show, how much to decide alone, language,
  delivery habits) — `learn.py prefer "<rule>" --global`: a line in `learned/preferences.md`.
- In doubt — this game. A game's preference beats a global one. Taken back → `learn.py unprefer "<part>" …`.

## Not to do

- Never edit the studio silently: every change of the skill goes through a lesson the director accepted.
- Never store a game's taste as a global preference.
- Never copy project facts into the studio "just in case": Claude's project memory keeps those.
