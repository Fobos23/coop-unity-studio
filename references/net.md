# Network: listen-server co-op on NGO 2.x

Names below (`LagComp`, `CrowdSync`, `SnapshotBuffer`, `GameNet.Version`) are the pattern. Until they ship as a
package, the working implementation to port from is Zombolic (`D:/Unity/FlatArtProjects/Zombolic`):
`Assets/Game/Scripts/Net/LagComp.cs`, `Net/SnapshotBuffer.cs`, `AI/ZombieSync.cs`, `Net/TransportDriver.cs`,
`Net/GameNet.cs` (approval and version). Read the real file before porting; do not port from this summary.

## The shape every game here has

- **Host = listen server.** AI, ballistics, melee, damage, pickups and the session state run only on the host.
  A client draws and sends input as RPCs.
- **The player's own character** is owner-driven: `NetworkTransform` with `UseUnreliableDeltas`, owner
  authority. Everything else that moves in numbers (AI, crowds, debris) has no `NetworkTransform`.
- **A client sees the world in the past**, by: ½ ping (snapshot to client) + 0–100 ms (waiting for the next send
  tick) + render delay (~130–200 ms) + ½ ping (the action back to the host) + up to one host frame. At 120 ms
  ping that is 0.25–0.45 s: a running enemy at 4.6 m/s moves 1–2 m, a capsule is 0.3 m wide. A host that checks
  a client's shot against live colliders makes the client miss what is in its crosshair while its local effect
  shows blood. This is the source of most "it should have hit" reports.

## Rule 1 — a client's action is judged by what the client saw

### Against AI: rewind
The client sends its view time with the action; the host places shadow hitboxes where the AI was at that moment
(from the same snapshot history it streams) and queries those.

```csharp
// client (owner): the time of the snapshot it was rendering
FireRpc(origin, dir, CrowdSync.ViewTime);

// host
[Rpc(SendTo.Server)]
void FireRpc(Vector3 origin, Vector3 dir, double viewTime)
{
    double at = LagComp.ShotTime(player, viewTime);          // 0 for the host player and in tests: no rewind
    bool rewound = LagComp.Begin(at, origin + dir * len * 0.5f, len * 0.5f + radius);
    bool any = Physics.SphereCast(origin, radius, dir, out var hit, len,
        LagComp.Mask(Layers.ShotMask), QueryTriggerInteraction.Ignore);
    if (rewound)
    {
        if (any) hit.point = LagComp.ToNow(hit.collider.GetComponent<AiHitbox>(), hit.point);
        LagComp.End();                                        // before damage: damage and effects hit the live AI
    }
    // damage on the live AI ...
}
```

- `LagComp.Begin(at, center, radius)` moves shadow hitboxes (their own layer, e.g. 20) of the AI near the query
  to their positions at `at`, calls `Physics.SyncTransforms()` once; `End()` parks them again.
