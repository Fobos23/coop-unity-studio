using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using UnityEngine;
using UnityEngine.InputSystem;

namespace __NS__.Dev
{
    /// <summary>A field the gym panel can turn. Host-only fields are shown read-only on clients (the host is authoritative).</summary>
    [AttributeUsage(AttributeTargets.Field)]
    public sealed class TuneAttribute : Attribute
    {
        public readonly float min, max;
        public readonly bool hostOnly;
        public TuneAttribute(float min, float max, bool hostOnly = true) { this.min = min; this.max = max; this.hostOnly = hostOnly; }
    }

    // Gym harness: exists only when the game starts with -gym <Name> (Tools/dev/gym.sh). A gym is a separate scene for
    // one mechanic with production code, data-driven parameters, distance/speed markers and minimal juice.
    //
    // The same keys in every gym (physical key positions, so a Russian layout works too):
    //   R restart · Tab tuning panel · O overlay · P save values · 1 / 2 load preset A / B · Shift+1 / Shift+2 save
    //   preset A / B · T slow motion x0.25 (host or single player only)
    //
    // In the gym scene's bootstrap:
    //   Gym.Track(weaponConfig, "rifle");            // fields marked [Tune(min, max)] get sliders
    //   Gym.OnRestart = () => GymRange.ResetTargets();
    //   Gym.Overlay("hits", () => $"hits {hits}/{shots}  rewind {LagComp.LastRewindMs} ms");
    //
    // Loading the gym scene is the game's job: after StartHost succeeds, the host start code does
    //   if (Gym.RequestedScene != null) NetworkManager.Singleton.SceneManager.LoadScene(Gym.RequestedScene, LoadSceneMode.Single);
    // instead of opening the lobby; clients started with -autojoin follow the host's scene as usual.
    //
    // Saved values go to <persistentDataPath>/gyms/<gym>[_A|_B].tune as "group.field=value" lines and to the log as
    // "[GYM] saved <gym> group.field=value …". A build cannot write assets: the agent moves the numbers into the data
    // asset by an editor step once the director says "lock it".
    public sealed class Gym : MonoBehaviour
    {
        public static Gym I { get; private set; }
        public static string Name { get; private set; }
        public static Action OnRestart;

        sealed class Entry { public object target; public FieldInfo field; public TuneAttribute tune; public string key; }

        static readonly List<Entry> entries = new List<Entry>();
        static readonly List<(string name, Func<string> text)> overlays = new List<(string, Func<string>)>();

        bool showPanel = true, showOverlay = true, slow;
        Vector2 scroll;
        Rect window = new Rect(12, 12, 360, 520);
        string status = "";

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Init()
        {
            var args = Environment.GetCommandLineArgs();
            int i = Array.IndexOf(args, "-gym");
            if (i < 0 || I != null) return;
            Name = i + 1 < args.Length && !args[i + 1].StartsWith("-") ? args[i + 1] : "gym";
            var go = new GameObject("Gym");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Gym>();
            Debug.Log($"[GYM] {Name} started");
        }

        public static bool Active => I != null;

        /// <summary>The scene name after -gym (the gym scene is named like the gym), or null without -gym. Readable before any scene loads.</summary>
        public static string RequestedScene
        {
            get
            {
                var args = Environment.GetCommandLineArgs();
                int i = Array.IndexOf(args, "-gym");
                return i >= 0 && i + 1 < args.Length && !args[i + 1].StartsWith("-") ? args[i + 1] : null;
            }
        }

        public static void Track(object target, string group)
        {
            if (target == null) return;
            foreach (var f in target.GetType().GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
            {
                var t = f.GetCustomAttribute<TuneAttribute>();
                if (t == null) continue;
                if (f.FieldType != typeof(float) && f.FieldType != typeof(int) && f.FieldType != typeof(bool)) continue;
                entries.Add(new Entry { target = target, field = f, tune = t, key = group + "." + f.Name });
            }
        }

        public static void Overlay(string name, Func<string> text) => overlays.Add((name, text));

        static bool IsAuthority()
        {
            var net = Unity.Netcode.NetworkManager.Singleton;
            return net == null || !net.IsListening || net.IsServer;
        }

        void Update()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            bool shift = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
            if (kb.tabKey.wasPressedThisFrame) showPanel = !showPanel;
            if (kb.oKey.wasPressedThisFrame) showOverlay = !showOverlay;
            if (kb.rKey.wasPressedThisFrame) { OnRestart?.Invoke(); Log("restart"); }
            if (kb.pKey.wasPressedThisFrame) Save("");
            if (kb.digit1Key.wasPressedThisFrame) { if (shift) Save("_A"); else Load("_A"); }
            if (kb.digit2Key.wasPressedThisFrame) { if (shift) Save("_B"); else Load("_B"); }
            if (kb.tKey.wasPressedThisFrame && IsAuthority())
            {
                slow = !slow;
                Time.timeScale = slow ? 0.25f : 1f;
                Log(slow ? "slow motion x0.25" : "normal speed");
            }
        }

