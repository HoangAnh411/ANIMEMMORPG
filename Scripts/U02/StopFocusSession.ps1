param([Parameter(Mandatory=$true)][string]$SessionPath,[ValidateSet('F')][string]$Stage='F')
$ErrorActionPreference='Stop'
$session=(Resolve-Path -LiteralPath $SessionPath).Path
$allowed=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot ('../../Artifacts/U02/Focus'))).Path
if(!$session.StartsWith($allowed+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated Focus investigation sessions may be stopped'}
$file=if(Test-Path (Join-Path $session 'all-processes.json')){Join-Path $session 'all-processes.json'}else{Join-Path $session 'processes.json'}
$records=Get-Content -Raw -Encoding UTF8 -LiteralPath $file | ConvertFrom-Json
foreach($record in $records){
 $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
 if(!$live){continue}
 if($live.Name -ne 'UnrealEditor.exe' -or [IO.Path]::GetFullPath($live.ExecutablePath) -ine [IO.Path]::GetFullPath($record.executable) -or (Get-FileHash -LiteralPath $record.executable).Hash -ine $record.binarySHA256 -or !$live.CommandLine.Contains($record.project) -or !$live.CommandLine.Contains($record.userDir)){throw ('PID identity mismatch; not stopping '+$record.pid)}
 Stop-Process -Id $record.pid
 Write-Output ('Stopped own '+$record.role+' PID '+$record.pid)
}

$editorFile=Join-Path $session 'original-editor-windows.json'
if(Test-Path -LiteralPath $editorFile){
 . (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
 Restore-FOriginalEditorWindows (Get-Content -LiteralPath $editorFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}
