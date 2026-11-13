$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$manifestFile=Join-Path $root 'Docs/U03/Evidence/C1/MANIFEST.json'
$csvFile=Join-Path $root 'Docs/U03/Evidence/C1/PACKAGE.csv'
$manifestBytes=[IO.File]::ReadAllBytes($manifestFile)
$csvBytes=[IO.File]::ReadAllBytes($csvFile)
$checks=@()
function Expect-Refusal([string]$Name,[scriptblock]$Action,[string]$Pattern){
 $caught=$null
 try{& $Action}catch{$caught=$_.Exception.Message}
 if(!$caught -or $caught -notmatch $Pattern){throw ('Unexpected launcher result: '+$Name+' '+$caught)}
 return @{check=$Name;result='PASS';message=$caught}
}
try{
 $entries=Import-Csv -LiteralPath $csvFile
 $entries[0].sha256=('0'*64)
 $entries | Export-Csv -LiteralPath $csvFile -NoTypeInformation -Encoding UTF8
 $checks+=Expect-Refusal 'Package hash mismatch refuses before launching' {& (Join-Path $PSScriptRoot 'PlayC1.ps1')} 'Package hash mismatch'
 [IO.File]::WriteAllBytes($csvFile,$csvBytes)
 $manifest=Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
 $manifest.binaries[0].sha256=('0'*64)
 $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestFile -Encoding UTF8
 $checks+=Expect-Refusal 'Editor module hash mismatch refuses before launching' {& (Join-Path $PSScriptRoot 'ReviewC1Network.ps1')} 'module hash mismatch'
 [IO.File]::WriteAllBytes($manifestFile,$manifestBytes)
 $manifest=Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
 $manifest.source=('0'*40)
 $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestFile -Encoding UTF8
 $checks+=Expect-Refusal 'Clone source mismatch refuses before launching' {& (Join-Path $PSScriptRoot 'ReviewC1Network.ps1')} 'clone source differs'
}finally{
 [IO.File]::WriteAllBytes($manifestFile,$manifestBytes)
 [IO.File]::WriteAllBytes($csvFile,$csvBytes)
}
@{completed=$true;checks=$checks;manifestRestoredByteForByte=([Convert]::ToBase64String([IO.File]::ReadAllBytes($manifestFile)) -eq [Convert]::ToBase64String($manifestBytes));packageIndexRestoredByteForByte=([Convert]::ToBase64String([IO.File]::ReadAllBytes($csvFile)) -eq [Convert]::ToBase64String($csvBytes))} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $root 'Artifacts/U03/C1/Audit/LAUNCH-GUARDS.json')
Write-Output ('PASS '+$checks.Count+' launcher refusal guards; original manifest/index bytes restored')
