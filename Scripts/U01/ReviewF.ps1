param([int]$Port=17877)
$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$manifest=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root 'Docs/U01/Evidence/F/MANIFEST.json') | ConvertFrom-Json
$project=Join-Path $root 'Artifacts/U01/F/Source/AnimeMMORPG.uproject'
$sha=git -C (Split-Path $project) rev-parse HEAD
if($sha -ne $manifest.sourceSHA){throw 'Built F clone source differs from accepted review artifact'}
if(Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue){throw 'Port is occupied; stop your previous F session or choose -Port'}
$output=Join-Path $root 'Artifacts/U01/F/Reviews';New-Item -ItemType Directory -Force -Path $output | Out-Null
$session=& (Join-Path $PSScriptRoot 'StartFSession.ps1') -CloneProject $project -OutputRoot $output -Port $Port
if(!$session -or !(Test-Path (Join-Path $session 'processes.json'))){throw 'Session did not become ready'}
$session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U01/F/LatestReview.txt')
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class FReviewWindows {
 public delegate bool Visitor(IntPtr h,IntPtr p);
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int Left,Top,Right,Bottom;}
 [DllImport("user32.dll")] public static extern bool EnumWindows(Visitor f,IntPtr p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 public static void Show(uint pid){EnumWindows((h,p)=>{uint current;Rect r;GetWindowThreadProcessId(h,out current);GetClientRect(h,out r);if(current==pid&&r.Right>=640&&r.Bottom>=360)ShowWindow(h,9);return true;},IntPtr.Zero);}
}
"@
$records=Get-Content -Raw -Encoding UTF8 (Join-Path $session 'processes.json') | ConvertFrom-Json
foreach($record in $records){if($record.role -ne 'Server'){[FReviewWindows]::Show($record.pid)};Write-Output ($record.role+' PID='+$record.pid)}
Write-Output ('Logs: '+$session)
Write-Output 'Left=A, right=B. Resume in each client; console: U01NetFixture reset (test ground only).'
Write-Output ('Cleanup: powershell -File "'+(Join-Path $PSScriptRoot 'StopFSession.ps1')+'" -SessionPath "'+$session+'"')
