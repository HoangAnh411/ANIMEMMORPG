# Snapshot every original Editor window, including already minimized ones.
function Get-U02OriginalEditorWindows([string]$Project){
 . (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
 $records=@()
 foreach($process in (Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'")){
  if($process.CommandLine.Replace('/','\').IndexOf($Project.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -lt 0 -or $process.CommandLine -match ' -game| -server'){continue}
  foreach($handle in [FReviewHostNative]::Windows($process.ProcessId)){$records+=[pscustomobject]@{pid=$process.ProcessId;project=$Project;hwnd=$handle;placement=[FReviewHostNative]::Read([IntPtr]$handle)}}
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
