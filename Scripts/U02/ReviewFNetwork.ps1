param([int]$Port=17889)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $root 'Artifacts/U02/F/Source/AnimeMMORPG.uproject'
$manifest=Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Docs/U02/Evidence/F/MANIFEST.json') | ConvertFrom-Json
if((git -C (Split-Path $project) rev-parse HEAD) -ne $manifest.sourceSHA){throw 'F clone source differs from reviewed binary'}
if((Get-FileHash (Join-Path (Split-Path $project) 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')).Hash -ine $manifest.moduleSHA256){throw 'F module hash mismatch'}
if((Get-FileHash 'D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe').Hash -ine $manifest.engineExeSHA256){throw 'Engine executable hash mismatch'}
if(Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue){throw 'Network port occupied'}
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot 'EnsureEditorMinimized.ps1')
$windows=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject') | Out-Null
try{
 $session=& (Join-Path $PSScriptRoot 'StartFSession.ps1') -CloneProject $project -OutputRoot (Join-Path $root 'Artifacts/U02/F') -MemoryBudget -ClientMaxFPS 60 -BufferedDiagnostics -Port $Port
 if(!$session -or !(Test-Path (Join-Path $session 'processes.json'))){throw 'F session not ready'}
 ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'original-editor-windows.json')
 . (Join-Path $PSScriptRoot 'EnsureEditorMinimized.ps1')
 $observed=@(Confirm-U02EditorMinimized $windows)
 ConvertTo-Json -InputObject $observed -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $session 'editor-minimized-verified.json')
 $session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U02/F/LatestReview.txt')
 [string]([DateTime]::UtcNow.Ticks)+' hit' | Set-Content -Encoding UTF8 (Join-Path $session 'command.txt')
 Write-Host ('U02-F ready: '+$session)
 Write-Host 'Left=A, right=B. Resume after focus changes. Stop-U02-F.cmd restores Editor windows.'
}catch{Restore-FOriginalEditorWindows $windows;throw}
