param([ValidateSet('Minimize','Restore')][string]$Mode,[Parameter(Mandatory=$true)][string]$Session,[Parameter(Mandatory=$true)][string]$IsolationRoot,[Parameter(Mandatory=$true)][string]$OriginalProject)
$ErrorActionPreference='Stop'
$path=(Resolve-Path $Session).Path;$isolation=(Resolve-Path $IsolationRoot).Path
if(!$path.StartsWith($isolation+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Session outside diagnostic isolation'}
$pref=Get-Content -Raw (Join-Path $isolation 'Runs/Preflight-20261118/PREFLIGHT.json') | ConvertFrom-Json
foreach($expected in $pref.editor){
 $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$expected.ProcessId)
 if(!$live -or $live.ExecutablePath -ine $expected.ExecutablePath -or $live.CreationDate.ToUniversalTime().ToString('o') -ne $expected.creationUTC){throw 'Original Editor creation identity changed; no placement action'}
}
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
$file=Join-Path $path 'original-editor-windows.json'
if($Mode -eq 'Minimize'){
 $ready=Get-Content -Raw (Join-Path $path 'READINESS.json') | ConvertFrom-Json
 if(!$ready.completed -or (Test-Path $file)){throw 'Fresh readiness/placement record required'}
 $before=@(Suspend-FOriginalEditorWindows $OriginalProject)
 ConvertTo-Json -InputObject $before -Depth 9 | Set-Content -Encoding UTF8 $file
 ConvertTo-Json -InputObject @(Confirm-U02EditorMinimized $before) -Depth 9 | Set-Content -Encoding UTF8 (Join-Path $path 'editor-minimized.json')
}else{
 $before=Get-Content -Raw $file | ConvertFrom-Json
 Restore-FOriginalEditorWindows $before;Start-Sleep -Milliseconds 500
 $after=@(Get-U02OriginalEditorWindows $OriginalProject);$ok=$true
 foreach($b in $before){$a=@($after | Where-Object {$_.pid -eq $b.pid -and $_.hwnd -eq $b.hwnd});if($a.Count -ne 1){$ok=$false;continue};if($a[0].placement.Show -ne $b.placement.Show){$ok=$false};foreach($edge in @('Left','Top','Right','Bottom')){if($a[0].placement.Normal.$edge -ne $b.placement.Normal.$edge){$ok=$false}}}
 @{completed=$ok;windows=$after} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $path 'editor-restored.json')
 if(!$ok){throw 'Original window placement mismatch'}
}
