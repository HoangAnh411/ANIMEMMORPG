param([Parameter(Mandatory=$true)][string]$Record,[Parameter(Mandatory=$true)][string]$Out)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $Out){throw 'Immutable stop proof already exists'}
$r=Get-Content -Raw -Encoding UTF8 $Record | ConvertFrom-Json
if($r.role -ne 'U04R1bPackage'){throw 'Not an owned R1b process record'}
. (Join-Path $PSScriptRoot 'R1bLifecyclePolicy.ps1')
$audit=@{completed=$false;oldProcessExited=$false;nextStartAllowed=$false;record=[IO.Path]::GetFullPath($Record);recordSHA256=(Get-FileHash -LiteralPath $Record).Hash;pid=$r.pid;creationUTC=$r.creationUTC;executable=$r.executable;beginUTC=[DateTime]::UtcNow.ToString('o');timeoutSeconds=30;pollMilliseconds=250}
$watch=[Diagnostics.Stopwatch]::StartNew()
$getLive={
 $v=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$r.pid)
 if($v){@{creationUTC=$v.CreationDate.ToUniversalTime().ToString('o');executable=$v.ExecutablePath;commandLine=$v.CommandLine}}
}
$stopOwned={param($observed)
 if((Get-FileHash -LiteralPath $r.executable).Hash -ine $r.binarySHA256){throw 'Refusing Stop: executable hash mismatch'}
 $cmd=$observed.commandLine.Replace('\','/').ToLowerInvariant()
 foreach($scope in @($r.userDir,$r.log,('-U02SourceSHA='+$r.sourceSHA))){if(!$cmd.Contains($scope.Replace('\','/').ToLowerInvariant())){throw 'Refusing Stop: owned command scope mismatch'}}
 # Pin a stable OS handle before final identity check, avoiding numeric PID reuse.
 try{$owned=[Diagnostics.Process]::GetProcessById([int]$r.pid);$null=$owned.Handle}catch{
  if(!(& $getLive)){return $false};throw
 }
 try{
  $latest=& $getLive
  if(!$latest){return $false}
  if($latest.creationUTC -ne $r.creationUTC -or $latest.executable -ine $r.executable -or (Convert-R1bCreationUTC $owned.StartTime) -ne $r.creationUTC){throw 'Refusing Stop: final handle/creation identity mismatch'}
  $owned.Kill() # exactly one request; no kill retry
  return $true
 }finally{$owned.Dispose()}
}
try{Invoke-R1bStopPolicy -Expected $r -GetLive $getLive -StopOwned $stopOwned -Sleep250 {Start-Sleep -Milliseconds 250} -NowSeconds {$watch.Elapsed.TotalSeconds} -GetOtherSessions {Get-R1bSessions} -Audit $audit}
catch{$audit.error=$_.Exception.Message;throw}
finally{$audit.endUTC=[DateTime]::UtcNow.ToString('o');$audit | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -LiteralPath $Out}
