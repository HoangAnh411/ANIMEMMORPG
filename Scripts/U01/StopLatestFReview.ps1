$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$latest=Join-Path $root 'Artifacts/U01/F/LatestReview.txt'
if(!(Test-Path -LiteralPath $latest)){throw 'No F review session has been launched'}
$session=(Get-Content -LiteralPath $latest -Raw -Encoding UTF8).Trim()
& (Join-Path $PSScriptRoot 'StopFSession.ps1') -SessionPath $session
