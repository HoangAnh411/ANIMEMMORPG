param(
 [Parameter(Mandatory=$true)][string]$IsolationRoot,
 [Parameter(Mandatory=$true)][string]$Manifest,
 [Parameter(Mandatory=$true)][string]$RunId,
 [ValidateSet(30,60,120)][int]$FPS=30,
 [switch]$Fixture
)
$ErrorActionPreference='Stop'
$isolation=(Resolve-Path -LiteralPath $IsolationRoot).Path
$m=Get-Content -Raw -Encoding UTF8 $Manifest | ConvertFrom-Json
$clone=(Resolve-Path -LiteralPath (Join-Path $isolation 'Source')).Path
if($m.clone -ine $clone){throw 'Build clone mismatch'}
if(@(git -C $clone diff $m.sourceSHA -- Source Content Config Plugins AnimeMMORPG.uproject).Count){throw 'Runtime inputs changed from built source'}
$package=Join-Path $m.build 'Archive/Windows'
if(![IO.Path]::GetFullPath($package).StartsWith($isolation+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Package outside isolation'}
$out=Join-Path $isolation ('Runs/'+$RunId)
if(Test-Path $out){throw 'Immutable run exists'}
$exe=Join-Path $package 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
if((Get-FileHash -LiteralPath $exe).Hash -ine $m.gameSHA256){throw 'Executable hash mismatch'}
foreach($f in $m.package){if((Get-FileHash -LiteralPath (Join-Path $package $f.path)).Hash -ine $f.sha256){throw 'Package hash mismatch'}}
$settings=Join-Path $out 'User'
$keyB=$settings.Replace('\','/').ToLowerInvariant()
if(@(Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -and $_.Name -in @('AnimeMMORPG.exe','UnrealEditor.exe') -and $_.CommandLine.Replace('\','/').ToLowerInvariant().Contains($keyB)}).Count){throw 'Session conflict'}
New-Item -ItemType Directory -Path $settings | Out-Null
$raw=Join-Path $out 'Raw';New-Item -ItemType Directory -Path $raw | Out-Null
$log=Join-Path $out 'Game.log'
$cmds='t.MaxFPS '+$FPS+',t.IdleWhenNotForeground 0,r.VSync 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'
$map='/Game/AnimeMMORPG/Maps/L_CharacterCombatLab'+$(if($Fixture){'?U03Regression=1'}else{''})
$arguments=@($map,'-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-NoLiveCoding','-U01Trace',('-U01SourceSHA='+$m.sourceSHA),('-U02SourceSHA='+$m.sourceSHA),('-U02RunId='+$RunId),('-UserDir="'+$settings+'"'),('-abslog="'+$log+'"'),('-ExecCmds="'+$cmds+'"'))
if($Fixture){$arguments+=@('-U04BFPSFixture',('-U04BOutput="'+$raw+'"'))}
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $package -WindowStyle Normal -PassThru
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.Id)
@{role='U04BPackage';pid=$p.Id;creationUTC=$live.CreationDate.ToUniversalTime().ToString('o');executable=$exe;binarySHA256=$m.gameSHA256;sourceSHA=$m.sourceSHA;toolSHA=(git -C $clone rev-parse HEAD);isolationRoot=$isolation;buildManifest=[IO.Path]::GetFullPath($Manifest);buildManifestSHA256=(Get-FileHash $Manifest).Hash;userDir=$settings;log=$log;arguments=$arguments;targetFPS=$FPS;fixture=[bool]$Fixture;startedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
Write-Output (Join-Path $out 'process.json')
