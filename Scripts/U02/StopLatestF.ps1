$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$session=(Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Artifacts/U02/F/LatestReview.txt')).Trim()
& (Join-Path $PSScriptRoot 'StopFSession.ps1') -SessionPath $session
