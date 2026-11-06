if(-not ('U02FocusWindows' -as [type])){
 Add-Type @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
public static class U02FocusWindows {
 [StructLayout(LayoutKind.Sequential)] public struct Point{public int X,Y;}
 [StructLayout(LayoutKind.Sequential)] public struct Rect{public int L,T,R,B;}
 [StructLayout(LayoutKind.Sequential)] public struct Placement{public uint Length,Flags,Show;public Point Min,Max;public Rect Normal;}
 public delegate bool Visitor(IntPtr h,IntPtr p);
 [DllImport("user32.dll")] static extern bool EnumWindows(Visitor f,IntPtr p);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] static extern bool GetWindowPlacement(IntPtr h,ref Placement p);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 public static List<long> Find(uint pid){var a=new List<long>();EnumWindows((h,p)=>{uint id;GetWindowThreadProcessId(h,out id);var v=new Placement();v.Length=(uint)Marshal.SizeOf(v);if(id==pid&&IsWindowVisible(h)&&GetWindowPlacement(h,ref v)&&v.Normal.R-v.Normal.L>=640&&v.Normal.B-v.Normal.T>=360)a.Add(h.ToInt64());return true;},IntPtr.Zero);return a;}
}
'@
}
# Snapshot every original Editor window, including already minimized ones.
function Get-U02OriginalEditorWindows([string]$Project){
 . (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
 $records=@()
 foreach($process in (Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'")){
  if($process.CommandLine.Replace('/','\').IndexOf($Project.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -lt 0 -or $process.CommandLine -match ' -game| -server'){continue}
  foreach($handle in [U02FocusWindows]::Find($process.ProcessId)){$records+=[pscustomobject]@{pid=$process.ProcessId;project=$Project;hwnd=$handle;placement=[FReviewHostNative]::Read([IntPtr]$handle)}}
 }
 return $records
}
# Review-only window placement correction; preserve original records for Stop.
function Confirm-U02EditorMinimized($Records){
 . (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
 foreach($record in $Records){
  $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid);[uint32]$ownerId=0
  [FReviewHostNative]::GetWindowThreadProcessId([IntPtr][long]$record.hwnd,[ref]$ownerId) | Out-Null
  if(!$live -or $live.Name -ne 'UnrealEditor.exe' -or $live.CommandLine.Replace('/','\').IndexOf($record.project.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -lt 0 -or $ownerId -ne $record.pid){throw 'Original Editor window identity changed; cannot verify minimize'}
 }
 # Client startup can restore a floating/owner Editor window after the first minimize.
 # Repeat only at review launch, after both clients are ready; never close/restart Editor.
 for($attempt=0;$attempt -lt 5;$attempt++){
  foreach($record in $Records){[FReviewHostNative]::ShowWindow([IntPtr][long]$record.hwnd,6) | Out-Null}
  Start-Sleep -Milliseconds 100
  $observed=@(foreach($record in $Records){$p=[FReviewHostNative]::Read([IntPtr][long]$record.hwnd);[pscustomobject]@{pid=$record.pid;hwnd=$record.hwnd;show=$p.Show;minimized=($p.Show -eq 2);utc=[DateTime]::UtcNow.ToString('o')}})
  if(@($observed | Where-Object {!$_.minimized}).Count -eq 0){return $observed}
 }
 throw 'Original Editor windows did not remain minimized; review launch is not ready'
}
