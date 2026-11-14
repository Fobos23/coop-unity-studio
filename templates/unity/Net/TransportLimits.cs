using System;
using Unity.Collections;
using Unity.Netcode.Transports.UTP;
using Unity.Networking.Transport;
using Unity.Networking.Transport.Utilities;
using UnityEngine;

namespace __NS__.Net
{
    // Unity Transport driver of the game. Packets are at most MaxMessage bytes: full-size packets are lost through a
    // relay (DTLS) and the reliable stream stalls (a client never gets the scene change). The limits never grow — the
    // pre-commit hook blocks it (hook.conf LIMITS).
    // Autotests: -netsim <delay ms>,<jitter ms>,<loss %> adds the simulator stage to every pipeline; the delay acts on
    // send and receive, so the ping to the host grows by about twice the delay.
    //
    // Install before the transport creates its driver (before StartHost/StartClient):
    //   TransportLimits.Install();
    //   NetworkManager.Singleton.MaximumTransmissionUnitSize = TransportLimits.NgoMtu;
    public class TransportLimits : INetworkStreamDriverConstructor
    {
        public const int MaxMessage = 1200;   // transport packet
        public const int NgoMtu = 1088;       // one NGO batch: MaxMessage minus relay/DTLS headers

        public readonly int delayMs, jitterMs, dropPercent;
        public bool Simulating => delayMs > 0 || jitterMs > 0 || dropPercent > 0;

        public TransportLimits(int delayMs, int jitterMs, int dropPercent)
        {
            this.delayMs = delayMs;
            this.jitterMs = jitterMs;
            this.dropPercent = dropPercent;
        }

        public static TransportLimits Active => UnityTransport.s_DriverConstructor as TransportLimits;

        public static void Install()
        {
            var args = Environment.GetCommandLineArgs();
            int i = Array.IndexOf(args, "-netsim");
            var p = i >= 0 && i + 1 < args.Length ? args[i + 1].Split(',') : new string[0];
            int Get(int k) => k < p.Length && int.TryParse(p[k], out var v) ? Mathf.Max(0, v) : 0;
            UnityTransport.s_DriverConstructor = new TransportLimits(Get(0), Get(1), Get(2));
            if (i >= 0) Debug.Log($"[NetSim] delay={Get(0)}ms jitter={Get(1)}ms drop={Get(2)}%");
        }

        public void CreateDriver(UnityTransport transport, out NetworkDriver driver,
            out NetworkPipeline unreliableFragmentedPipeline,
            out NetworkPipeline unreliableSequencedFragmentedPipeline,
            out NetworkPipeline reliableSequencedPipeline)
        {
            var settings = transport.GetDefaultNetworkSettings();
            var config = settings.GetNetworkConfigParameters();
            config.maxMessageSize = MaxMessage;
            settings.AddRawParameterStruct(ref config);
            if (Simulating)
                settings.WithSimulatorStageParameters(maxPacketCount: 4000, mode: ApplyMode.AllPackets,
                    packetDelayMs: delayMs, packetJitterMs: jitterMs, packetDropPercentage: dropPercent,
                    randomSeed: (uint)Environment.TickCount);
            driver = NetworkDriver.Create(new UDPNetworkInterface(), settings);
            transport.GetDefaultPipelineConfigurations(ref driver, out var uf, out var usf, out var rs);
            unreliableFragmentedPipeline = driver.CreatePipeline(WithSimulator(uf));
            unreliableSequencedFragmentedPipeline = driver.CreatePipeline(WithSimulator(usf));
            reliableSequencedPipeline = driver.CreatePipeline(WithSimulator(rs));
        }

        NativeArray<NetworkPipelineStageId> WithSimulator(NativeArray<NetworkPipelineStageId> stages)
        {
            if (!Simulating) return stages;
            var sim = NetworkPipelineStageId.Get<SimulatorPipelineStage>();
            foreach (var s in stages) if (s.Equals(sim)) return stages;
            var r = new NativeArray<NetworkPipelineStageId>(stages.Length + 1, Allocator.Temp);
            for (int i = 0; i < stages.Length; i++) r[i] = stages[i];
            r[stages.Length] = sim;
            return r;
        }
    }
}
