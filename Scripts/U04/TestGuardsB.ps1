param([Parameter(Mandatory=$true)][string]$IsolationRoot,[Parameter(Mandatory=$true)][string]$Manifest,[Parameter(Mandatory=$true)][string]$LiveRecord,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
if(Test-Path $Output){throw 'Immutable guard run exists'}
New-Item -ItemType Directory -Path $Output | Out-Null
. (Join-Path $PSScriptRoot 'AssertRuntimeB.ps1')
. (Join-Path $PSScriptRoot 'IdentityB.ps1')
$m=Get-Content -Raw -Encoding UTF8 $Manifest | ConvertFrom-Json
$clone=Join-Path $IsolationRoot 'Source';$checks=@()
function Refuse([string]$Name,[scriptblock]$Action){
 $refused=$false;$message=''
 try{& $Action | Out-Null}catch{$refused=$true;$message=$_.Exception.Message}
 $script:checks+=@{name=$Name;refused=$refused;message=$message}
 if(!$refused){throw ('Guard unexpectedly allowed '+$Name)}
}
Refuse 'unknown source commit' {Assert-BRuntime $clone ('0'*40)}
Refuse 'wrong known runtime source' {Assert-BRuntime $clone '18804bfa32b14471df1ffa4bd7aeaed6cd80074c'}
$fake=$m.PSObject.Copy();$fake.moduleSHA256='0'*64
$fakeFile=Join-Path $Output 'wrong-module.json';$fake | ConvertTo-Json -Depth 30 | Set-Content $fakeFile
Refuse 'wrong Editor module checksum' {Assert-BIdentity $clone $m.sourceSHA $fakeFile (Join-Path $IsolationRoot 'Runs') (Join-Path $IsolationRoot 'Settings/Guards')}
$fake=$m.PSObject.Copy();$fake.gameSHA256='0'*64
$fakeFile=Join-Path $Output 'wrong-package.json';$fake | ConvertTo-Json -Depth 30 | Set-Content $fakeFile
Refuse 'wrong packaged executable checksum' {& (Join-Path $PSScriptRoot 'StartB.ps1') -IsolationRoot $IsolationRoot -Manifest $fakeFile -RunId 'Guard-Must-Not-Launch' -Fixture}
$r=Get-Content -Raw -Encoding UTF8 $LiveRecord | ConvertFrom-Json
$before=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$r.pid)
if(!$before){throw 'Guard preservation probe needs a live owned process'}
$r.role='U04BPackage';$r.creationUTC='1900-01-01T00:00:00.0000000Z'
$fakeFile=Join-Path $Output 'wrong-creation.json';$r | ConvertTo-Json -Depth 10 | Set-Content $fakeFile
Refuse 'Stop wrong creation identity' {& (Join-Path $PSScriptRoot 'StopB.ps1') -Record $fakeFile}
$after=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$r.pid)
$preserved=$after -and $before.CreationDate -eq $after.CreationDate -and $before.ExecutablePath -eq $after.ExecutablePath
@{completed=($preserved -and $checks.Count -eq 5);checks=$checks;ownedLiveProcessPreserved=[bool]$preserved;pid=$r.pid;creationUTC=$before.CreationDate.ToUniversalTime().ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $Output 'RESULTS.json')
if(!$preserved){throw 'Live owned process preservation failed'}
Write-Output 'PASS five guard refusals and live process preservation'
