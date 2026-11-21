# Level design: space first

A map is designed before it is built: a legend, a scheme with numbers, a passport for every place. The numbers come
from the game's own metrics, not from taste. How a map is assembled in Unity is in `maps.md`; this file is about what
to assemble.

## A boring map is a space problem first

When a playtest calls a map empty, easy or "did the task and left without meeting anyone", look at the space before
proposing a mechanic, an AI rule or a balance change:

| Look at | Sign of the problem |
|---|---|
| size | the same AI population on several times the area: density drops, pressure never arrives |
| street widths | one width everywhere; wide straight streets let the squad pass anything |
| sightlines | views longer than the AI's sight range: the squad sees and avoids, the AI is too far to engage |
| relief | everything on one level: no crest, no high ground, no one-way drop |
| routes | one straight way to the goal with an exact marker: nothing to decide |
| respite | no place to shut a door and talk, or such places only by accident |
| places | spots on the route with no role and no story |

Small dense maps that players praise usually do all of this by accident: the way to the goal runs through a populated
building, the cargo is slow and noisy, there is nowhere to step aside. Write down why they work and keep it as the
formula. A director rule on top of a flat, wide map treats the symptom.

## Rules in the game's own numbers

Take the numbers from the balance data and derive the limits; record both in the GDD.

| Metric of the game | Rule derived from it |
|---|---|
| AI sight range | no outdoor sightline longer than about 0.8 of it; one intended vista per map, from a high point |
| sprint speed | edge to edge in about 35 s; any goal within about 150 m of path; a larger map dilutes pressure |
| sprint speed against the fastest AI | a respite door within about 4 s of sprint from any point of a route |
| jump height | ledges up to it can be climbed; a window sill below it is an entrance |
| safe fall height | a drop up to it is a free one-way shortcut; a storey drop costs health; higher is a wound |
| storey height of the building kit | ground levels in steps of half a storey, so relief meets floors, porches and roofs |
| what a player cannot do with cargo (ladders, narrow gaps) | the way back with cargo differs from the way in |
| vehicle width and turning | the vehicle's street stays free of tall blockers and is broken only by bends |

**Size.** Small and thought through beats large. Two blocks of about 100 m is a ceiling for a squad on foot.

**Street widths.** Three of them, each with a role: one widest open place (fast, exposed), ordinary streets with
cover, and alleys, yards and passages 1.5–3 m wide (hidden, tight, no way back). No open ground wider than about
25 m without cover; cover every 8–10 m of a route.

**Relief.** Every level change has a job: a crest hides what is behind it; high ground sees and is seen; a half-storey
drop is a way down only; a bridge puts two routes in one place, over and under; a slope makes cargo roll. At least
three ground levels on a map. Buildings stand on flat terraces of their level; relief reaches them as terraces and
retaining walls. No hills for looks.

**Routes.** Three ways to the goal, each with its price: open (fast, any cargo, through a chokepoint), hidden (quiet,
slow, tight, needs a tool) and high or low (view or cover, jumps and ladders, no cargo). They split within 30 m of the
start and meet at the goal; any two overlap by no more than a third. A chokepoint and its bypass come as a pair.
One-way shortcuts reward the squad that got there. Map variants close one route and open another. The marker leads to
the building, not to the room.

**Respite.** A respite place is a building whose entrances all close from inside, with two exits that both lead
somewhere, a window to the outside and something worth entering for. Three types the player learns to tell apart: a
plain respite, a stronghold by the exit point, and a look-alike with sleeping AI inside. One stands before a
chokepoint and one after it. Check every second exit: a door into a fenced yard without a gate is a trap by mistake.

**Rhythm.** The map sets the same peaks and lulls as an AI director, by space: start with a view of the landmark and
of the fork → approach and first respite → chokepoint, first contact within 75–90 s → goal inside a populated building
→ return by another way under pressure → exit as a defended place with 2–3 approaches. AI spawn zones are part of the
layout: they open onto the way back, 40–70 m from where the squad usually is, never on the vehicle's path.

## What breaks a sightline

Found by running the sightline check on a real layout; the first version with straight streets gave 100 m.

- Cars do not block sight: the player's eye is above a car roof. A bus, a lorry, a tent, a blind fence or a house does.
- One blocker across a street is not enough: the view passes beside it. Two staggered blockers with gaps on opposite
  sides work.
