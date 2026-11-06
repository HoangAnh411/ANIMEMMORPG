param([string]$EngineRoot='D:/Software/UE_5.8')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $root 'Artifacts/U02/D/Source/AnimeMMORPG.uproject'
$run=Join-Path $root ('Artifacts/U02/D/Author-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$script=Join-Path $root 'Artifacts/U02/D/Source/Scripts/U02/CreateDStations.py'
$argsD=@(('"'+$project+'"'),'-run=pythonscript',('-script="'+$script+'"'),'-NullRHI','-nosound','-unattended','-NoLiveCoding','-ModelContextProtocolPort=18027',('-abslog="'+(Join-Path $run 'Editor.log')+'"'))
$p=Start-Process -FilePath $exe -ArgumentList $argsD -WindowStyle Hidden -PassThru
@{pid=$p.Id;exe=$exe;arguments=$argsD;sourceSHA=(& git -C (Split-Path $project) rev-parse HEAD)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $run 'process.json')
$p.WaitForExit();@{exitCode=$p.ExitCode;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $run 'result.json')
if($p.ExitCode -ne 0 -or !(Select-String -Path (Join-Path $run 'Editor.log') -Pattern 'U02D_AUTHOR_SUCCESS')){throw ('Author failed '+$run)}
Write-Output $run
