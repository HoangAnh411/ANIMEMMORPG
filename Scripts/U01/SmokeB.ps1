param(
 [Parameter(Mandatory=$true)][string]$Executable,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{40}$')][string]$SourceSHA,
 [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference='Stop'
$exe=(Resolve-Path -LiteralPath $Executable).Path
$out=Join-Path $OutputRoot ('SmokeB-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $out | Out-Null
$results=@()
foreach($map in @('L_Boot','L_CharacterCombatLab','L_NetworkLab')) {
 $user=Join-Path $out $map
 New-Item -ItemType Directory -Path $user | Out-Null
 $log=Join-Path $user 'Game.log'
 $args=@(('/Game/AnimeMMORPG/Maps/'+$map),'-windowed','-ResX=1280','-ResY=720','-nosplash','-unattended',
   '-U01Trace',('-U01SourceSHA='+$SourceSHA),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'))
 if($map -eq 'L_Boot') { $args+='-ExecCmds="Quit"' } else { $args+='-U01ProbeSeconds=8' }
 @{executable=$exe;arguments=$args;sourceSHA=$SourceSHA;startedUtc=[DateTime]::UtcNow.ToString('o')} |
   ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $user 'command.json')
 $p=Start-Process -FilePath $exe -ArgumentList $args -PassThru -WindowStyle Hidden
 $finished=$p.WaitForExit(120000)
 # Do not automatically kill a potentially visible/manual review session on timeout.
 if(!$finished) { throw ('Smoke timed out; inspect PID '+$p.Id+' and '+$log) }
 $text=Get-Content -Raw -LiteralPath $log
 $failures=@(Select-String -LiteralPath $log -Pattern 'Error:|Fatal|Blueprint Runtime Error|Accessed None|Failed to load' | ForEach-Object Line)
 $loaded=$text -match ('LoadMap.*'+$map)
 $metrics=@(Select-String -LiteralPath $log -Pattern 'LogU01Control: Display: Metrics ' | ForEach-Object {($_.Line -split 'Metrics ',2)[1] | ConvertFrom-Json})
 $ok=($p.ExitCode -eq 0 -and $loaded -and $failures.Count -eq 0)
 if($map -ne 'L_Boot') { $ok=$ok -and $metrics.Count -gt 0 -and @($metrics | Where-Object {$_.error -or $_.sourceSHA -ne $SourceSHA -or !$_.locallyControlled}).Count -eq 0 }
 $results+=[pscustomobject]@{map=$map;bootstrapPID=$p.Id;exitCode=$p.ExitCode;loaded=$loaded;passed=$ok;errors=$failures;log=$log;metrics=$metrics}
 $results | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'results.json')
 Write-Output ($map+' passed='+$ok)
}
Write-Output $out
if(@($results | Where-Object {!$_.passed}).Count -gt 0) { exit 1 }
