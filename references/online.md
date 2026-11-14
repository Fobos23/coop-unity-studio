# Online: Relay, join codes, voice, Steam

## Unity Relay through the Sessions API

- `com.unity.services.multiplayer` Sessions with a custom `INetworkHandler`, so the game still starts NGO itself
  (approval, version, player cap).
- **The SDK calls `INetworkHandler.StartAsync` again on session changes**; a second `StartClient` fails and the SDK
  then stops the network. The handler ignores repeat starts.
- Transport `maxMessageSize = 1200` (`net.md`, rule 5): full-size packets through Relay stall the reliable stream.
- **Region**: without an explicit region the SDK can pick a server on another continent when its QoS probe fails
  (+300 ms on every packet). Measure QoS yourself (ping + loss per region), let the host pick in the menu, fall back
  by time zone, and log `relay QoS`, `relay region=`, `relay server` in the host log. "Lag through Relay" reports
  start from those lines.
- **Join codes**: the SDK rejects codes with letters outside its alphabet before any request, and `Describe` then
  says "no connection": validate the code and show a clear message.
- A connection screen stays up while joining, while the session works, during shutdown, and until the local player
  and a camera exist (a lobby scene without its own camera shows a frozen frame with UI on top at 800 fps).
  Cancel/Esc cancels the join. Connect attempts bounded (≈ 20 s).
- Two copies on one PC: the second host moves off a busy 7777; a connect-by-address menu that always uses the
  default port reaches the first copy.

## VPN on the developer's PC

- A VPN can route the LAN subnet into the tunnel: LAN joins fail ("failed to connect"), 127.0.0.1 works, so
  same-PC autotests cannot see it. The VPN is the director's: they switch it off to test LAN.
- A VPN exit can be IP-blocked by some service dashboards (seen with Unity's Vivox API: bare HTML 403 from the edge),
  while runtime hosts work. Check the API path from another network before blaming the project.
- VPN DNS can break LFS pushes (`unity-windows.md`).

## Voice (Vivox pattern)

- Voice must not depend on Relay: the host creates a room id (GUID) and sends it in the session player data; voice
  connects only with a teammate present.
- Sign in to Unity services before touching `VivoxService.Instance` (null until services init).
- Without credentials the package logs an exception inside `InitializeAsync`; autotests stop on the word
  "Exception", so downgrade Vivox-tagged logs to warnings and check credentials before init.
- `LeaveAllChannelsAsync` starts a login when logged out: skip unless logged in with channels. Dropped channels are
  not rejoined by Vivox.
- Autotests: real voice off unless `-realvoice`; `-voicesim` fakes a ready voice for UI and rules.
- `RTP Timeout (1058)` on both channels = UDP to the voice servers blocked on that network. Plan: if voice fails
  where game traffic passes, voice over the game network (Dissonance) before switching vendors.

## Steam (phase 8)

- Steamworks app (a fee, tax and payout forms take weeks: start early), Steamworks.NET or Facepunch.Steamworks,
  a Netcode transport for Steam Networking Sockets.
- Only network manager creation and the invite flow change; the ~1200-byte rule stays.
- Keep Relay with join codes for dev builds, autotests and playtests before the store page.
- Measure: ping of the same pair of players over Relay and over Steam SDR.
