param([Parameter(Mandatory=$true)][string]$Script,[Parameter(Mandatory=$true)][string]$RunId,[Parameter(Mandatory=$true)][string]$OutputRoot,[string[]]$CaptureArguments)
$ErrorActionPreference='Stop'
$run=Join-Path $OutputRoot $RunId
if(Test-Path $run){throw 'Immutable capture run already exists'}
New-Item -ItemType Directory -Path $run | Out-Null
$scriptPath=Join-Path $PSScriptRoot $Script
$argsA=@('-X','utf8',$scriptPath)+$CaptureArguments+@('--out',(Join-Path $run 'Capture'))
@{utc=[DateTime]::UtcNow.ToString('o');toolCommit=(git -C (Join-Path $PSScriptRoot '../..') rev-parse HEAD);executable=(Get-Command python).Source;arguments=$argsA;harness=@(Get-ChildItem $PSScriptRoot -File | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash)} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $run 'command.json')
& python @argsA *> (Join-Path $run 'capture.log')
$code=$LASTEXITCODE
@{exitCode=$code;completedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $run 'result.json')
if($code -ne 0){throw ('Capture failed: '+$run)}
Write-Output $run