- Overlaps: the same. Angles and distances to neighbours: `LagComp.PositionAt(ai, at)`.
- Continuous tools without an own time: `LagComp.EstimatedTime(player)` (half RTT + render delay).
- Body contact or a pushed cart: `LagComp.ActorTime(player)` (the host sees the client's body ½ ping late; the AI
  is rewound by that plus the client's render delay).
- Clamp: rewind at most ~1 s (`MaxRewind`); the shot origin is accepted within a tolerance (≈ 4 m) because the
  host sees a running client late.
- Explosions and area effects are not rewound (radius > displacement).
- AI attacks on players use live host positions. Rewinding that way makes hits come "from nowhere". Make the AI's
  visible wind-up longer than the delay instead.
- **Hitboxes on the AI root** (capsule + head sphere), not on animated bones: the host does not depend on animation
  state and rewind can place the shadows exactly.

### Against players and the client's own body: claim
Other players reach a client through `NetworkTransform`'s internal buffer, which the host cannot rewind. So the
one who saw decides, and the host checks plausibility:
- the client traces its shot or swing against players as it sees them and sends `ShotView.mate` / `mateAt`;
- the host accepts it if the named player is within `ClaimReach` (≈ 3.5 m) of the claimed point, and lets that
  shot hit no other player;
- catching a thrown object, "the object hit me": the client decides by its own picture (`CargoClaimRpc` pattern);
  the host decides alone only for the host player (`LagComp.UsesClaims(player)`);
- never apply damage from a claim without the host-side check.

## Rule 2 — masses move as one snapshot stream

- One host component (`CrowdSync`, ex-`ZombieSync`) sends all moving AI as **unreliable** chunks of ≤ `MaxChunk`
  (900) bytes with the host's timestamp: position (quantised), yaw, state/animation byte.
- Rate by distance to the nearest client: ≤ 20 m — 10 Hz, ≤ 40 m — 5 Hz, farther — 2.5 Hz. A standing AI repeats
  for 3 ticks, then goes quiet. Sleeping/dormant AI sends nothing. No clients → no stream and no history.
- The client keeps a `SnapshotBuffer` and renders at `RenderTime` (latest − ~0.15 s), extrapolating between rare
  snapshots. The same history feeds the host's rewind.
- 1000 `NetworkTransform`s killed the host; 1000 AI as a stream is ~4 KB per tick (~320 kbit/s per client).
- A standing AI on the client is not touched (no transform writes for hundreds of objects that did not move).

## Rule 3 — delivery

- `RpcDelivery.Unreliable`: everything that is only look and sound — blood, tracers, muzzle flashes, hit reactions,
  footsteps, remote shot effects.
- Reliable RPC or `NetworkVariable`: what the game or the UI depends on — death, downed, doors, pickups, cargo,
  objectives, icons like "seen/heard".
- The reliable channel is one ordered stream: every lost reliable packet holds all later reliable messages for a
  resend (≥ ping). Few frequent reliable messages = fewer "lags" under loss. A reliable RPC every frame is forbidden.
- One RPC = one effect on every peer (particles spawn locally), rate-limited.

## Rule 4 — NetworkVariable

- Write only on change: `if (v.Value != x) v.Value = x;`.
- Continuous values: with a threshold and at most 3–10 Hz (a detection meter every 0.3 s, a pitch from 0.5°).
- Owner-writable only for what the owner inputs itself (look, movement mode).

## Rule 5 — sizes

- Transport packet ≤ 1200 bytes (`maxMessageSize`): through Relay (DTLS) full-size 1400 packets are lost and the
  reliable stream stalls forever (client stuck in the lobby, heartbeats keep it "alive"). PMTU and window size are
  not the cause.
- NGO batch: `MaximumTransmissionUnitSize = 1088`.
- One message ≤ ~1000 bytes. Long lists go in chunks. `ReliableFragmentedSequenced` only for one-offs (join, scene
  change), never for a stream.
- Estimate RPC size in review: Vector3 12, float 4, int 4, double 8, bool 1, array = length × element + 4.
- The limits never grow. The pre-commit hook blocks it (`githooks/pre-commit.sh`, `mtu`).

## Rule 6 — what is a NetworkObject

Only what changes game state and is seen by all: doors, containers, pickups, carts, vehicles, the session
manager. Decor, furniture, static props, background cars — plain scene objects. Networked items spawn as one batch
on session start over the reliable channel. An in-scene `NetworkObject` needs fresh ids after a scene rebuild
(`GlobalObjectIdHash`).

## Rule 7 — the network version

A string constant (`GameNet.Version = "0.14.0"`) checked in connection approval: a mismatch is refused with a
clear message ("incompatible game version: host 0.14.0, you 0.13.0"). Bump it, with one line of what changed in its
comment, when RPCs, `NetworkVariable`s, serialized structs, snapshot formats, in-scene `NetworkObject`s or the
network prefab list change. One bump per branch is enough; a merge where both sides changed the format needs a
version above both. The hook checks this against master at the branch point.

## Checklist before a PR that touches the network

- [ ] new client hit checks go through `LagComp`; the host path (`viewTime = 0`) unchanged
- [ ] player-vs-player and own-body events by claim + host check
- [ ] cosmetics unreliable, state reliable, no reliable RPC per frame
- [ ] no message over ~1000 bytes except one-offs
- [ ] network version bumped if the format changed
- [ ] scenarios: the card's own + smoke set; `lagaim` and `lanlag` when hits or sync changed

## Measuring (scenario patterns)

| Scenario | What it proves |
|---|---|
| `lagaim` | host + client on `-netsim 60,10,2` (~150 ms, 2 % loss): N shots and swings at a running AI with rewind on/off; crowd stream numbers (chunks per tick, largest chunk, kbit/s) |
| `lanlag` | the whole session flow on a bad network |
| `onlinelag` | the same through Relay |
| `NETSIM=100,20,3 …` | worse network: rewind still ≥ 90 % |

Budgets that worked: client hits ≥ 90 % at ~150 ms; one chunk ≤ 900 B; 150 wandering AI near one client
< 400 kbit/s; host ≥ 60 fps at max players and max AI; frame hitch < 100 ms.

## What else can be done later (by value)
1. Steam Networking Sockets (SDR relays, route per pair, no Relay traffic bill, friends invites). Same ~1200-byte
   rule. Only network manager creation and the invite flow change.
2. Per-client interest (each client its own stream, far AI rarer): 2–3× less traffic when players spread out, but
   rewind history per client.
3. Delta compression against the last acknowledged snapshot: ~4–5 bytes per AI instead of ~11.
