$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$clone=Join-Path $root 'Artifacts/U03/B2/Source'
& python (Join-Path $PSScriptRoot 'PrepareB2CloneConfig.py') --root $clone
if($LASTEXITCODE -ne 0){throw 'Clone config guard failed'}
if(@(git -C $clone status --porcelain --untracked-files=no).Count){throw 'Clone dirty'}
$source=git -C $clone rev-parse HEAD
$run=Join-Path $root ('Artifacts/U03/B2/Runs/Package-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$project=Join-Path $clone 'AnimeMMORPG.uproject'
$exe='D:/Software/UE_5.8/Engine/Build/BatchFiles/RunUAT.bat'
$archive=Join-Path $run 'Archive'
$uat=@('BuildCookRun',('-project='+$project),'-noP4','-platform=Win64','-clientconfig=Development','-build','-cook','-stage','-pak','-archive',('-archivedirectory='+$archive),'-map=/Game/AnimeMMORPG/Maps/L_Boot+/Game/AnimeMMORPG/Maps/L_CharacterCombatLab+/Game/AnimeMMORPG/Maps/L_NetworkLab','-unattended','-utf8output','-nocompileeditor')
@{sourceSHA=$source;project=$project;executable=$exe;arguments=$uat;started=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 7 | Set-Content -Encoding UTF8 (Join-Path $run 'Package.command.json')
& $exe @uat *> (Join-Path $run 'Package.log')
$code=$LASTEXITCODE
@{ExitCode=$code;completed=[DateTime]::UtcNow.ToString('o');Archive=$archive} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $run 'Package.result.json')
if($code -ne 0){throw ('Package failed '+$run)}
Write-Output $archive
