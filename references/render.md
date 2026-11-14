# Render: what a frame costs and how to keep it

Measured on Zombolic (URP Forward+, RTX 2080 + i7-9700K, 1600×900): main thread 3–6 ms, GPU 2–3 ms. A stylized
co-op game with many buildings and AI is **CPU-bound**: cut passes and objects, not triangles.

## Shadows cost most

Every shadowed light is a separate pass over everything in its volume. A map with 58 hard-shadow lamps had ~25 of
them shadowing per frame and 4300 shadow casters; without shadows the frame was a third faster.

- **Small props cast no shadows.** A runtime budget component (`RenderBudget` pattern, added by the map's info
  component on every playable map) sets `ShadowCastingMode.Off` on renderers whose bounds diagonal < 1 m, except
  players, AI, the first-person view and anything moving (`NetworkObject`, `Rigidbody`). Do not put shadows back on
  small props in prefabs or scenes.
- **Shadowed lamps are counted.** A new lamp is a downward spot with `LightShadows.Hard`; never a point light with
  shadows (6 passes). Light created at runtime has no shadow unless it must.
- The budget keeps shadows on the 8 nearest visible lamps within 30 m (10 % hysteresis for lamps that already
  have one) and turns off lamps whose light sphere (`range + 1.5 m`) the camera cannot see (`CullingGroup`, frame +
  baked occlusion), after 0.3 s. Code that switches lamps must respect it: a lamp off by the budget is
  `RenderBudget.Culled(light)`; "is lit" = `light.enabled || RenderBudget.Culled(light)`. The budget restores only
  what it turned off itself.
- AI shadows only within 30 m (±1 m hysteresis), updated 128 per frame.
- One shadow cascade (several cascades at a low sun leak light through thin walls and roofs).

Results of the budget: the hospital 5.95 → 3.39 ms (−43 %), indoors −52 %; open districts −4…−9 %.

## Occlusion culling only where measured

Umbra helps only where walls hide a lot (multi-storey interiors): 4.2 → 3.2 ms from indoors. On small open maps it
only splits static batches. Rule: a map gets baked occlusion only if the render probe shows `base` clearly faster
than `occOff` on that map. Then:
- moving things (doors, carts, physics, networked) are not Occluder/Occludee Static;
- every door gets an `OcclusionPortal` that closes at the end of the door swing;
- the map step rebakes it; the build step checks a geometry fingerprint and rebakes stale data;
- changing such a map's geometry around the steps → run the bake step before building.

## Graphics API and Graphics Jobs on Windows (Unity 6000.3)

- Graphics Jobs **off** for Windows (`PlayerSettings.graphicsJobs = false` /
  `m_BuildTargetGraphicsJobs: WindowsStandaloneSupport: 0`). On D3D12 they free resources the GPU still uses (D3D12
  debug layer: errors 527 and 921 CORRUPTION) and hang the GPU on heavy maps: `DXGI_ERROR_DEVICE_HUNG`, then
  `nvlddmkm 153`. Both Split and Native modes hang. Cost of turning them off: ~0.1 ms, ~5 % host fps.
- API list `Direct3D11, Direct3D12` (D3D11 first; D3D12 by `-force-d3d12`). On the heavy district D3D11 was also
  faster (7.36 vs 7.90 ms). The log line `GfxDevice: creating device client; kGfxThreadingModeThreaded` proves jobs
  are off.
- Before turning jobs back on after a Unity upgrade: run the heaviest map with
  `-force-gfx-jobs split -force-d3d12-debug` (copy `d3d12SDKLayers.dll` of the same version as `D3D12Core.dll`
  from `<Editor>/Data/PlaybackEngines/windowsstandalonesupport/External/AgilitySDK/x64` into
  `Builds/Windows/D3D12`; the Windows optional feature "Graphics Tools" is needed too). No 527/921 errors allowed.
  Remove the debug DLL before packing a build.
- A GPU can also hang when thousands of renderers become visible in one frame (a probe re-enabling 2200 small
  renderers at once): show and hide in portions (≈150 per frame).

## The render probe scenario (pattern)

One player, fixed resolution (1600×900), its own camera copy. 10 NavMesh points inside buildings and 10 outside
(farthest-point sampling) × 4 directions. Per mode: 6 warm-up frames, 12 measured frames with `FrameTimingManager`
(`enableFrameTimingStats` on) and `ProfilerRecorder` counters (batches, SetPass, triangles, shadow casters, visible
skinned). GPU frames over 1000 ms are driver noise and dropped. AI stand still.

Modes: `base` (as in game), `legacy` (no budget), `occOff`, `far60` (camera far 60 m), `noShadow`, `noAI`,
`noSmall` (no renderers < 1.5 m), budget parts one by one, shadow caps 4/16.

Output: `RPROBE mode=<m> ALL|IN|OUT frame= main= render= gpu= | batches= … shadowLamps= lampsOn=`, the 6 worst
views, checks `renderprobe_done`, `renderprobe_occlusion_works`, `renderprobe_lamp_culling_works`,
`renderprobe_budget_not_slower`; screenshot pairs `*_legacy.png` / `*_budget.png` of the views where the budget
removed most shadows (they must look the same: < 0.05 % pixels differ, AI poses aside).

Noise between runs is ±0.1–0.2 ms (other game copies running): compare modes **within one run**. Keep a table per
map in the project's render reference: map, frame before/after, batches, triangles, shadow casters, shadowed lamps
in frame. A new map's `base ALL` is compared with that table; a row written from the same run is not a reference.

Finding the view that hangs the GPU: log `RPROBE view at= yaw= mode=` before the first frame of each view; the last
such line before `887a0006` is the culprit; repeat one view with `-probeat x,y,z -probeyaw N -proberepeat K`.

## New content checklist

- [ ] new lamps: downward spots, hard shadows, range like the neighbours
- [ ] large props (furniture, cars) keep shadows; small ones lose them by the budget, not by hand
- [ ] the map's probe: `base ALL` not worse than comparable maps; shadowed lamps in frame ≤ ~8
- [ ] a map with interiors: `base` vs `occOff` measured, occlusion kept only if it wins