        static string FilePath(string suffix) =>
            Path.Combine(Application.persistentDataPath, "gyms", Name + suffix + ".tune");

        void Save(string suffix)
        {
            var sb = new StringBuilder();
            var line = new StringBuilder($"[GYM] saved {Name}{suffix}");
            foreach (var e in entries)
            {
                string v = Format(e.field.GetValue(e.target));
                sb.Append(e.key).Append('=').Append(v).Append('\n');
                line.Append(' ').Append(e.key).Append('=').Append(v);
            }
            var path = FilePath(suffix);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, sb.ToString());
            Debug.Log(line.ToString());
            status = "saved " + Path.GetFileName(path);
        }

        void Load(string suffix)
        {
            var path = FilePath(suffix);
            if (!File.Exists(path)) { status = "no preset " + Path.GetFileName(path); return; }
            bool authority = IsAuthority();
            foreach (var raw in File.ReadAllLines(path))
            {
                int eq = raw.IndexOf('=');
                if (eq <= 0) continue;
                string key = raw.Substring(0, eq), val = raw.Substring(eq + 1);
                foreach (var e in entries)
                    if (e.key == key && (authority || !e.tune.hostOnly)) Set(e, val);
            }
            Log("loaded " + Path.GetFileName(path));
        }

        void Log(string s) { status = s; Debug.Log($"[GYM] {Name}: {s}"); }

        static string Format(object v) => v is float f ? f.ToString("0.###", CultureInfo.InvariantCulture) : Convert.ToString(v, CultureInfo.InvariantCulture);

        static void Set(Entry e, string val)
        {
            var t = e.field.FieldType;
            if (t == typeof(float) && float.TryParse(val, NumberStyles.Float, CultureInfo.InvariantCulture, out var f)) e.field.SetValue(e.target, f);
            else if (t == typeof(int) && int.TryParse(val, out var n)) e.field.SetValue(e.target, n);
            else if (t == typeof(bool) && bool.TryParse(val, out var b)) e.field.SetValue(e.target, b);
        }

        void OnGUI()
        {
            if (showOverlay && overlays.Count > 0)
            {
                var sb = new StringBuilder();
                foreach (var (name, text) in overlays) sb.Append(name).Append(": ").Append(text()).Append('\n');
                GUI.Label(new Rect(Screen.width - 420, 12, 408, 22 * overlays.Count + 8), sb.ToString());
            }
            if (showPanel) window = GUI.Window(73001, window, DrawPanel, $"Gym {Name}{(slow ? "  x0.25" : "")}");
        }

        void DrawPanel(int id)
        {
            bool authority = IsAuthority();
            scroll = GUILayout.BeginScrollView(scroll);
            foreach (var e in entries)
            {
                bool locked = e.tune.hostOnly && !authority;
                GUI.enabled = !locked;
                object v = e.field.GetValue(e.target);
                GUILayout.Label($"{e.key} = {Format(v)}{(locked ? "  (host)" : "")}");
                if (v is float f)
                {
                    float nf = GUILayout.HorizontalSlider(f, e.tune.min, e.tune.max);
                    if (!Mathf.Approximately(nf, f)) e.field.SetValue(e.target, nf);
                }
                else if (v is int n)
                {
                    int nn = Mathf.RoundToInt(GUILayout.HorizontalSlider(n, e.tune.min, e.tune.max));
                    if (nn != n) e.field.SetValue(e.target, nn);
                }
                else if (v is bool b)
                {
                    bool nb = GUILayout.Toggle(b, "on");
                    if (nb != b) e.field.SetValue(e.target, nb);
                }
                GUI.enabled = true;
            }
            GUILayout.EndScrollView();
            GUILayout.Label("R restart · Tab panel · O overlay · P save · 1/2 preset · Shift+1/2 save preset · T slow");
            if (status.Length > 0) GUILayout.Label(status);
            GUI.DragWindow();
        }
    }
}
