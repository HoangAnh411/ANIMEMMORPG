param([ValidateSet('L_Boot','L_CharacterCombatLab','L_NetworkLab')][string]$Map='L_Boot')
$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$manifest=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root 'Docs/U01/Evidence/E/MANIFEST.json') | ConvertFrom-Json
$exe=Join-Path $root ($manifest.packageRelativePath+'/AnimeMMORPG.exe')
if(!(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'E package missing; see REPORT-E'}
$user=Join-Path $root 'Artifacts/U01/E/PlayerSettings'
$logs=Join-Path $root 'Artifacts/U01/E/PlayerLogs'
New-Item -ItemType Directory -Force -Path $user,$logs | Out-Null
$log=Join-Path $logs ((Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
$arguments=@(('/Game/AnimeMMORPG/Maps/'+$Map),'-windowed','-ResX=1280','-ResY=720','-U01Trace',('-U01SourceSHA='+$manifest.sourceSHA),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'))
# This launcher intentionally opens the playable package for the user.
Start-Process -FilePath $exe -ArgumentList $arguments | Out-Null
Write-Output ('E source '+$manifest.sourceSHA+'; log '+$log)
