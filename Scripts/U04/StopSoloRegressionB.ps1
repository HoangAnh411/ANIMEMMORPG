param([Parameter(Mandatory=$true)][string]$Session)
$ErrorActionPreference='Stop'
$root=(Resolve-Path $env:U04B_WORKSPACE_ROOT).Path
$sessionPath=(Resolve-Path -LiteralPath $Session).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U04/B/'))
if(!$sessionPath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Not a U03-D session'}
$record=Get-Content -Raw -LiteralPath (Join-Path $sessionPath 'process.json') | ConvertFrom-Json
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
if($live){
 if($record.creationUTC -and $live.CreationDate.ToUniversalTime().ToString('o') -ne $record.creationUTC){throw 'Process creation identity mismatch; refusing Stop'}
 if($record.role -ne 'U03PackageD' -or $live.ExecutablePath -ine $record.executable -or !$live.CommandLine.Contains($record.userDir) -or !$live.CommandLine.Contains($record.log) -or (Get-FileHash -LiteralPath $record.executable).Hash -ne $record.binarySHA256){throw 'Package identity changed; refusing Stop'}
 if(!$live.CommandLine.Contains('-U02SourceSHA='+$record.sourceSHA) -or $record.project -ine (Join-Path $root 'Artifacts/U04/B/Source/AnimeMMORPG.uproject')){throw 'Package project/source identity mismatch'}
 Stop-Process -Id $record.pid
 Wait-Process -Id $record.pid -Timeout 10 -ErrorAction SilentlyContinue
}
. (Join-Path $root 'Scripts/U01/FReviewHost.ps1')
$windows=Get-Content -Raw -LiteralPath (Join-Path $sessionPath 'original-editor-windows.json') | ConvertFrom-Json
& (Join-Path $PSScriptRoot 'RestoreEditorB.ps1') -Session $sessionPath
Write-Output 'Stopped only the owned U03-D session; restored valid original Editor windows'
