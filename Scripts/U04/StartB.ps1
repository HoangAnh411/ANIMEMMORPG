param(
 [Parameter(Mandatory=$true)][string]$IsolationRoot,
 [Parameter(Mandatory=$true)][string]$Manifest,
 [Parameter(Mandatory=$true)][string]$RunId,
 [ValidateSet(30,60,120)][int]$FPS=30,
 [switch]$Fixture,
 [switch]$InputDiagnostic,
 [switch]$TimingDiagnostic
)
$ErrorActionPreference='Stop'
$isolation=(Resolve-Path -LiteralPath $IsolationRoot).Path
$m=Get-Content -Raw -Encoding UTF8 $Manifest | ConvertFrom-Json
if($m.sourceSHA -notmatch '^[0-9a-f]{40}$'){throw 'Full source SHA required'}
$clone=(Resolve-Path -LiteralPath (Join-Path $isolation 'Source')).Path
if($m.clone -ine $clone){throw 'Build clone mismatch'}
. (Join-Path $PSScriptRoot 'AssertRuntimeB.ps1')
Assert-BRuntime $clone $m.sourceSHA
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
. (Join-Path $PSScriptRoot 'SoloLaunchSpec.ps1')
$spec=New-U04SoloLaunchSpec -Package $package -Output $out -SourceSHA $m.sourceSHA -RunId $RunId -FPS $FPS -Fixture:$Fixture -InputDiagnostic:$InputDiagnostic -TimingDiagnostic:$TimingDiagnostic
# Preserve the Windows command-line form accepted by the packaged launcher.
$arguments=@($spec.arguments | ForEach-Object {
 if($_ -match '^(-(?:UserDir|abslog|ExecCmds|U04BOutput)=)(.*)$'){$Matches[1]+'"'+$Matches[2]+'"'}else{$_}
})
$p=Start-Process -FilePath $spec.executable -ArgumentList $arguments -WorkingDirectory $spec.workingDirectory -WindowStyle Normal -PassThru
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.Id)
@{role='U04BPackage';pid=$p.Id;creationUTC=$live.CreationDate.ToUniversalTime().ToString('o');executable=$exe;binarySHA256=$m.gameSHA256;sourceSHA=$m.sourceSHA;toolSHA=(git -C $clone rev-parse HEAD);isolationRoot=$isolation;buildManifest=[IO.Path]::GetFullPath($Manifest);buildManifestSHA256=(Get-FileHash $Manifest).Hash;userDir=$settings;log=$log;arguments=$arguments;targetFPS=$FPS;fixture=[bool]$Fixture;startedUTC=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $out 'process.json')
Write-Output (Join-Path $out 'process.json')
