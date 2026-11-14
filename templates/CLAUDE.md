# __GAME__ — rules for Claude sessions

Co-op for up to __PLAYERS__ players. The host is a listen server (NGO 2.x, Unity Transport): all AI, hit physics
and damage run on it. Online play goes through Unity Relay (DTLS, packet at most 1200 bytes); Steam later.
The studio process (phases, card cycle, testing policy): skill `coop-unity-studio`. Current phase and gates:
`docs/ROADMAP.md`. Design: `docs/GDD_*.md`.

## Network and performance — mandatory

1. **A client's action is checked by what the client saw** (it sees the world 150–400 ms late).
   - Against AI: rewind. The client sends its view time in the RPC; the host checks inside
     `LagComp.Begin(at, center, radius)` … `LagComp.End()` with `LagComp.Mask(...)`.
   - Against other players and the client's own body: the client's claim, checked by the host for plausibility.
   Checking a client's action against live AI colliders or the host's view of players is forbidden.
2. **Mass moving objects** (AI, any crowd): no `NetworkTransform` and no RPC per object; one snapshot stream,
   unreliable, in chunks ≤ the stream's `MaxChunk`, with the host's timestamp, rate by distance to clients.
3. **Delivery.** Look and sound — `RpcDelivery.Unreliable`. State and one-off game events — reliable RPC or
   `NetworkVariable`. A reliable RPC every frame is forbidden.
4. **NetworkVariable** is written only on change and not more often than needed (continuous values every 0.1–0.3 s,
   with a threshold). Owner-writable only for what the owner inputs.
5. **Message size** ≤ ~1000 bytes, except one-off sync on join. Transport limits (`TransportLimits.MaxMessage` 1200,
   `TransportLimits.NgoMtu`) are never raised.
6. **NetworkObject** only for what changes game state and is seen by all. Decor, furniture, static props — never.
7. **Network format changed** (RPC, message, `NetworkVariable`, prefab with `NetworkObject`) — bump `NetVersion.Version`.
8. **The host holds the frame.** No `FindObjectsByType`, `GetComponent`, LINQ or allocations in `Update` and in loops
   over AI; physics `NonAlloc`; heavy work (hundreds of spawns, setup) spread over frames: a hitch over 100 ms drops
   the connection through Relay.
9. **AI hitboxes on the root** (capsule + head sphere), not on bones.

## Render — mandatory

10. **Small props cast no shadows** (the render budget removes them below 1 m; don't add them back).
11. **Shadowed lamps are counted**: a new lamp is a downward spot with `LightShadows.Hard`, never a point light with a
    shadow. Code that switches lamps respects the budget (`RenderBudget.Culled(light)`).
12. **Occlusion only where a measurement showed a gain** (list of maps in the builder).
13. **Content added — measure it**: `renderprobe<N>` of the map against the table before the PR.
14. **Windows: Graphics Jobs off, D3D11 first** (D3D12 hangs on heavy maps with jobs in Unity 6000.3).

## Assets

15. **Installed packs first**: `python <studio skill>/scripts/find-packs.py .` before making a model, texture, sound
    or animation; offer what fits. None installed or none fits → make it. Surface is a texture, wear is a decal,
    geometry is form only. Every third-party asset → `docs/LICENSES.md`.
16. **The director's sketch is the plan**: rebuild it exactly; ideas go as proposals.

## Checking after changes

- After every card: its own scenarios + `bash Tools/dev/run-suite.sh smoke`. A smoke failing in an untouched suite →
  `run-suite.sh suite <name>`.
- Full regression `run-suite.sh full`: a phase gate, an external build, a Unity/Netcode/Transport upgrade, or on request.
- Network, hits, weapons: `lagaim` and `lanlag` in the card's own set. AI, crowds, maps: the crowd scenario
  (max players, max AI; host ≥ 60 fps). Render: `renderprobe<N>`.
- Builds and hand-over: skill `coop-unity-studio`, `references/ship.md`.
