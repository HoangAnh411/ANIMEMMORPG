param(
 [Parameter(Mandatory=$true)][string]$Executable,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{40}$')][string]$SourceSHA,
 [Parameter(Mandatory=$true)][string]$OutputRoot,
 [string]$ExistingRun
)
$ErrorActionPreference='Stop'
$exe=(Resolve-Path -LiteralPath $Executable).Path
if($ExistingRun) {
 $out=(Resolve-Path -LiteralPath $ExistingRun).Path
 $previous=Get-Content -Raw -LiteralPath (Join-Path $out 'results.json') | ConvertFrom-Json
} else {
 $out=Join-Path $OutputRoot ('SmokeB-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
 New-Item -ItemType Directory -Path $out | Out-Null
}
$results=@()
foreach($map in @('L_Boot','L_CharacterCombatLab','L_NetworkLab')) {
 $user=Join-Path $out $map
 if(!$ExistingRun) { New-Item -ItemType Directory -Path $user | Out-Null }
 $log=Join-Path $user 'Game.log'
 $args=@(('/Game/AnimeMMORPG/Maps/'+$map),'-windowed','-ResX=1280','-ResY=720','-nosplash','-unattended',
   '-U01Trace',('-U01SourceSHA='+$SourceSHA),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'))
 if($map -eq 'L_Boot') { $args+='-ExecCmds="Quit"' } else { $args+='-U01ProbeSeconds=8' }
 if(!$ExistingRun) {
 @{executable=$exe;arguments=$args;sourceSHA=$SourceSHA;startedUtc=[DateTime]::UtcNow.ToString('o')} |
   ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $user 'command.json')
 $p=Start-Process -FilePath $exe -ArgumentList $args -PassThru -WindowStyle Hidden
 $finished=$p.WaitForExit(120000)
 # Do not automatically kill a potentially visible/manual review session on timeout.
 if(!$finished) { throw ('Smoke timed out; inspect PID '+$p.Id+' and '+$log) }
 $exitCode=$p.ExitCode; $bootstrapPID=$p.Id
 } else {
 $old=@($previous | Where-Object map -eq $map)
 if($old.Count -ne 1) { throw 'Existing run missing unique map record' }
 $exitCode=$old[0].exitCode; $bootstrapPID=$old[0].bootstrapPID
 }
 $text=Get-Content -Raw -LiteralPath $log
 $diagnostics=@(Select-String -LiteralPath $log -Pattern 'Error:|Fatal|Blueprint Runtime Error|Accessed None|Failed to load' | ForEach-Object Line)
 # Keep known optional diagnostics in the report; these are not errors or missing game content.
 $optionalPattern="LogWindows: Failed to load '(aqProf|VtuneApi|VtuneApi32e|WinPixGpuCapturer)\.dll'|LogAudio: Display: No default SoundConcurrencyObject specified"
 $optional=@($diagnostics | Where-Object {$_ -match $optionalPattern})
 $failures=@($diagnostics | Where-Object {$_ -notmatch $optionalPattern})
 $loaded=$text -match ('LoadMap.*'+$map)
 $metrics=@(Select-String -LiteralPath $log -Pattern 'LogU01Control: Display: Metrics ' | ForEach-Object {($_.Line -split 'Metrics ',2)[1] | ConvertFrom-Json})
 $ok=($exitCode -eq 0 -and $loaded -and $failures.Count -eq 0)
 if($map -ne 'L_Boot') { $ok=$ok -and $metrics.Count -gt 0 -and @($metrics | Where-Object {$_.error -or $_.sourceSHA -ne $SourceSHA -or !$_.locallyControlled}).Count -eq 0 }
 $results+=[pscustomobject]@{map=$map;bootstrapPID=$bootstrapPID;exitCode=$exitCode;loaded=$loaded;passed=$ok;errors=$failures;optionalDiagnostics=$optional;log=$log;metrics=$metrics}
 $file=if($ExistingRun){'validated-results.json'}else{'results.json'}
 $results | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out $file)
 Write-Output ($map+' passed='+$ok)
}
Write-Output $out
if(@($results | Where-Object {!$_.passed}).Count -gt 0) { exit 1 }
