# Local review host helpers. No global power policy or Editor preference changes.
if(-not ('FReviewHostNative' -as [type])){
Add-Type @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
public static class FReviewHostNative {
 [StructLayout(LayoutKind.Sequential)] public struct Point {public int X,Y;}
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int Left,Top,Right,Bottom;}
 [StructLayout(LayoutKind.Sequential)] public struct Placement {public uint Length,Flags,Show;public Point Min,Max;public Rect Normal;}
 [StructLayout(LayoutKind.Sequential)] public struct Power {public uint Version,ControlMask,StateMask;}
 public delegate bool Visitor(IntPtr h,IntPtr p);
 [DllImport("user32.dll")] static extern bool EnumWindows(Visitor f,IntPtr p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] static extern bool GetWindowPlacement(IntPtr h,ref Placement p);
 [DllImport("user32.dll")] public static extern bool SetWindowPlacement(IntPtr h,ref Placement p);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetProcessInformation(IntPtr h,int kind,ref Power state,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetProcessInformation(IntPtr h,int kind,ref Power state,uint size);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 public static List<long> Windows(uint pid){var a=new List<long>();EnumWindows((h,p)=>{uint id;Rect r;GetWindowThreadProcessId(h,out id);GetClientRect(h,out r);if(id==pid&&r.Right>=640&&r.Bottom>=360&&IsWindowVisible(h))a.Add(h.ToInt64());return true;},IntPtr.Zero);return a;}
 public static Placement Read(IntPtr h){var p=new Placement();p.Length=(uint)Marshal.SizeOf(p);if(!GetWindowPlacement(h,ref p))throw new Exception("GetWindowPlacement failed");return p;}
 public static void Restore(long hwnd,uint flags,uint show,int left,int top,int right,int bottom){var p=new Placement();p.Length=44;p.Flags=flags;p.Show=show;p.Normal.Left=left;p.Normal.Top=top;p.Normal.Right=right;p.Normal.Bottom=bottom;if(!SetWindowPlacement(new IntPtr(hwnd),ref p))throw new Exception("SetWindowPlacement failed");}
 public static Power Timer(uint pid,bool ignore){IntPtr h=OpenProcess(0x1200,false,pid);if(h==IntPtr.Zero)throw new System.ComponentModel.Win32Exception();try{var s=new Power();s.Version=1;if(!GetProcessInformation(h,4,ref s,12))throw new System.ComponentModel.Win32Exception();var old=s;s.ControlMask|=4;if(ignore)s.StateMask|=4;else s.StateMask&=~4u;if(!SetProcessInformation(h,4,ref s,12))throw new System.ComponentModel.Win32Exception();return old;}finally{CloseHandle(h);}}
}
'@
}
function Set-FServerTimer($Record,[switch]$IgnoreTimerResolution){
 $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$Record.pid)
 if(!$live -or $live.Name -ne 'UnrealEditor.exe' -or !$live.CommandLine.Contains($Record.project) -or !$live.CommandLine.Contains($Record.userDir) -or $Record.role -ne 'Server'){throw 'Dedicated F process identity mismatch'}
 $old=[FReviewHostNative]::Timer($Record.pid,$IgnoreTimerResolution.IsPresent)
 return [pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');pid=$Record.pid;previous=$old;ignoreTimerResolution=$IgnoreTimerResolution.IsPresent;scope='This dedicated process only; honor existing engine timeBeginPeriod request; no tick-rate change'}
}
function Suspend-FOriginalEditorWindows([string]$Project){
 $records=@()
 foreach($process in (Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'")){
  if($process.CommandLine.Replace('/','\').IndexOf($Project.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -lt 0 -or $process.CommandLine -match ' -game| -server'){continue}
  foreach($handle in [FReviewHostNative]::Windows($process.ProcessId)){
   $placement=[FReviewHostNative]::Read([IntPtr]$handle)
   if($placement.Show -eq 2){continue}
   $records+=[pscustomobject]@{pid=$process.ProcessId;project=$Project;hwnd=$handle;placement=$placement}
   [FReviewHostNative]::ShowWindow([IntPtr]$handle,6) | Out-Null
  }
 }
 return $records
}
function Restore-FOriginalEditorWindows($Records){
 foreach($record in $Records){
  $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid);[uint32]$ownerId=0
  [FReviewHostNative]::GetWindowThreadProcessId([IntPtr][long]$record.hwnd,[ref]$ownerId) | Out-Null
  if(!$live -or $live.CommandLine.Replace('/','\').IndexOf($record.project.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -lt 0 -or $ownerId -ne $record.pid){Write-Warning 'Editor window identity changed; not restoring it';continue}
  $p=$record.placement;$b=$p.Normal
  [FReviewHostNative]::Restore($record.hwnd,$p.Flags,$p.Show,$b.Left,$b.Top,$b.Right,$b.Bottom)
 }
}
