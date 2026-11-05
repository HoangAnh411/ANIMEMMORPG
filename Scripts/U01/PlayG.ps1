param([ValidateSet(30,60,120)][int]$MaxFPS=60)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$manifest=Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Docs/U01/Evidence/G/MANIFEST.json') | ConvertFrom-Json
$package=Join-Path $root $manifest.packagePath
$exe=Join-Path $package 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.gameExecutableSHA256){throw 'G package executable hash mismatch'}
$index=Join-Path $root 'Docs/U01/Evidence/G/PACKAGE.csv'
if((Get-FileHash -LiteralPath $index -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.packageIndexSHA256){throw 'G package index hash mismatch'}
foreach($entry in (Import-Csv -LiteralPath $index)){
 $file=Join-Path $package $entry.PathUnderWindows
 if(!(Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.SHA256){throw ('G package hash mismatch: '+$entry.PathUnderWindows)}
}
& (Join-Path $PSScriptRoot 'StartGPackage.ps1') -Package $package -UserDir (Join-Path $root 'Artifacts/U01/G/ReviewUser') -Map L_Boot -MaxFPS $MaxFPS -Label Review
