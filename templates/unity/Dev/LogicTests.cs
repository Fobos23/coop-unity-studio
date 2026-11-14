using System;
using System.Collections.Generic;
using System.Text;

namespace __NS__.Dev
{
    // Logic tests: pure C# rules (formulas, economy, saves, limit invariants). Run in the open editor by eval:
    //   unity command eval --code 'return __NS__.Dev.LogicTests.Run();' --result-only --no-banner --timeout 120
    // (Tools/dev/logic-tests.sh). The result ends with "pass=N fail=M"; the script requires fail=0.
    // Add a test: a static method taking the context, registered in Tests below. Keep each test free of scenes and time.
    public static class LogicTests
    {
        public sealed class Ctx
        {
            public int pass, fail;
            public readonly StringBuilder log = new StringBuilder();

            public void Check(string name, bool ok, string detail = "")
            {
                if (ok) pass++; else fail++;
                log.Append(ok ? "PASS " : "FAIL ").Append(name).Append(": ").Append(detail).Append('\n');
            }
        }

        static readonly List<(string name, Action<Ctx> body)> Tests = new List<(string, Action<Ctx>)>
        {
            ("net_limits", NetLimits),
        };

        public static string Run()
        {
            var c = new Ctx();
            foreach (var (name, body) in Tests)
            {
                try { body(c); }
                catch (Exception e) { c.Check(name + "_no_exception", false, e.GetType().Name + ": " + e.Message); }
            }
            return c.log.ToString() + $"pass={c.pass} fail={c.fail}";
        }

        // The snapshot chunk fits one NGO batch with headers, and one batch fits one transport packet with relay headers.
        static void NetLimits(Ctx c)
        {
            const int snapshotChunk = 900;   // replace with the crowd stream's MaxChunk when it exists
            c.Check("net_limits_chunk_fits_batch", snapshotChunk + 64 <= Net.TransportLimits.NgoMtu,
                $"chunk={snapshotChunk} mtu={Net.TransportLimits.NgoMtu}");
            c.Check("net_limits_batch_fits_packet", Net.TransportLimits.NgoMtu + 100 <= Net.TransportLimits.MaxMessage,
                $"mtu={Net.TransportLimits.NgoMtu} max={Net.TransportLimits.MaxMessage}");
        }
    }
}
