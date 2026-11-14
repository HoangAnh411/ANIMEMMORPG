param([ValidateSet('combat','target','route','network','inspect')][string]$Mode,[string]$Record,[string]$Session,[Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out=[IO.Path]::GetFullPath($OutputRoot)
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/C2/'))
if(!$out.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'C2 capture output only'}
New-Item -ItemType Directory -Force -Path $out | Out-Null
$script=Join-Path $PSScriptRoot $(if($Mode -eq 'network'){'CaptureC2Network.py'}else{'CaptureC2Input.py'})
$captureArgs=if($Mode -eq 'network'){@($script,'--session',$Session,'--out',$out)}else{@($script,'--record',$Record,'--out',$out,'--mode',$Mode)}
New-Item -ItemType Directory -Force -Path (Join-Path $out 'harness') | Out-Null
foreach($file in @($script,(Join-Path $PSScriptRoot 'C2Client.py'),(Join-Path $PSScriptRoot 'C2NetworkClient.py'),(Join-Path $root 'Scripts/U01/F60Input.py'),$PSCommandPath)){Copy-Item -LiteralPath $file -Destination (Join-Path $out ('harness/'+(Split-Path $file -Leaf)))}
@{started=[DateTime]::UtcNow.ToString('o');mode=$Mode;executable='python';arguments=@('-X','utf8')+$captureArgs;harnessCommit=(git -C $root rev-parse HEAD);scriptSHA256=(Get-FileHash -LiteralPath $script).Hash;scope='Guarded physical input in recorded C2 processes; sequential input is not simultaneous'} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'command.json')
$ErrorActionPreference='Continue'
& python -X utf8 @captureArgs *> (Join-Path $out 'stdout.log')
$code=$LASTEXITCODE
$ErrorActionPreference='Stop'
@{exitCode=$code;completed=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $out 'process-result.json')
if($code -ne 0){throw ('C2 capture failed: '+$out)}
Write-Output $out
