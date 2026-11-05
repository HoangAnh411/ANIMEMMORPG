param([int]$Port=17879)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $root 'Artifacts/U01/G/Source/AnimeMMORPG.uproject'
$manifest=Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Docs/U01/Evidence/G/MANIFEST.json') | ConvertFrom-Json
if((git -C (Split-Path $project) rev-parse HEAD) -ne $manifest.sourceSHA){throw 'G clone source differs from verified binary source'}
if(Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue){throw 'Network review port occupied; stop the previous session first'}
. (Join-Path $PSScriptRoot 'FReviewHost.ps1')
$windows=@(Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
try{
 $session=& (Join-Path $PSScriptRoot 'StartFSession.ps1') -CloneProject $project -OutputRoot (Join-Path $root 'Artifacts/U01/G') -Stage G -MemoryBudget -ClientMaxFPS 60 -BufferedDiagnostics -Port $Port
 if(!$session -or !(Test-Path (Join-Path $session 'processes.json'))){throw 'G network session did not become ready'}
 ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'original-editor-windows.json')
 $session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U01/G/LatestNetworkReview.txt')
 Write-Host ('G network ready: '+$session)
 Write-Host 'Left=A, right=B. Select Resume after changing focus. Stop-G-Network.cmd restores Editor windows.'
}catch{Restore-FOriginalEditorWindows $windows;throw}
