param([Parameter(Mandatory=$true)][string]$Record)
$ErrorActionPreference='Stop'
$r=Get-Content -Raw -Encoding UTF8 $Record | ConvertFrom-Json
$out=Split-Path $Record
if(Test-Path (Join-Path $out 'HARNESS-EXIT.json')){throw 'Immutable invocation already completed'}
$script=if($r.purpose -eq 'NUMERIC'){'CaptureNumericR1b.py'}elseif($r.purpose -eq 'ILLUSTRATIVE'){'CaptureVideoR1b.py'}else{throw 'Unknown capture purpose'}
$begin=[DateTime]::UtcNow.ToString('o')
& python -u (Join-Path $PSScriptRoot $script) --record $Record 1> (Join-Path $out 'HARNESS-STDOUT.txt') 2> (Join-Path $out 'HARNESS-STDERR.txt')
$code=$LASTEXITCODE
@{script=$script;record=$Record;beginUTC=$begin;endUTC=[DateTime]::UtcNow.ToString('o');exitCode=$code} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $out 'HARNESS-EXIT.json')
exit $code
