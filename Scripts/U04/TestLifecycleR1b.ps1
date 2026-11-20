$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'R1bLifecyclePolicy.ps1')
$expected=@{creationUTC='original';executable='game.exe'}
if((Convert-R1bCreationUTC ([DateTime]::Parse('2026-11-20T04:22:45.5962182Z'))) -ne '2026-11-20T04:22:45.5962180Z'){throw 'CIM precision normalization failed'}
$results=@()
foreach($case in @('immediate','delayed','already-exited','pid-reused-before','pid-reused-during','timeout','other-session')){
 $state=@{seconds=0.0;kills=0;poll=0};$audit=@{completed=$false}
 $get={
  $state.poll++
  if($case -eq 'already-exited'){return}
  if($case -eq 'immediate' -and $state.kills){return}
  if($case -eq 'delayed' -and $state.seconds -ge 1.0){return}
  if($case -eq 'other-session' -and $state.kills){return}
  if($case -eq 'pid-reused-before' -or ($case -eq 'pid-reused-during' -and $state.kills)){return @{creationUTC='different';executable='game.exe'}}
  return $expected
 }
 $errorText=$null
 try{Invoke-R1bStopPolicy -Expected $expected -GetLive $get -StopOwned {$state.kills++;return $true} -Sleep250 {$state.seconds+=.25} -NowSeconds {$state.seconds} -GetOtherSessions {if($case -eq 'other-session'){@{ProcessId=999}}} -Audit $audit}catch{$errorText=$_.Exception.Message}
 $success=$case -in @('immediate','delayed','already-exited')
 if($audit.completed -ne $success){throw "Wrong verdict: $case"}
 if($state.kills -gt 1 -or ($case -in @('already-exited','pid-reused-before') -and $state.kills -ne 0)){throw "Unsafe kill count: $case"}
 if($case -eq 'timeout' -and $state.seconds -ne 30.0){throw 'Timeout not exactly30 seconds'}
 if($case -eq 'delayed' -and $state.seconds -ne 1.0){throw 'Delayed exit polling incorrect'}
 if(!$success -and !$errorText){throw "Missing failure: $case"}
 $results+=@{case=$case;passed=$true;stopRequests=$state.kills;elapsedSeconds=$state.seconds;expectedError=$errorText;audit=$audit}
}
$results | ConvertTo-Json -Depth 12
