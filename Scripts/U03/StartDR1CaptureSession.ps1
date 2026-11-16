param([switch]$Visibility,[int]$Port=17923)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
$before=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
$session=$null
try{
 $session=& (Join-Path $PSScriptRoot 'StartDSession.ps1') -CloneProject (Join-Path $root 'Artifacts/U03/D/Source/AnimeMMORPG.uproject') -OutputRoot (Join-Path $root 'Artifacts/U03/D/R1') -MemoryBudget -BufferedDiagnostics -R1VisibilityProbe:$Visibility -Port $Port
 if(!$session -or !(Test-Path (Join-Path $session 'processes.json'))){throw 'Session not ready'}
 ConvertTo-Json -InputObject $before -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'editor-before-loading.json')
 $placement=@(Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
 ConvertTo-Json -InputObject $placement -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'original-editor-windows.json')
 ConvertTo-Json -InputObject @(Confirm-U02EditorMinimized $placement) -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'editor-minimized-verified.json')
 $session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U03/D/R1/LatestSession.txt')
 Write-Output $session
}catch{
 if($session -and (Test-Path (Join-Path $session 'processes.json'))){& (Join-Path $PSScriptRoot 'StopDSession.ps1') -SessionPath $session}
 throw
}