- Shifting a street by its own width is not enough: a diagonal passes. It takes the street's width plus a building.
- Walls and fences stand right at the street. A lawn strip behind the sidewalk is a ready corridor for the eye.
- On the vehicle's street nothing tall may stand, so only a bend breaks it.
- A plateau or a yard is as long as its diagonal: put one tall thing in the middle.

## Places with a story

A place tells what happened there and how it ended. It is read in three layers, from three distances:

| Layer | Read from | Made of |
|---|---|---|
| silhouette | 40 m | large forms: a vehicle across the road, a tower, a row of blocks |
| evidence | 15 m | arrangement of props: what stands where, what is torn off, what was dropped |
| traces | 3 m | decals and small things: bullet holes, scorch, blood, chalk, a list on a table |

- If the answer to "what happened here" does not come within five seconds of looking, the place is not ready.
- The story gives play: every place has a line "what it gives the squad" — cover, a chokepoint, a bypass, a find, a
  danger. A find follows the story.
- One legend per map: 5–7 dated lines of what happened; the places are its frames, and a squad that walked the whole
  map can retell it. Link places: what was awaited in one is found stuck in another.
- Density per block: one landmark with the big story, 3–5 scenes, 10–15 small traces. No stretch of a route longer
  than about 30 m without a scene or a trace.
- Wear is decals and textures, never geometry. Models of loot and cargo are never decor.
- Before dressing, each place gets a passport (`templates/docs/MAP_PASSPORT.md`): what happened, silhouette, evidence,
  traces, what it gives the squad, who stands there, danger, bypass.

## The map cycle

1. **Legend**: 5–7 lines.
2. **Scheme**: ground levels, streets by width, landmark, routes, respite, chokepoints, exit. Drawn to scale from one
   coordinate table and checked by script (below). The director draws it or approves the studio's draft; an approved
   scheme is the plan and is rebuilt as it is.
3. **Passports** for every scene.
4. **Gray build** without detail → the director walks it, the rule check runs on the scene.
5. **Detail** by passport: silhouette, evidence, traces.
6. **Playtest** with a position journal: where squads walk, die, and sit behind a closed door.

A standard like this is proven on one pilot map and one playtest before other maps are converted to it.

## The scheme tool

`python <skill>/scripts/map-scheme.py <spec.json> [--out DIR] [--strict]` reads one JSON table and writes two sheets
(`<name>_plan.png`, `<name>_routes.png`) and `<name>_metrics.json`. Example with every field:
`templates/docs/map-scheme.example.json`.

- Buildings go in at their real footprints and doors: read them from the project's building data, never estimate.
- Blockers are listed with a kind; `tall` names the kinds that block sight. Low ones are cover only.
- Checks: ground levels, the goal by the shortest route, route overlap, the worst distance to a respite door (areas in
  `no_ai` are exempt), the longest sightline, spawn zones from the start. Limits are in `limits`; set them from the
  game's numbers above.
- Work in a loop: draw, run, read the top sightlines in the metrics, move things, run again.
- The sightline check is flat and rough: a ray stops at a building, a tall blocker, the background or a ground step of
  `level_step`; it knows nothing of windows or of looking down from a height, and on its 1 m grid a ray can slip past
  a thin fence that ends exactly at a corner. The check on the built scene (rays at eye height, paths on the NavMesh)
  is the evidence; the scheme check is for design.

## Checks on the built scene

Add to the map's own check step (`maps.md`, new-map checklist):

| Rule | How |
|---|---|
| sightlines | rays at eye height over a grid of outdoor points; list the worst |
| routes | NavMesh path lengths for each route, overlap, at least one passable with cargo |
| respite | closable entrances, two exits each reaching the routes, distance from route points |
| relief | at least three ground levels on the NavMesh |
| AI-free places | no NavMesh link onto ladders-only places |
| places | a marker with a passport per scene; no long stretch of a route without one |

## Playtest evidence

- The host log writes each player's position every 5 s: a heat map of where squads walk, die and stand.
- Time behind a closed door, the route taken there and back, AI within sight range every 30 s, the longest pause
  without AI near.
- Goals: no route below 15 % or above 60 % of raids; the way back differs in at least half of them; the squad shut
  itself in a building at least once in most raids; players can retell the map's story after three raids.
- Questions: "Was it scary? Where exactly?", "Which way did you go and why?", "What happened here, on this map?"
