$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$manifest=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root 'Evidence/D-R1/MANIFEST.json') | ConvertFrom-Json
$package=(Resolve-Path -LiteralPath (Join-Path $root $manifest.packageRelativePath)).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/D/'))
if(!$package.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Unexpected package path'}
foreach($entry in (Import-Csv -LiteralPath (Join-Path $root 'Evidence/D-R1/PACKAGE.csv'))){
 $file=[IO.Path]::GetFullPath((Join-Path $package $entry.path))
 if(!$file.StartsWith($package+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file).Hash -ine $entry.sha256){throw ('Package hash mismatch: '+$entry.path)}
}
& python (Join-Path $PSScriptRoot 'PrepareDCloneConfig.py') --root (Join-Path $root 'Artifacts/U03/D/Source')
if($LASTEXITCODE -ne 0){throw 'Clone config guard failed'}
if(@(git -C (Join-Path $root 'Artifacts/U03/D/Source') status --porcelain --untracked-files=no).Count){throw 'Review clone tracked source is dirty'}
$cloneSHA=git -C (Join-Path $root 'Artifacts/U03/D/Source') rev-parse HEAD
if($cloneSHA -ne $manifest.source){throw 'Review source association changed; inspect REPORT-D'}
$latest=Join-Path $root 'Artifacts/U03/D/LatestSolo.txt'
if(Test-Path -LiteralPath $latest){
 $previous=(Get-Content -LiteralPath $latest -Raw -Encoding UTF8).Trim()
 if(!$previous.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Unexpected previous D session path'}
 $recordPath=Join-Path $previous 'process.json'
 if(Test-Path -LiteralPath $recordPath){
  $previousRecord=Get-Content -LiteralPath $recordPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$previousRecord.pid)
  if($live -and $live.CommandLine.Contains($previousRecord.log) -and $live.ExecutablePath -ieq $previousRecord.executable){throw 'A D solo session is already running; use Stop-U03-D.cmd before opening another'}
 }
}
$session=Join-Path $root ('Artifacts/U03/D/Review-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
& (Join-Path $PSScriptRoot 'StartDPackage.ps1') -Package $package -OutputRoot $session -SettingsDirectory (Join-Path $root 'Artifacts/U03/D/UserSettings/Solo') | Out-Null
$record=Get-Content -Raw -LiteralPath (Join-Path $session 'process.json') | ConvertFrom-Json
$session | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U03/D/LatestSolo.txt')
Write-Host ('U03-D '+$manifest.source+' | LMB attack, Ctrl sprint, Escape/Resume | log '+$record.log)
try { (Get-Process -Id $record.pid).WaitForExit() }
finally { & (Join-Path $PSScriptRoot 'StopDPackage.ps1') -Session $session }
