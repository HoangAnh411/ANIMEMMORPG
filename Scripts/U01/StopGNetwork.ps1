$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$latest=Join-Path $root 'Artifacts/U01/G/LatestNetworkReview.txt'
if(!(Test-Path -LiteralPath $latest)){throw 'No G network review session recorded'}
$session=(Get-Content -LiteralPath $latest -Raw -Encoding UTF8).Trim()
& (Join-Path $PSScriptRoot 'StopFSession.ps1') -SessionPath $session -Stage G
