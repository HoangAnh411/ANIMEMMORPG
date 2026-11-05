$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$manifest=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root 'Docs/U02/Evidence/C/MANIFEST.json') | ConvertFrom-Json
$package=(Resolve-Path -LiteralPath (Join-Path $root $manifest.packageRelativePath)).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U02/C/'))
if(!$package.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Unexpected package path'}
foreach($entry in (Import-Csv -LiteralPath (Join-Path $root 'Docs/U02/Evidence/C/PACKAGE.csv'))){
 $file=[IO.Path]::GetFullPath((Join-Path $package $entry.path))
 if(!$file.StartsWith($package+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file).Hash -ine $entry.sha256){throw ('Package hash mismatch: '+$entry.path)}
}
$cloneSHA=git -C (Join-Path $root 'Artifacts/U02/C/Source') rev-parse HEAD
if($cloneSHA -ne $manifest.sourceSHA){throw 'Review source association changed; inspect REPORT-B'}
$session=Join-Path $root ('Artifacts/U02/C/Review-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
& (Join-Path $PSScriptRoot 'StartCPackage.ps1') -Package $package -OutputRoot $session | Out-Null
$record=Get-Content -Raw -LiteralPath (Join-Path $session 'process.json') | ConvertFrom-Json
Write-Host ('U02-C '+$manifest.sourceSHA+' | LMB attack, Ctrl sprint, Escape/Resume | log '+$record.log)
try { (Get-Process -Id $record.pid).WaitForExit() }
finally { & (Join-Path $PSScriptRoot 'StopCPackage.ps1') -Session $session }
