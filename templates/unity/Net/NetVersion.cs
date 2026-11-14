using System.Text;
using Unity.Netcode;

namespace __NS__.Net
{
    // The network version: copies with different versions never play together. Bump Version, with one line of what
    // changed, whenever RPCs, NetworkVariables, serialized structs, snapshot formats, in-scene NetworkObjects or the
    // network prefab list change. One bump per branch; a merge where both sides changed the format needs a version
    // above both. The pre-commit hook checks it (hook.conf NETVERSION_FILE points here).
    //
    // Client, before StartClient:  NetVersion.SetPayload(NetworkManager.Singleton);
    // Host, before StartHost:      NetworkManager.Singleton.NetworkConfig.ConnectionApproval = true;
    //                              NetworkManager.Singleton.ConnectionApprovalCallback = NetVersion.Approve;
    // Client, on disconnect:       show NetworkManager.Singleton.DisconnectReason when it is not empty.
    public static class NetVersion
    {
        public const string Version = "0.1.0"; // 0.1.0 — first network format
        public const int MaxPlayers = 4;

        public static void SetPayload(NetworkManager net) => net.NetworkConfig.ConnectionData = Encoding.UTF8.GetBytes(Version);

        public static void Approve(NetworkManager.ConnectionApprovalRequest req, NetworkManager.ConnectionApprovalResponse res)
        {
            var net = NetworkManager.Singleton;
            string theirs = req.Payload != null ? Encoding.UTF8.GetString(req.Payload) : "";
            bool isHostItself = req.ClientNetworkId == NetworkManager.ServerClientId;
            if (!isHostItself && theirs != Version)
            {
                res.Approved = false;
                res.Reason = $"Incompatible game version: host {Version}, yours {(theirs.Length > 0 ? theirs : "unknown")}";
                return;
            }
            if (!isHostItself && net != null && net.ConnectedClientsIds.Count >= MaxPlayers)
            {
                res.Approved = false;
                res.Reason = $"The session is full ({MaxPlayers} players)";
                return;
            }
            res.Approved = true;
            res.CreatePlayerObject = true;
        }
    }
}
