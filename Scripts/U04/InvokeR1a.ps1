param([Parameter(Mandatory=$true)][string]$Record,[ValidateSet('numeric','video')][string]$Mode='numeric')
$ErrorActionPreference='Stop'
$r=Get-Content -Raw -Encoding UTF8 $Record | ConvertFrom-Json
$session=Split-Path (Resolve-Path $Record).Path
$prefix=Join-Path $session ('Capture-'+$Mode)
if(Test-Path ($prefix+'.command.json')){throw 'Immutable invocation exists'}
if(!(Test-Path (Join-Path $r.isolationRoot 'Source')) -or !(Join-Path $r.isolationRoot 'Source').Equals((Resolve-Path (Join-Path $PSScriptRoot '../..')).Path,[StringComparison]::OrdinalIgnoreCase)){throw 'R1a tool/clone isolation mismatch'}
$argsA=@('-X','utf8',(Join-Path $PSScriptRoot 'CaptureR1a.py'),'--record',$Record,'--mode',$Mode)
@{utc=[DateTime]::UtcNow.ToString('o');toolCommit=(git -C (Join-Path $PSScriptRoot '../..') rev-parse HEAD);executable=(Get-Command python).Source;arguments=$argsA;sourceSHA=$r.sourceSHA;harness=@(Get-ChildItem $PSScriptRoot -File | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash)} | ConvertTo-Json -Depth 8 | Set-Content ($prefix+'.command.json')
try{$ErrorActionPreference='Continue'; & python @argsA *> ($prefix+'.log');$code=$LASTEXITCODE}finally{$ErrorActionPreference='Stop'}
@{exitCode=$code;completedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content ($prefix+'.result.json')
if($code -ne 0){throw ('R1a capture stopped: '+$prefix)}
