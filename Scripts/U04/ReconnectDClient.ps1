param([Parameter(Mandatory=$true)][string]$SessionPath)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$session=(Resolve-Path $SessionPath).Path
$allowed=(Resolve-Path (Join-Path $root 'Artifacts/U04/A')).Path
if(!$session.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Only D session reconnect'}
$records=Get-Content -Raw -Encoding UTF8 (Join-Path $session 'processes.json') | ConvertFrom-Json
$old=$records | Where-Object role -eq ClientA
# Product Quit/Logout can precede OS teardown; wait without killing any process.
Wait-Process -Id $old.pid -Timeout 15 -ErrorAction SilentlyContinue
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$old.pid)
if($live -and $old.creationUTC -and $live.CreationDate.ToUniversalTime().ToString('o') -ne $old.creationUTC){
 @{pid=$old.pid;status='REUSED_PID_PRESERVED';creation=$live.CreationDate} | ConvertTo-Json | Set-Content (Join-Path $session 'reconnect-reused-pid.json')
 $live=$null
}
if($live){
 if(!$live.ExecutablePath -or !$live.CommandLine){throw 'Old client still exiting; identity unavailable, refusing Stop'}
 if([IO.Path]::GetFullPath($live.ExecutablePath) -ine [IO.Path]::GetFullPath($old.executable) -or !$live.CommandLine.Contains($old.project) -or !$live.CommandLine.Contains($old.userDir) -or !$live.CommandLine.Contains($old.log)){throw 'Old client identity mismatch'}
 Stop-Process -Id $old.pid
 Wait-Process -Id $old.pid -Timeout 10 -ErrorAction SilentlyContinue
}
$newUser=Join-Path $session ('ClientA-Reconnect-'+(Get-Date -Format 'HHmmss'));New-Item -ItemType Directory -Path $newUser | Out-Null
$log=Join-Path $newUser 'ClientA.log'
$argsNew=@($old.arguments | ForEach-Object {if($_ -like '-UserDir=*'){'-UserDir="'+$old.userDir+'"'}elseif($_ -like '-U01FPerfFile=*'){'-U01FPerfFile="'+(Join-Path $newUser 'Frames.jsonl')+'"'}elseif($_ -like '-abslog=*'){'-abslog="'+$log+'"'}elseif($_ -like '-ModelContextProtocolPort=*'){('-ModelContextProtocolPort='+([int](($old.arguments | Where-Object {$_ -like '-ModelContextProtocolPort=*'}) -split '=')[1]+10))}else{$_}})
$p=Start-Process -FilePath $old.executable -ArgumentList $argsNew -WorkingDirectory (Split-Path $old.project) -WindowStyle Normal -PassThru
$new=$old.PSObject.Copy();$new.pid=$p.Id;$new.creationUTC=(Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.Id)).CreationDate.ToUniversalTime().ToString('o');$new.userDir=$old.userDir;$new.log=$log;$new.arguments=$argsNew;$new.utc=[DateTime]::UtcNow.ToString('o')
$allFile=Join-Path $session 'all-processes.json';$all=$records;if(Test-Path $allFile){$all=Get-Content -Raw -Encoding UTF8 $allFile | ConvertFrom-Json}
@($all)+@($new) | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $allFile
$new | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $newUser 'process.json')
@($records | Where-Object role -ne ClientA)+@($new) | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'processes.json')
Write-Output $newUser
