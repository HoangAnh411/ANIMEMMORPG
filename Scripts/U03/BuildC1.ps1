$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$clone=Join-Path $root 'Artifacts/U03/C1/Source'
if(@(git -C $clone status --porcelain --untracked-files=no).Count){throw 'Clone tracked source dirty'}
$source=git -C $clone rev-parse HEAD
$project=Join-Path $clone 'AnimeMMORPG.uproject'
$run=Join-Path $root ('Artifacts/U03/C1/Runs/Build-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$engine=Get-Content -Raw 'D:/Software/UE_5.8/Engine/Build/Build.version' | ConvertFrom-Json
$exe='D:/Software/UE_5.8/Engine/Build/BatchFiles/Build.bat'
foreach($kind in @('Generate','Editor','Game')){
 $buildArgs=if($kind -eq 'Generate'){@('-projectfiles',('-project='+$project),'-game','-rocket')}else{@($(if($kind -eq 'Editor'){'AnimeMMORPGEditor'}else{'AnimeMMORPG'}),'Win64','Development',('-Project='+$project),'-WaitMutex','-NoHotReloadFromIDE')}
 @{sourceSHA=$source;project=$project;engine=$engine;executable=$exe;arguments=$buildArgs;started=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 7 | Set-Content -Encoding UTF8 (Join-Path $run ($kind+'.command.json'))
 & $exe @buildArgs *> (Join-Path $run ($kind+'.log'))
 $code=$LASTEXITCODE
 @{ExitCode=$code;completed=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $run ($kind+'.result.json'))
 if($code -ne 0){throw ($kind+' failed: '+$run)}
}
Write-Output ('Build complete '+$run)
