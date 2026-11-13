param([Parameter(Mandatory=$true)][string]$Package,[Parameter(Mandatory=$true)][string]$OutputRoot)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/C1/'))
$packagePath=(Resolve-Path -LiteralPath $Package).Path
if(!$packagePath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'C1 package only'}
$exe=Join-Path $packagePath 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
$sha=git -C (Join-Path $root 'Artifacts/U03/C1/Source') rev-parse HEAD
$results=@()
foreach($map in @('L_Boot','L_CharacterCombatLab','L_NetworkLab')){
 $out=Join-Path $OutputRoot $map;New-Item -ItemType Directory -Force -Path $out | Out-Null
 $log=Join-Path $out 'Game.log'
 $arguments=@(('/Game/AnimeMMORPG/Maps/'+$map),'-NullRHI','-nosound','-unattended','-nosplash','-U01Trace',('-U01SourceSHA='+$sha),('-U02SourceSHA='+$sha),('-UserDir="'+$out+'"'),('-abslog="'+$log+'"'))
 if($map -eq 'L_Boot'){$arguments+='-ExecCmds="Quit"'}else{$arguments+='-U01ProbeSeconds=3'}
 $p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $packagePath -WindowStyle Hidden -PassThru
 @{pid=$p.Id;executable=$exe;arguments=$arguments;sourceSHA=$sha;binarySHA256=(Get-FileHash $exe).Hash;world=$map;scope='packaged load smoke, not input'} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
 if(!$p.WaitForExit(60000)){throw ('Smoke did not exit: owned PID '+$p.Id)}
 $text=Get-Content -Raw -Encoding UTF8 -LiteralPath $log
 $loaded=$text -match ('LoadMap: /Game/AnimeMMORPG/Maps/'+$map) -or $text -match ('Bringing World /Game/AnimeMMORPG/Maps/'+$map)
 $fatal=$text -match 'Fatal error:|Assertion failed:|Failed to load package.+/Game/AnimeMMORPG|Couldn.t find file for package'
 $results+=@{map=$map;pid=$p.Id;exitCode=$p.ExitCode;loaded=$loaded;passed=($p.ExitCode -eq 0 -and $loaded -and !$fatal);log=$log;sourceSHA=$sha}
 $results | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $OutputRoot 'results.json')
 if(!$results[-1].passed){throw ('Smoke failed '+$map+'; '+$log)}
}
Write-Output ('PASS 3 packaged maps: '+$OutputRoot)
