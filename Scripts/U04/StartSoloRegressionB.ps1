param([Parameter(Mandatory=$true)][string]$Package,[Parameter(Mandatory=$true)][string]$OutputRoot,[ValidatePattern('^[0-9a-f]{40}$')][string]$SourceSHA,[Parameter(Mandatory=$true)][string]$RunId,[Parameter(Mandatory=$true)][string]$Manifest,[switch]$TargetFixture,[switch]$Regression,[string]$SettingsDirectory)
$ErrorActionPreference='Stop'
$root=(Resolve-Path $env:U04B_WORKSPACE_ROOT).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U04/B/'))
$packagePath=(Resolve-Path -LiteralPath $Package).Path
$out=[IO.Path]::GetFullPath((Join-Path $OutputRoot $RunId))
if(Test-Path $out){throw 'Immutable session exists'}
if(!$packagePath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase) -or !$out.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Only isolated U03-D paths allowed'}
$exe=Join-Path $packagePath 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
if(!(Test-Path -LiteralPath $exe)){throw 'Packaged game missing'}
$sha=$SourceSHA
if($SourceSHA -ne $sha){throw 'Source mismatch'}
. (Join-Path $PSScriptRoot 'IdentityB.ps1')
$identity=Assert-BIdentity (Join-Path $root 'Artifacts/U04/B/Source') $SourceSHA $Manifest $OutputRoot $SettingsDirectory
if($identity.sourceSHA -ne $sha -or (Get-FileHash $exe).Hash -ine $identity.gameSHA256){throw 'Package identity mismatch'}
foreach($entry in $identity.package){if((Get-FileHash (Join-Path $packagePath $entry.path)).Hash -ine $entry.sha256){throw 'Package content mismatch'}}
New-Item -ItemType Directory -Force -Path $out | Out-Null
. (Join-Path $root 'Scripts/U01/FReviewHost.ps1')
. (Join-Path $root 'Scripts/U02/EnsureEditorMinimized.ps1')
$windows=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))

ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'original-editor-windows.json')
$log=Join-Path $out 'Game.log'
$mapURL='/Game/AnimeMMORPG/Maps/L_CharacterCombatLab'+$(if($TargetFixture){'?U03TabFixture=1'}elseif($Regression){'?U03Regression=1'}else{''})
$userRoot=if($SettingsDirectory){[IO.Path]::GetFullPath($SettingsDirectory)}else{$out}
if(!$userRoot.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'D settings isolation required'}

$settingsKeyA=[IO.Path]::GetFullPath($userRoot).Replace('\','/').ToLowerInvariant()
$usingSettingsA=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('UnrealEditor.exe','AnimeMMORPG.exe') -and $_.CommandLine -and $_.CommandLine.Replace('\','/').ToLowerInvariant().Contains($settingsKeyA)})
if($usingSettingsA.Count){throw 'Settings directory session conflict'}
New-Item -ItemType Directory -Path $userRoot -Force | Out-Null
$arguments=@('-U04AReadOnlyFrames',('-U01FPerfFile="'+(Join-Path $out 'Frames.jsonl')+'"'),$mapURL,'-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-U01Trace','-U02Trace',('-U01SourceSHA='+$sha),('-U02SourceSHA='+$sha),('-U02RunId='+(Split-Path $out -Leaf)),('-UserDir="'+$userRoot+'"'),('-abslog="'+$log+'"'),'-ExecCmds="t.MaxFPS 60,t.IdleWhenNotForeground 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2"')
# This is the interactive Windows input/capture target, so it needs a visible game window.
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $packagePath -WindowStyle Normal -PassThru
@{role='U03PackageD';project=(Join-Path $root 'Artifacts/U04/B/Source/AnimeMMORPG.uproject');creationUTC=(Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.Id)).CreationDate.ToUniversalTime().ToString('o');pid=$p.Id;executable=$exe;binarySHA256=(Get-FileHash -LiteralPath $exe).Hash;sourceSHA=$sha;userDir=$userRoot;log=$log;arguments=$arguments;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
$ready=$false
for($i=0;$i -lt 400;$i++){
 if($p.HasExited){throw ('D package exited '+$p.ExitCode)}
 if((Test-Path $log) -and (Select-String -LiteralPath $log -Pattern 'Metrics .*"locallyControlled":true' -Quiet)){$ready=$true;break}
 Start-Sleep -Milliseconds 500
}
if(!$ready){throw 'D package not ready; scoped process record retained'}
Write-Output (Join-Path $out 'process.json')
