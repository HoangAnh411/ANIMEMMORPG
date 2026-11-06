param([Parameter(Mandatory=$true)][string]$Label,[ValidateSet('Baseline','DiagnosticsOff','LowRender')][string]$Profile='Baseline',[int]$Count=2,[int]$Clients=2,[switch]$EditorVisible)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
$windows=@(Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
try{
 $session=& (Join-Path $PSScriptRoot 'StartFocusSession.ps1') -CloneProject (Join-Path $root 'Artifacts/U02/F/Source/AnimeMMORPG.uproject') -OutputRoot (Join-Path $root 'Artifacts/U02/Focus') -MemoryBudget -ClientMaxFPS 60 -ClientCount $Clients -BufferedDiagnostics -Port 17890 -FocusCase $Profile
 ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'original-editor-windows.json')
 if($EditorVisible){Restore-FOriginalEditorWindows $windows}else{foreach($w in $windows){[FReviewHostNative]::ShowWindow([IntPtr][long]$w.hwnd,6) | Out-Null};Start-Sleep -Milliseconds 300}
 $session | Set-Content (Join-Path $root ('Artifacts/U02/Focus/'+$Label+'-session.txt'))
 $probeArgs=@((Join-Path $PSScriptRoot 'ProbeFocus.py'),'--session',$session,'--label',$Label,'--count',$Count,'--seconds','15')
 if($Clients -eq 1){$probeArgs+='--single'}
 & python @probeArgs
 if($LASTEXITCODE -ne 0){throw 'Focus probe failed'}
 & (Join-Path $PSScriptRoot 'StopFocusSession.ps1') -SessionPath $session
 & python (Join-Path $PSScriptRoot 'AnalyzeFocus.py') --session $session --label $Label
 if($LASTEXITCODE -ne 0){throw 'Analysis failed'}
}finally{
 if($session -and (Test-Path (Join-Path $session 'processes.json'))){& (Join-Path $PSScriptRoot 'StopFocusSession.ps1') -SessionPath $session}
 Restore-FOriginalEditorWindows $windows
}
