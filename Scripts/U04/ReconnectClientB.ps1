param([Parameter(Mandatory=$true)][string]$SessionPath)
$ErrorActionPreference='Stop'
$root=(Resolve-Path $env:U04B_WORKSPACE_ROOT).Path
$session=(Resolve-Path $SessionPath).Path
$allowed=(Resolve-Path (Join-Path $root 'Artifacts/U04/B')).Path
if(!$session.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Only D session reconnect'}
$records=Get-Content -Raw -Encoding UTF8 (Join-Path $session 'processes.json') | ConvertFrom-Json
$old=$records | Where-Object role -eq ClientA
# Reconnect follows an explicit product Quit. Use native process liveness rather
# than a CIM instance that may outlive an exiting process; never Stop an old PID.
$oldGone=$false
for($attempt=0;$attempt -lt 120;$attempt++){
 $oldNative=Get-Process -Id $old.pid -ErrorAction SilentlyContinue
 if(!$oldNative -or $oldNative.HasExited){$oldGone=$true;break}
 if($old.creationUTC -and [Math]::Abs(($oldNative.StartTime.ToUniversalTime()-[DateTime]::Parse($old.creationUTC).ToUniversalTime()).TotalSeconds) -gt .1){
  @{pid=$old.pid;status='REUSED_PID_PRESERVED';startUTC=$oldNative.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $session 'reconnect-reused-pid.json')
  $oldGone=$true;break
 }
 Start-Sleep -Milliseconds 500
}
if(!$oldGone){throw 'Product Quit process did not exit within60 seconds; no PID stopped'}
@{pid=$old.pid;utc=[DateTime]::UtcNow.ToString('o');method='Native process absent/exited after product Quit; no Stop performed'} | ConvertTo-Json | Set-Content (Join-Path $session 'reconnect-old-exit.json')
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
