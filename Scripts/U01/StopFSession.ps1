param([Parameter(Mandatory=$true)][string]$SessionPath)
$ErrorActionPreference='Stop'
$session=(Resolve-Path -LiteralPath $SessionPath).Path
$allowed=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../Artifacts/U01/F')).Path
if(!$session.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated F sessions may be stopped'}
$file=if(Test-Path (Join-Path $session 'all-processes.json')){Join-Path $session 'all-processes.json'}else{Join-Path $session 'processes.json'}
$records=Get-Content -Raw -Encoding UTF8 -LiteralPath $file | ConvertFrom-Json
foreach($record in $records){
 $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
 if(!$live){continue}
 if($live.Name -ne 'UnrealEditor.exe' -or !$live.CommandLine.Contains($record.project) -or !$live.CommandLine.Contains($record.userDir)){throw ('PID identity mismatch; not stopping '+$record.pid)}
 Stop-Process -Id $record.pid
 Write-Output ('Stopped own '+$record.role+' PID '+$record.pid)
}
