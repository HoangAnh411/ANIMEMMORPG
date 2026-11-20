param([Parameter(Mandatory=$true)][string]$Manifest,[Parameter(Mandatory=$true)][string]$RunId,[Parameter(Mandatory=$true)][ValidateSet(30,60,120)][int]$FPS,[ValidateSet('NUMERIC','ILLUSTRATIVE')][string]$Purpose='NUMERIC')
$ErrorActionPreference='Stop'
$m=Get-Content -Raw -Encoding UTF8 $Manifest | ConvertFrom-Json
$isolation=(Resolve-Path $m.isolationRoot).Path
$out=Join-Path $isolation ('Runs/'+$RunId)
if(Test-Path $out){throw 'Immutable R1b run already exists'}
if(@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'AnimeMMORPG.exe' -and $_.CommandLine -and $_.CommandLine.Replace('\','/').Contains($isolation.Replace('\','/'))}).Count){throw 'Another R1b package process is active'}
New-Item -ItemType Directory -Path $out | Out-Null
& python (Join-Path $PSScriptRoot 'R1bContract.py') --manifest $Manifest --out (Join-Path $out 'IDENTITY-GUARD.json')
if($LASTEXITCODE -ne 0){throw 'Frozen contract/package guard failed; no process started'}
$package=$m.packageRoot;$exe=Join-Path $package 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
$user=Join-Path $out 'User';$raw=Join-Path $out 'Raw';New-Item -ItemType Directory -Path $user,$raw | Out-Null
$log=Join-Path $out 'Game.log'
$cmds='t.MaxFPS '+$FPS+',t.IdleWhenNotForeground 0,r.VSync 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'
$argsA=@('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab?U03Regression=1','-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-NoLiveCoding','-U01Trace',('-U01SourceSHA='+$m.nativeSource),('-U02SourceSHA='+$m.nativeSource),('-U02RunId='+$RunId),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'),('-ExecCmds="'+$cmds+'"'),'-U04BFPSFixture','-U04BInputDiagnostic','-U04BDiagnosticTiming',('-U04BOutput="'+$raw+'"'))
# Visible window is the explicitly requested interactive Windows-input target.
$p=Start-Process -FilePath $exe -ArgumentList $argsA -WorkingDirectory $package -WindowStyle Normal -PassThru
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.Id)
@{role='U04R1bPackage';purpose=$Purpose;pid=$p.Id;creationUTC=$live.CreationDate.ToUniversalTime().ToString('o');executable=$exe;binarySHA256=$m.gameSHA256;sourceSHA=$m.nativeSource;toolSHA=$m.toolCommit;repositoryHEAD=(git -C $m.clone rev-parse HEAD);isolationRoot=$isolation;packageRoot=$package;batchManifest=[IO.Path]::GetFullPath($Manifest);batchManifestSHA256=(Get-FileHash $Manifest).Hash;buildManifest=$m.buildIdentity;buildManifestSHA256=$m.buildIdentitySHA256;moduleSHA256=$m.moduleSHA256;engineSHA256=$m.engineSHA256;userDir=$user;log=$log;arguments=$argsA;targetFPS=$FPS;fixture=$true;startedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
Write-Output (Join-Path $out 'process.json')
