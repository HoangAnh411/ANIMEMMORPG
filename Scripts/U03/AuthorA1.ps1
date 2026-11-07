param([string]$EngineRoot='D:/Software/UE_5.8')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $root 'Artifacts/U03/A1/Source/AnimeMMORPG.uproject'
if(!(Test-Path -LiteralPath $project)){throw 'A1 clone missing'}
$run=Join-Path $root ('Artifacts/U03/A1/Author-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$script=Join-Path $root 'Artifacts/U03/A1/Source/Scripts/U03/CreateA1Assets.py'
$argsC=@(('"'+$project+'"'),'-run=pythonscript',('-script="'+$script+'"'),'-NullRHI','-nosound','-unattended','-NoLiveCoding','-ModelContextProtocolPort=18033',('-abslog="'+(Join-Path $run 'Editor.log')+'"'))
$process=Start-Process -FilePath $exe -ArgumentList $argsC -WindowStyle Hidden -PassThru
@{pid=$process.Id;exe=$exe;arguments=$argsC;sourceSHA=(& git -C (Split-Path $project) rev-parse HEAD)} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $run 'process.json')
$process.WaitForExit()
@{exitCode=$process.ExitCode;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $run 'result.json')
$output=Join-Path $root 'Artifacts/U03/A1/Source/Saved/U03A1-Authoring.txt'
if($process.ExitCode -ne 0 -or !(Test-Path -LiteralPath $output) -or (Get-Content -Raw -LiteralPath $output) -notlike 'SUCCESS*'){throw ('Authoring failed; '+$run)}
Write-Output ('A1 authoring completed: '+$run)
