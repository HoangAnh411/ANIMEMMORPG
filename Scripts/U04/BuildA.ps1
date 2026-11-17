param(
 [Parameter(Mandatory=$true)][string]$Clone,
 [Parameter(Mandatory=$true)][string]$SourceSHA,
 [Parameter(Mandatory=$true)][string]$RunId,
 [Parameter(Mandatory=$true)][string]$OutputRoot,
 [string]$EngineRoot='D:/Software/UE_5.8'
)
$ErrorActionPreference='Stop'
$clonePath=(Resolve-Path $Clone).Path
$expected=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../Artifacts/U04/A/Source'))
if($clonePath -ine $expected){throw 'U04 isolated clone required'}
if((git -C $clonePath rev-parse HEAD) -ne $SourceSHA){throw 'Source mismatch'}
if(@(git -C $clonePath status --porcelain --untracked-files=no).Count){throw 'Dirty clone'}
$run=Join-Path $OutputRoot $RunId
if(Test-Path $run){throw 'Immutable run already exists'}
New-Item -ItemType Directory -Path $run | Out-Null
$project=Join-Path $clonePath 'AnimeMMORPG.uproject'
$engine=Get-Content -Raw (Join-Path $EngineRoot 'Engine/Build/Build.version') | ConvertFrom-Json
if($engine.PatchVersion -ne 4 -or $engine.Changelist -ne 58902052){throw 'Engine identity mismatch'}
git -C $clonePath status --porcelain=v2 --branch | Set-Content (Join-Path $run 'clone-before.txt')
foreach($kind in @('Generate','Editor','Game','Package')){
 $exe=Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat'
 $argsA=if($kind -eq 'Generate'){@('-projectfiles',('-project='+$project),'-game','-rocket')}elseif($kind -eq 'Package'){
  $exe=Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat'
  @('BuildCookRun',('-project='+$project),'-noP4','-platform=Win64','-clientconfig=Development','-build','-cook','-stage','-pak','-archive',('-archivedirectory='+(Join-Path $run 'Archive')),'-map=/Game/AnimeMMORPG/Maps/L_Boot+/Game/AnimeMMORPG/Maps/L_CharacterCombatLab+/Game/AnimeMMORPG/Maps/L_NetworkLab','-unattended','-utf8output','-nocompileeditor','-ubtargs=-WaitMutex')
 }else{@($(if($kind -eq 'Editor'){'AnimeMMORPGEditor'}else{'AnimeMMORPG'}),'Win64','Development',('-Project='+$project),'-WaitMutex','-NoHotReloadFromIDE')}
 @{sourceSHA=$SourceSHA;toolCommit=(git -C (Join-Path $PSScriptRoot '../..') rev-parse HEAD);engine=$engine;executable=$exe;arguments=$argsA;startedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $run ($kind+'.command.json'))
 & $exe @argsA *> (Join-Path $run ($kind+'.log'))
 $code=$LASTEXITCODE
 @{exitCode=$code;completedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $run ($kind+'.result.json'))
 if($code -ne 0){throw ($kind+' failed; see '+$run)}
}
Write-Output $run
