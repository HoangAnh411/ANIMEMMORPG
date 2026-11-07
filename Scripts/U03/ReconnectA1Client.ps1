param([Parameter(Mandatory=$true)][string]$SessionPath)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$session=(Resolve-Path $SessionPath).Path
$allowed=(Resolve-Path (Join-Path $root 'Artifacts/U03/A1')).Path
if(!$session.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Only A1 session reconnect'}
$records=Get-Content -Raw -Encoding UTF8 (Join-Path $session 'processes.json') | ConvertFrom-Json
$old=$records | Where-Object role -eq ClientA
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$old.pid)
if($live){if([IO.Path]::GetFullPath($live.ExecutablePath) -ine [IO.Path]::GetFullPath($old.executable) -or !$live.CommandLine.Contains($old.project) -or !$live.CommandLine.Contains($old.userDir)){throw 'Old client identity mismatch'};Stop-Process -Id $old.pid}
$newUser=Join-Path $session ('ClientA-Reconnect-'+(Get-Date -Format 'HHmmss'));New-Item -ItemType Directory -Path $newUser | Out-Null
$log=Join-Path $newUser 'ClientA.log'
$argsNew=@($old.arguments | ForEach-Object {if($_ -like '-UserDir=*'){'-UserDir="'+$newUser+'"'}elseif($_ -like '-U01FPerfFile=*'){'-U01FPerfFile="'+(Join-Path $newUser 'Frames.jsonl')+'"'}elseif($_ -like '-abslog=*'){'-abslog="'+$log+'"'}elseif($_ -like '-ModelContextProtocolPort=*'){'-ModelContextProtocolPort=18513'}else{$_}})
$p=Start-Process -FilePath $old.executable -ArgumentList $argsNew -WorkingDirectory (Split-Path $old.project) -WindowStyle Normal -PassThru
$new=$old.PSObject.Copy();$new.pid=$p.Id;$new.userDir=$newUser;$new.log=$log;$new.arguments=$argsNew;$new.utc=[DateTime]::UtcNow.ToString('o')
$allFile=Join-Path $session 'all-processes.json';$all=$records;if(Test-Path $allFile){$all=Get-Content -Raw -Encoding UTF8 $allFile | ConvertFrom-Json}
@($all)+@($new) | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $allFile
$new | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $newUser 'process.json')
@($records | Where-Object role -ne ClientA)+@($new) | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $session 'processes.json')
Write-Output $newUser
