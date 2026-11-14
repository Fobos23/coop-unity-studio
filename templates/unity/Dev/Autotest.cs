using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace __NS__.Dev
{
    // Autotest harness of the built player. It exists only when the game starts with -scenario, -autohost, -autojoin
    // or -joincode (Tools/dev/autotest.sh passes them), so a normal launch never creates it.
    //
    // Log contract, parsed by Tools/dev/autotest.sh, run-suite.sh and the autotest-runner agent:
    //   [AUTOTEST] CHECK PASS <name>: <detail>        [AUTOTEST] CHECK FAIL <name>: <detail>
    //   [AUTOTEST] SUMMARY <scenario> pass=N fail=M failed=[a, b]
    //   [AUTOTEST] PERF <scenario> fps=.. min=.. <more fields>
    //   [AUTOTEST] host=True port=<port>              (the network code calls HostStarted after StartHost succeeds)
    //
    // A scenario is a coroutine registered by name. It runs on every copy started with -scenario <name>: the host and
    // the clients (branch on NetworkManager.Singleton.IsServer). The host's SUMMARY ends the run; a client writes its
    // own CHECK lines into its own log (c1.log).
    //
    //   [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    //   static void Register() => Autotest.Register("coop", Coop);
    //   static IEnumerator Coop(Autotest t)
    //   {
    //       yield return t.Until(() => Session.Started, 60f, "session_started");
    //       if (!t.LastOk) yield break;
    //       t.Check("players_in", Session.Players == 2, $"players={Session.Players}");
    //       yield return t.Shot("lobby");
    //   }
    public sealed class Autotest : MonoBehaviour
    {
        public static Autotest I { get; private set; }
        public static string Scenario => Arg("-scenario");
        public static string ShotsDir => Arg("-shots");
        public static bool Headless => Application.isBatchMode || SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null;

        static readonly Dictionary<string, Func<Autotest, IEnumerator>> scenarios = new Dictionary<string, Func<Autotest, IEnumerator>>();

        int passCount, failCount, shotIndex;
        readonly List<string> failures = new List<string>();
        bool summarized;

        /// <summary>True when the last Until() saw its condition before the timeout.</summary>
        public bool LastOk { get; private set; }

        public static void Register(string name, Func<Autotest, IEnumerator> body) => scenarios[name] = body;

        /// <summary>Value after the flag; "" when the flag has no value; null when the flag is absent.</summary>
        public static string Arg(string name)
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length; i++)
                if (args[i] == name) return i + 1 < args.Length && !args[i + 1].StartsWith("-") ? args[i + 1] : "";
            return null;
        }

        public static bool Has(string name) => Arg(name) != null;

        public static int ArgInt(string name, int fallback) => int.TryParse(Arg(name), out var v) ? v : fallback;

        public static void HostStarted(int port) => Debug.Log($"[AUTOTEST] host=True port={port}");

        static void Log(string s) => Debug.Log("[AUTOTEST] " + s);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Init()
        {
            if (!Has("-scenario") && !Has("-autohost") && !Has("-autojoin") && !Has("-joincode")) return;
            if (I != null) return;
            var go = new GameObject("Autotest");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Autotest>();
        }

        IEnumerator Start()
        {
            var name = Scenario;
            if (string.IsNullOrEmpty(name)) yield break;   // a plain -autohost/-autojoin copy: the game's own code joins
            if (!scenarios.TryGetValue(name, out var body))
            {
                Check("scenario_known", false, $"no scenario registered as '{name}'");
                Summary(name);
                yield break;
            }
            yield return null;
            var it = body(this);
            while (true)
            {
                object current;
                try
                {
                    if (!it.MoveNext()) break;
                    current = it.Current;
                }
                catch (Exception e)
                {
                    Check("scenario_no_exception", false, e.GetType().Name + ": " + e.Message);
                    Debug.LogException(e);
                    break;
                }
                yield return current;
            }
            Summary(name);
        }

        public void Check(string name, bool ok, string detail = "")
        {
            if (ok) passCount++;
            else { failCount++; failures.Add(name); }
            Log($"CHECK {(ok ? "PASS" : "FAIL")} {name}: {detail}");
        }

        public void Summary(string scenario)
        {
            if (summarized) return;
            summarized = true;
            Log($"SUMMARY {scenario} pass={passCount} fail={failCount} failed=[{string.Join(", ", failures)}]");
        }

        public static void Perf(string scenario, string fields) => Log($"PERF {scenario} {fields}");

        /// <summary>Waits for cond up to timeout seconds (unscaled). With a check name, records PASS/FAIL. Sets LastOk.</summary>
        public IEnumerator Until(Func<bool> cond, float timeout, string check = null, string detail = null)
        {
            float start = Time.realtimeSinceStartup;
            bool ok = false;
            while (Time.realtimeSinceStartup - start < timeout)
            {
                if (cond()) { ok = true; break; }
                yield return null;
            }
            LastOk = ok;
            if (check != null)
                Check(check, ok, detail ?? (ok ? $"after {Time.realtimeSinceStartup - start:0.0}s" : $"timeout {timeout:0}s"));
        }

        /// <summary>Screenshot into -shots as NN_name.png at the end of this frame; skipped without -shots or graphics.</summary>
        public IEnumerator Shot(string name)
        {
            var dir = ShotsDir;
            if (string.IsNullOrEmpty(dir) || Headless) yield break;
            Directory.CreateDirectory(dir);
            yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(Path.Combine(dir, $"{shotIndex++:00}_{name}.png"));
            yield return null;
        }
    }
}
