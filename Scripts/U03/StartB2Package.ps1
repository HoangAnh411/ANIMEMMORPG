param([Parameter(Mandatory=$true)][string]$Package,[Parameter(Mandatory=$true)][string]$OutputRoot,[ValidatePattern('^[0-9a-f]{40}$')][string]$SourceSHA)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/B2/'))
$packagePath=(Resolve-Path -LiteralPath $Package).Path
$out=[IO.Path]::GetFullPath($OutputRoot)
if(!$packagePath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase) -or !$out.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated U03-B2 paths allowed'}
$exe=Join-Path $packagePath 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
if(!(Test-Path -LiteralPath $exe)){throw 'Packaged game missing'}
$sha=git -C (Join-Path $root 'Artifacts/U03/B2/Source') rev-parse HEAD
if($SourceSHA){$sha=$SourceSHA}
New-Item -ItemType Directory -Force -Path $out | Out-Null
. (Join-Path $root 'Scripts/U01/FReviewHost.ps1')
. (Join-Path $root 'Scripts/U02/EnsureEditorMinimized.ps1')
$windows=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
Suspend-FOriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject') | Out-Null
ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'original-editor-windows.json')
$log=Join-Path $out 'Game.log'
$arguments=@('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab','-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-U01Trace','-U02Trace',('-U01SourceSHA='+$sha),('-U02SourceSHA='+$sha),('-U02RunId='+(Split-Path $out -Leaf)),('-UserDir="'+$out+'"'),('-abslog="'+$log+'"'),'-ExecCmds="t.MaxFPS 60,t.IdleWhenNotForeground 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2"')
# This is the interactive Windows input/capture target, so it needs a visible game window.
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $packagePath -WindowStyle Normal -PassThru
@{role='U03PackageB2';project=(Join-Path $root 'Artifacts/U03/B2/Source/AnimeMMORPG.uproject');pid=$p.Id;executable=$exe;binarySHA256=(Get-FileHash -LiteralPath $exe).Hash;sourceSHA=$sha;userDir=$out;log=$log;arguments=$arguments;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
$ready=$false
for($i=0;$i -lt 400;$i++){
 if($p.HasExited){throw ('B2 package exited '+$p.ExitCode)}
 if((Test-Path $log) -and (Select-String -LiteralPath $log -Pattern 'Metrics .*"locallyControlled":true' -Quiet)){$ready=$true;break}
 Start-Sleep -Milliseconds 500
}
if(!$ready){throw 'B2 package not ready; scoped process record retained'}
ConvertTo-Json -InputObject @(Confirm-U02EditorMinimized $windows) -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'editor-minimized-verified.json')
Write-Output (Join-Path $out 'process.json')
