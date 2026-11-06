param([Parameter(Mandatory=$true)][string]$Session)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$sessionPath=(Resolve-Path -LiteralPath $Session).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U02/D/'))
if(!$sessionPath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Not a U02-D session'}
$record=Get-Content -Raw -LiteralPath (Join-Path $sessionPath 'process.json') | ConvertFrom-Json
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
if($live){
 if($record.role -ne 'U02PackageD' -or $live.ExecutablePath -ine $record.executable -or !$live.CommandLine.Contains($record.userDir) -or (Get-FileHash -LiteralPath $record.executable).Hash -ne $record.binarySHA256){throw 'Package identity changed; refusing Stop'}
 Stop-Process -Id $record.pid
}
. (Join-Path $root 'Scripts/U01/FReviewHost.ps1')
$windows=Get-Content -Raw -LiteralPath (Join-Path $sessionPath 'original-editor-windows.json') | ConvertFrom-Json
Restore-FOriginalEditorWindows $windows
Write-Output 'Stopped only the owned U02-D session; restored valid original Editor windows'
