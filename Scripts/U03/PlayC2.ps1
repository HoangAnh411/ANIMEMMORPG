$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$manifest=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root 'Docs/U03/Evidence/C2/MANIFEST.json') | ConvertFrom-Json
$package=(Resolve-Path -LiteralPath (Join-Path $root $manifest.packageRelativePath)).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/C2/'))
if(!$package.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Unexpected package path'}
foreach($entry in (Import-Csv -LiteralPath (Join-Path $root 'Docs/U03/Evidence/C2/PACKAGE.csv'))){
 $file=[IO.Path]::GetFullPath((Join-Path $package $entry.path))
 if(!$file.StartsWith($package+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file).Hash -ine $entry.sha256){throw ('Package hash mismatch: '+$entry.path)}
}
& python (Join-Path $PSScriptRoot 'PrepareC2CloneConfig.py') --root (Join-Path $root 'Artifacts/U03/C2/Source')
if($LASTEXITCODE -ne 0){throw 'Clone config guard failed'}
if(@(git -C (Join-Path $root 'Artifacts/U03/C2/Source') status --porcelain --untracked-files=no).Count){throw 'Review clone tracked source is dirty'}
$cloneSHA=git -C (Join-Path $root 'Artifacts/U03/C2/Source') rev-parse HEAD
if($cloneSHA -ne $manifest.source){throw 'Review source association changed; inspect REPORT-C2'}
$session=Join-Path $root ('Artifacts/U03/C2/Review-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
& (Join-Path $PSScriptRoot 'StartC2Package.ps1') -Package $package -OutputRoot $session | Out-Null
$record=Get-Content -Raw -LiteralPath (Join-Path $session 'process.json') | ConvertFrom-Json
$session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U03/C2/LatestSolo.txt')
Write-Host ('U03-C2 '+$manifest.source+' | LMB attack, Ctrl sprint, Escape/Resume | log '+$record.log)
try { (Get-Process -Id $record.pid).WaitForExit() }
finally { & (Join-Path $PSScriptRoot 'StopC2Package.ps1') -Session $session }
