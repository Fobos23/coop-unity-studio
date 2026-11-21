# Maps

What to build — size, sightlines, relief, routes, respite, places with a story, the scheme and the passports —
is in `level-design.md`. This file is how to assemble it.

## The model: a hand-placed scene + an idempotent step

The director lays out buildings and props by hand (or gives a sketch scene, a drawing, a template of loose props).
An editor step regenerates everything gameplay needs under a `[Generated]` root: streets, cordon, doors, interiors,
loot containers, lighting, the map info component, managers, NavMesh. Never hand-edit what the step owns; never let
the step touch hand-placed roots except by explicit, reported moves. One shared pipeline (`SetupMapScene(MapPlan)`)
serves every map; a map is a `MapPlan` (scene and NavMesh paths, seed, rects, building names per kind, hooks) plus an
optional draft step. Never put one map's coordinates into the shared pipeline.

## A map from the director's sketch

The sketch is the plan: same wall lines, rooms, doors, windows, stairs, roof features; only the material changes.
1. Dump the sketch from git (a scene copy), find openings by per-piece raycasts, render a plan PNG per floor.
2. Transcribe walls as data (a plan table in code), lay kit modules on those lines with scaled fillers.
3. Compare plan PNGs of the result with the sketch before building the player. Deviate only where the kit physically
   cannot fit, and say so in the report.
4. Adopt the sketch once: move its objects (keeping x/z) into hand-editable roots (`Shell`, `Fixtures`, `Ground`,
   `Zones`); everything else goes under child roots the step deletes and rebuilds.

## Scene conventions (pattern)

| Root | Meaning |
|---|---|
| `Ground` | playable area: renderer bounds = map bounds, NavMesh volume, cordon line (one mesh over the whole map) |
| `Interactive<Kind>…` | gameplay buildings → building component, doors, furniture, containers |
| `Props` | background and outside props |
| `Zones/<Start|Exit|Spawn_*>/Area` | start, exit and spawn rects |

## New-map checklist

0. A scheme the director approved and a passport per place (`level-design.md`); the map's check step also runs the
   level-design rules on the scene.
1. Scene, map file with its `MapPlan` and menu wrappers; prefix every helper with the map name (a partial builder
   class already has generic names).
2. Plan geometry derived from the map's own layout, not constants of another map.
3. The step deletes `[Generated]`, seeds `Random`, rebuilds — rerunnable with identical report counts.
4. Buildings: component at the bounds centre, AI counts, `NavMeshModifierVolume` for the indoor area, roofs not
   walkable. Doorless buildings marked open, or their AI sleep forever.
5. Doors, interiors, containers on NavMesh within 2 m of their own floor; 1 m clear in front of doors (agent radius).
6. Bounds: invisible walls on their own layer that bullets ignore; a visible fence with gaps where the design wants
   them; the NavMesh volume not larger than `Ground`.
7. Lighting setup, map info (start, 4–8 player spawns, AI spawns, exit), managers with `NetworkObject`.
8. NavMesh on `[Generated]`, volume = `Ground` bounds, physics colliders; save `<Scene>_NavMesh.asset`. Stairs from
   some packs need `voxelSize 0.05`.
9. Save → build settings → refresh in-scene network ids → save again.
10. Mission entry; new objectives wired into the session manager and HUD.
11. A scenario for the map (its own suite in `autotests.txt`): scene and objective, doors (locked ones open with the
    tool), containers in every building, loot stays on the floor and spread, bounds hold, every building reachable,
    no attacks through floors, objective → exit → back to the lobby. A render probe of the map against the table.

## Common traps

| Symptom | Fix |
|---|---|
| reachability test fails at doors | closed doors carve the NavMesh, also in edit mode and only on the next editor tick: open doors in one eval, query in the next, or build a temporary surface with obstacles off |
| upper floor unreachable | furniture on a stair landing: bake a pre-furniture NavMesh, mark stair routes, keep them clear |
| AI hit or see players through floors | reach = flat range + vertical limit + chest-to-chest linecast; sight blocked across floors indoors |
| loot under the floor, behind a wall, in one pile | never derive drop height; sample NavMesh on the container's floor, keep paths inside the same building, space items ≥ 0.65 m |
| AI spawn inside a bed | pick spots before furnishing, re-pick blocked ones after |
| players leave the map | NavMesh volume larger than `Ground`, or a gap in the bounds walls: the scenario samples NavMesh outside each edge |
| a wall piece with "Door" in its name becomes a swinging door | rename on adoption (`Wall_Frame`, `Cabinet_Leaf`) |
| footprint 3–4 m too large | 45° wall pieces inflate renderer bounds: bake the mesh straight and rotate the object; move canopies and signs out of the building root |
| table tops scan as a second floor | give items on tables colliders, or put the roof slab collider below the visible ceiling |
| old tests break on a new layout | tests use helpers that find spots, not coordinates or building names |
| editor freezes during map work | a modal dialog; never overwrite an open scene file |

## Building scale

Pack buildings often feel cramped at scale 1 in first person. If the project scales gameplay buildings (Zombolic:
×1.2), walls, floors, doors and stairs grow; furniture, containers, loot, cars and characters keep their size; lamps
raise range by the scale and intensity by its square. Decide this in phase 4, before many maps exist.

## Below ground level

A pit or basement needs a hole in `Ground` (one mesh of boxes plus colliders, still one renderer for the bounds),
1.8 m headroom for players and agents, its own indoor volume and room box, and tests that sample NavMesh instead of
raycasting down from above.
