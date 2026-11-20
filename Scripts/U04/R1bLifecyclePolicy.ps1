# Production orchestration policy with injectable observations for offline tests.
function Invoke-R1bStopPolicy {
 param($Expected,[scriptblock]$GetLive,[scriptblock]$StopOwned,[scriptblock]$Sleep250,[scriptblock]$NowSeconds,[scriptblock]$GetOtherSessions,$Audit)
 $start=& $NowSeconds
 $live=& $GetLive
 $Audit.polls=@();$Audit.stopRequests=0
 if($live){
  if($live.creationUTC -ne $Expected.creationUTC -or $live.executable -ine $Expected.executable){throw 'Stop identity mismatch/PID reused; refusing action'}
  $requested=& $StopOwned $live
  $Audit.stopRequests=if($requested){1}else{0}
  $deadline=(& $NowSeconds)+30.0
  while($true){
   $live=& $GetLive
   $Audit.polls+=@{elapsedSeconds=((& $NowSeconds)-$start);exists=[bool]$live;creationUTC=if($live){$live.creationUTC}else{$null}}
   if(!$live){$Audit.stopState='EXIT_CONFIRMED';break}
   if($live.creationUTC -ne $Expected.creationUTC -or $live.executable -ine $Expected.executable){throw 'PID reused/identity mismatch while waiting; no further stop or start'}
   if((& $NowSeconds) -ge $deadline){throw 'Stop timeout at30 seconds; no retry or next Start'}
   & $Sleep250
  }
 }else{$Audit.stopState='ALREADY_EXITED'}
 $others=@(& $GetOtherSessions)
 $Audit.otherSessions=$others
 if($others.Count){throw 'Another R1b session remains alive; next Start forbidden'}
 $Audit.elapsedSeconds=((& $NowSeconds)-$start);$Audit.completed=$true;$Audit.oldProcessExited=$true;$Audit.nextStartAllowed=$true
}

function Get-R1bSessions {
 @(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'AnimeMMORPG.exe' -and $_.CommandLine -and $_.CommandLine.Replace('\','/').Contains('Artifacts/U04/B-R1b')} | Select-Object ProcessId,ExecutablePath)
}

function Convert-R1bCreationUTC([DateTime]$Time){
 # Win32_Process CreationDate has microsecond precision; preserve exactly that
 # precision when comparing the stable OS handle's100ns creation timestamp.
 $t=$Time.ToUniversalTime().Ticks
 ([DateTime]::new(($t-($t%10)),[DateTimeKind]::Utc)).ToString('o')
}
