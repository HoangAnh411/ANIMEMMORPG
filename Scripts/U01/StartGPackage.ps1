param(
 [Parameter(Mandatory=$true)][string]$Package,
 [Parameter(Mandatory=$true)][string]$UserDir,
 [ValidateSet('L_Boot','L_CharacterCombatLab','L_NetworkLab')][string]$Map='L_CharacterCombatLab',
 [ValidateSet(30,60,120)][int]$MaxFPS=60,
 [int]$Width=1280,[int]$Height=720,[string]$Label='Game',
 [switch]$Measure,[switch]$Fullscreen
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$allowed=Join-Path $root 'Artifacts/U01/G/'
$packagePath=(Resolve-Path -LiteralPath $Package).Path
$user=[IO.Path]::GetFullPath($UserDir)
if(!$packagePath.StartsWith($allowed.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -or !$user.StartsWith($allowed.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated G artifacts are allowed'}
$exe=Join-Path $packagePath 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
if(!(Test-Path $exe)){throw 'Packaged game executable missing'}
New-Item -ItemType Directory -Force -Path $user | Out-Null
$sha=git -C (Join-Path $root 'Artifacts/U01/G/Source') rev-parse HEAD
$log=Join-Path $user ($Label+'.log')
$commands='t.MaxFPS '+$MaxFPS+',t.IdleWhenNotForeground 0,r.ScreenPercentage 100'
if($Measure){$commands+=',stat unit'}
$mode=if($Fullscreen){'-fullscreen'}else{'-windowed'}
$arguments=@(('/Game/AnimeMMORPG/Maps/'+$Map),$mode,('-ResX='+$Width),('-ResY='+$Height),'-WinX=0','-WinY=30','-nosplash','-U01Trace',('-U01SourceSHA='+$sha),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'),('-ExecCmds="'+$commands+'"'))
if($Fullscreen){$arguments+='-ForceRes'}
if($Measure){$arguments+=@('-U01FProbe',('-U01FPerfFile="'+(Join-Path $user ($Label+'-frames.jsonl'))+'"'))}
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $packagePath -WindowStyle Normal -PassThru
$record=[pscustomobject]@{role='Package';pid=$p.Id;executable=$exe;project=Join-Path $root 'Artifacts/U01/G/Source/AnimeMMORPG.uproject';sourceSHA=$sha;userDir=$user;log=$log;arguments=$arguments;utc=[DateTime]::UtcNow.ToString('o');requestedFPS=$MaxFPS;requestedWindow=@($Width,$Height);renderer='Unchanged project defaults; internal100%'}
$record | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $user ($Label+'.process.json'))
Write-Output (Join-Path $user ($Label+'.process.json'))
