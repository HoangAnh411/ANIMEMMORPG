param([Parameter(Mandatory=$true)][string]$SessionPath,[ValidateSet('B')][string]$Stage='B')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'PreserveDLauncherLogs.ps1')
$session=(Resolve-Path -LiteralPath $SessionPath).Path
$allowed=(Resolve-Path -LiteralPath (Join-Path $env:U04B_WORKSPACE_ROOT 'Artifacts/U04/B')).Path
if(!$session.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated U03-D sessions may be stopped'}
$file=if(Test-Path (Join-Path $session 'all-processes.json')){Join-Path $session 'all-processes.json'}else{Join-Path $session 'processes.json'}
$records=Get-Content -Raw -Encoding UTF8 -LiteralPath $file | ConvertFrom-Json
foreach($record in $records){
 $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
 if(!$live){continue}
 if($record.creationUTC -and $live.CreationDate.ToUniversalTime().ToString('o') -ne $record.creationUTC){throw 'Process creation identity mismatch; refusing Stop'}
 if($live.Name -ne 'UnrealEditor.exe' -or [IO.Path]::GetFullPath($live.ExecutablePath) -ine [IO.Path]::GetFullPath($record.executable) -or (Get-FileHash -LiteralPath $record.executable).Hash -ine $record.binarySHA256 -or !$live.CommandLine.Contains($record.project) -or !$live.CommandLine.Contains($record.userDir) -or !$live.CommandLine.Contains($record.log)){throw ('PID identity mismatch; not stopping '+$record.pid)}
 if(!$live.CommandLine.Contains('-U02SourceSHA='+$record.sourceSHA)){throw 'Session source identity mismatch'}
 $module=Join-Path (Split-Path $record.project) 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'
 if((Get-FileHash -LiteralPath $module).Hash -ine $record.moduleSHA256){throw 'Session module identity mismatch'}
 Stop-Process -Id $record.pid
 Wait-Process -Id $record.pid -Timeout 10 -ErrorAction SilentlyContinue
 Write-Output ('Stopped own '+$record.role+' PID '+$record.pid)
}
foreach($record in $records){Restore-U03DStableSdkLog $record}

$editorFile=Join-Path $session 'original-editor-windows.json'
if(Test-Path -LiteralPath $editorFile){
 & (Join-Path $PSScriptRoot 'RestoreEditorB.ps1') -Session $session
}
