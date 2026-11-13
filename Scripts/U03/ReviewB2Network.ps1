param([int]$Port=17913)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $root 'Artifacts/U03/B2/Source/AnimeMMORPG.uproject'
$manifest=Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Docs/U03/Evidence/B2/MANIFEST.json') | ConvertFrom-Json
if((git -C (Split-Path $project) rev-parse HEAD) -ne $manifest.source){throw 'B2 clone source differs from reviewed binary'}
if((Get-FileHash (Join-Path (Split-Path $project) 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')).Hash -ine $manifest.binaries[0].sha256){throw 'B2 module hash mismatch'}
if((Get-FileHash 'D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe').Hash -ine $manifest.engineExeSHA256){throw 'Engine executable hash mismatch'}
if(Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue){throw 'Network port occupied'}
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
$windows=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject') | Out-Null
try{
 $session=& (Join-Path $PSScriptRoot 'StartB2Session.ps1') -CloneProject $project -OutputRoot (Join-Path $root 'Artifacts/U03/B2') -MemoryBudget -ClientMaxFPS 60 -BufferedDiagnostics -Port $Port
 if(!$session -or !(Test-Path (Join-Path $session 'processes.json'))){throw 'B2 session not ready'}
 ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'original-editor-windows.json')
 . (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
 $observed=@(Confirm-U02EditorMinimized $windows)
 ConvertTo-Json -InputObject $observed -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $session 'editor-minimized-verified.json')
 $session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U03/B2/LatestReview.txt')
 [string]([DateTime]::UtcNow.Ticks)+' b2-off' | Set-Content -Encoding UTF8 (Join-Path $session 'command.txt')
 Write-Host ('U03-B2 ready: '+$session)
 Write-Host 'Left=A, right=B. Resume after focus changes. Stop-U03-B2.cmd restores Editor windows.'
}catch{
 $launchFailure=$_
 if($session -and (Test-Path (Join-Path $session 'processes.json'))){
  try{& (Join-Path $PSScriptRoot 'StopB2Session.ps1') -SessionPath $session}
  catch{Write-Warning ('Session cleanup refused or failed: '+$_.Exception.Message)}
 }
 Restore-FOriginalEditorWindows $windows
 throw $launchFailure
}
