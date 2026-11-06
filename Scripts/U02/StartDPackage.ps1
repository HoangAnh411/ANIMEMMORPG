param([Parameter(Mandatory=$true)][string]$Package,[Parameter(Mandatory=$true)][string]$OutputRoot,[ValidatePattern('^[0-9a-f]{40}$')][string]$SourceSHA)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U02/D/'))
$packagePath=(Resolve-Path -LiteralPath $Package).Path
$out=[IO.Path]::GetFullPath($OutputRoot)
if(!$packagePath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase) -or !$out.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated U02-D paths allowed'}
$exe=Join-Path $packagePath 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
if(!(Test-Path -LiteralPath $exe)){throw 'Packaged game missing'}
$sha=git -C (Join-Path $root 'Artifacts/U02/D/Source') rev-parse HEAD
if($SourceSHA){$sha=$SourceSHA}
New-Item -ItemType Directory -Force -Path $out | Out-Null
. (Join-Path $root 'Scripts/U01/FReviewHost.ps1')
$windows=@(Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'original-editor-windows.json')
$log=Join-Path $out 'Game.log'
$arguments=@('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab','-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-U01Trace','-U02Trace',('-U01SourceSHA='+$sha),('-U02SourceSHA='+$sha),('-U02RunId='+(Split-Path $out -Leaf)),('-UserDir="'+$out+'"'),('-abslog="'+$log+'"'),'-ExecCmds="t.MaxFPS 60,t.IdleWhenNotForeground 0,r.ScreenPercentage 100"')
# This is the interactive Windows input/capture target, so it needs a visible game window.
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $packagePath -WindowStyle Normal -PassThru
@{role='U02PackageD';pid=$p.Id;executable=$exe;binarySHA256=(Get-FileHash -LiteralPath $exe).Hash;sourceSHA=$sha;userDir=$out;log=$log;arguments=$arguments;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
Write-Output (Join-Path $out 'process.json')
