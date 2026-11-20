param([Parameter(Mandatory=$true)][string]$Record)
$ErrorActionPreference='Stop'
$r=Get-Content -Raw -Encoding UTF8 $Record | ConvertFrom-Json
if($r.role -ne 'U04R1bPackage'){throw 'Not an owned R1b process record'}
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$r.pid)
if(!$live){return}
if($live.CreationDate.ToUniversalTime().ToString('o') -ne $r.creationUTC -or $live.ExecutablePath -ine $r.executable -or (Get-FileHash $r.executable).Hash -ine $r.binarySHA256){throw 'Refusing Stop: process creation/executable/hash mismatch'}
$cmd=$live.CommandLine.Replace('\','/').ToLowerInvariant()
foreach($scope in @($r.userDir,$r.log,('-U02SourceSHA='+$r.sourceSHA))){if(!$cmd.Contains($scope.Replace('\','/').ToLowerInvariant())){throw 'Refusing Stop: owned command scope mismatch'}}
Stop-Process -Id $r.pid
