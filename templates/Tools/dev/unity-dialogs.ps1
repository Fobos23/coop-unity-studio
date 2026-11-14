# Lists, and with -Press closes, modal Unity Editor windows that block `unity command eval` for ONE project.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File Tools/dev/unity-dialogs.ps1 -Project <path or folder name> [-Press]
# Presses only: Dismiss ("Packages with Errors"), Ignore ("Enter Safe Mode?" - closing it would quit the editor),
# Reload ("modified externally" - closing it would mean Ignore and a later save writes stale data).
# Never presses "Dismiss Forever" (writes ProjectSettings). Other projects' editors are not touched (matched by pid).
param([Parameter(Mandatory = $true)][string]$Project, [switch]$Press)
Add-Type @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class U32 {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr w, EnumProc p, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  public static string Text(IntPtr h) { var s = new StringBuilder(512); GetWindowText(h, s, 512); return s.ToString(); }
  public static string Cls(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
  public static List<IntPtr> Tops(uint pid) { var r = new List<IntPtr>(); EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); if (p == pid && IsWindowVisible(h)) r.Add(h); return true; }, IntPtr.Zero); return r; }
  public static List<IntPtr> Kids(IntPtr w) { var r = new List<IntPtr>(); EnumChildWindows(w, (h, l) => { r.Add(h); return true; }, IntPtr.Zero); return r; }
}
"@
$norm = $Project.Replace('/', '\').TrimEnd('\')
if ($norm.Contains('\')) { $rx = [regex]::Escape($norm) + '(["\s]|$)' }
else { $rx = '[\\/]' + [regex]::Escape($norm) + '(["\s]|$)' }
$procs = Get-CimInstance Win32_Process -Filter "Name='Unity.exe'" | Where-Object {
  $_.CommandLine -and ($_.CommandLine.Replace('/', '\') -match "(?i)$rx") -and $_.CommandLine -notmatch "AssetImportWorker" }
if (-not $procs) { Write-Output "no Unity editor found for project $Project"; exit 0 }
foreach ($p in $procs) {
  foreach ($h in [U32]::Tops([uint32]$p.ProcessId)) {
    $title = [U32]::Text($h)
    if ($title -match "Unity 6") { continue }   # the main editor window
    Write-Output ("pid {0} window [{1}] class {2}" -f $p.ProcessId, $title, [U32]::Cls($h))
    foreach ($k in [U32]::Kids($h)) {
      $t = [U32]::Text($k)
      if ($t -and [U32]::Cls($k) -eq "Button") {
        Write-Output "  button [$t]"
        if ($Press -and ($t -ceq "Dismiss" -or $t -ceq "Ignore" -or $t -ceq "Reload")) {
          [void][U32]::SendMessage($k, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)   # BM_CLICK
          Write-Output "  pressed $t"
        }
      }
    }
  }
}
