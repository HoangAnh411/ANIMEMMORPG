param([Parameter(Mandatory=$true)][string]$SourceSHA,[Parameter(Mandatory=$true)][string]$Manifest,[Parameter(Mandatory=$true)][string]$Package,[Parameter(Mandatory=$true)][string]$Run)
$ErrorActionPreference='Stop'
if(Test-Path $Run){throw 'Immutable guard run exists'}
New-Item -ItemType Directory -Path $Run | Out-Null
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$clone=Join-Path $root 'Artifacts/U04/A/Source'
$settings=Join-Path $Run 'Settings'
$project=Join-Path $clone 'AnimeMMORPG.uproject'
$checks=@()
function Refuse([string]$Name,[scriptblock]$Action,[string]$Pattern){
 $caught=$null;try{& $Action | Out-Null}catch{$caught=$_.Exception.Message}
 if(!$caught -or $caught -notmatch $Pattern){throw ('Unexpected guard outcome: '+$Name+' '+$caught)}
 return @{check=$Name;result='PASS';message=$caught}
}
$before=@(Get-CimInstance Win32_Process | Select-Object ProcessId,ExecutablePath,CreationDate)
$checks+=Refuse 'Wrong source' { & "$PSScriptRoot/StartDPackage.ps1" -Package $Package -OutputRoot $Run -RunId WrongSource -SourceSHA ('0'*40) -Manifest $Manifest -SettingsDirectory $settings } 'Source mismatch'
$bad=Get-Content -Raw $Manifest | ConvertFrom-Json
$bad.moduleSHA256='0'*64
$bad | ConvertTo-Json -Depth 30 | Set-Content (Join-Path $Run 'bad-module.json')
$checks+=Refuse 'Wrong Editor module' { & "$PSScriptRoot/StartDSession.ps1" -CloneProject $project -OutputRoot $Run -RunId WrongModule -SourceSHA $SourceSHA -Manifest (Join-Path $Run 'bad-module.json') -SettingsDirectory $settings -Port 19440 -McpPort 19450 } 'module hash mismatch'
$bad=Get-Content -Raw $Manifest | ConvertFrom-Json
$bad.package[0].sha256='0'*64
$bad | ConvertTo-Json -Depth 30 | Set-Content (Join-Path $Run 'bad-package.json')
$checks+=Refuse 'Wrong package content' { & "$PSScriptRoot/StartDPackage.ps1" -Package $Package -OutputRoot $Run -RunId WrongPackage -SourceSHA $SourceSHA -Manifest (Join-Path $Run 'bad-package.json') -SettingsDirectory $settings } 'Package content mismatch'
$socket=New-Object System.Net.Sockets.UdpClient(19440)
try{$checks+=Refuse 'Occupied network port' { & "$PSScriptRoot/StartDSession.ps1" -CloneProject $project -OutputRoot $Run -RunId OccupiedPort -SourceSHA $SourceSHA -Manifest $Manifest -SettingsDirectory $settings -Port 19440 -McpPort 19450 } 'Port occupied'}finally{$socket.Close()}
New-Item -ItemType Directory -Path (Join-Path $Run 'Existing') | Out-Null
$checks+=Refuse 'Conflicting session output' { & "$PSScriptRoot/StartDPackage.ps1" -Package $Package -OutputRoot $Run -RunId Existing -SourceSHA $SourceSHA -Manifest $Manifest -SettingsDirectory $settings } 'Immutable session exists'
@{completed=$true;checks=$checks;before=$before;after=@(Get-CimInstance Win32_Process | Select-Object ProcessId,ExecutablePath,CreationDate)} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $Run 'result.json')
Write-Output ('PASS '+$checks.Count+' launch refusal guards')
