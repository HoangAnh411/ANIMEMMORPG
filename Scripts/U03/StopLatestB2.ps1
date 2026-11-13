$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
foreach($kind in @('Review','Solo')){
 $latest=Join-Path $root ('Artifacts/U03/B2/Latest'+$kind+'.txt')
 if(Test-Path -LiteralPath $latest){
  $session=(Get-Content -LiteralPath $latest -Raw -Encoding UTF8).Trim()
  if($kind -eq 'Review'){& (Join-Path $PSScriptRoot 'StopB2Session.ps1') -SessionPath $session}
  else{& (Join-Path $PSScriptRoot 'StopB2Package.ps1') -Session $session}
 }
}
