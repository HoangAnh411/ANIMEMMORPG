param(
 [Parameter(Mandatory=$true)][string]$CloneProject,
 [Parameter(Mandatory=$true)][string]$OutputRoot,
 [Parameter(Mandatory=$true)][string]$SourceSHA,
 [Parameter(Mandatory=$true)][string]$RunId,
 [Parameter(Mandatory=$true)][string]$SettingsDirectory,
 [Parameter(Mandatory=$true)][string]$Manifest,
 [int]$McpPort=19410,
 [switch]$ReproducePython,
 [switch]$Diagnostics,
 [switch]$MemoryBudget,
 [ValidateSet(30,60)][int]$ClientMaxFPS=60,
 [ValidateSet(1,2)][int]$ClientCount=2,
 [switch]$BufferedDiagnostics,
 [switch]$PersistSettings,
 [switch]$R1VisibilityProbe,
 [int]$Port=19400,
 [ValidateSet('B')][string]$Stage='B'
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot 'PreserveLauncherLogsB.ps1')
$project=(Resolve-Path -LiteralPath $CloneProject).Path
if($project -notlike '*\Artifacts\U04\B-R1a\Source\*'){throw 'Isolated stage clone required'}
& python (Join-Path $PSScriptRoot 'PrepareB.py') --root (Split-Path $project)
if($LASTEXITCODE -ne 0){throw 'Clone config guard failed'}
if(@(git -C (Split-Path $project) status --porcelain --untracked-files=no).Count){throw 'Clone tracked tree is dirty'}
$sha=$SourceSHA
if($sha -ne $SourceSHA){throw 'Source mismatch'}
if(Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue){throw 'Port occupied'}
if(Get-NetTCPConnection -LocalPort $McpPort -ErrorAction SilentlyContinue){throw 'MCP port occupied'}
. (Join-Path $PSScriptRoot 'IdentityB.ps1')
$identity=Assert-BIdentity (Split-Path $project) $SourceSHA $Manifest $OutputRoot $SettingsDirectory
foreach($portCheck in @($McpPort,($McpPort+1),($McpPort+2))){if(Get-NetTCPConnection -LocalPort $portCheck -ErrorAction SilentlyContinue){throw 'MCP port occupied'}}
$exe='D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$run=Join-Path $OutputRoot $RunId
if(Test-Path $run){throw 'Immutable session exists'}
New-Item -ItemType Directory -Path $run | Out-Null

$settingsKeyA=[IO.Path]::GetFullPath($SettingsDirectory).Replace('\','/').ToLowerInvariant()
$usingSettingsA=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('UnrealEditor.exe','AnimeMMORPG.exe') -and $_.CommandLine -and $_.CommandLine.Replace('\','/').ToLowerInvariant().Contains($settingsKeyA)})
if($usingSettingsA.Count){throw 'Settings directory session conflict'}
$records=@()
try{
$roles=if($ClientCount -eq 1){@('Server','ClientA')}else{@('Server','ClientA','ClientB')}
foreach($role in $roles){
 $user=Join-Path $run $role;New-Item -ItemType Directory -Path $user | Out-Null
 $log=Join-Path $user ($role+'.log')
 $settingsRoot=Join-Path $SettingsDirectory $role
 $settingsRoot=[IO.Path]::GetFullPath($settingsRoot)
 New-Item -ItemType Directory -Path $settingsRoot -Force | Out-Null
 if($PersistSettings -and $role -ne 'Server'){Backup-U03DStableSdkLog $user $settingsRoot}
 $arguments=@(('"'+$project+'"'),'-U04R1InputTrace')
 if($role -eq 'Server'){$arguments+=@('/Game/AnimeMMORPG/Maps/L_NetworkLab','-server',('-port='+$Port),'-NullRHI','-nosound')}
 else{$arguments+=@(('127.0.0.1:'+$Port),'-game','-windowed','-ResX=900','-ResY=540',('-WinX='+$(if($role -eq 'ClientA'){0}else{940})),'-WinY=100')}
 if($ReproducePython){if($role -ne 'Server'){$arguments+='-NullRHI'}}else{$arguments+='-DisablePython'}
 if($Diagnostics){$arguments+='-U01FPerf'}
 if($R1VisibilityProbe){$arguments+='-U03R1VisibilityProbe'}
 if($BufferedDiagnostics){$arguments+=('-U01FPerfFile="'+(Join-Path $user 'Frames.jsonl')+'"')}
 $cap=if($role -eq 'Server'){30}else{$ClientMaxFPS}
 $commands='t.MaxFPS '+$cap+',t.IdleWhenNotForeground 0'
 if($role -ne 'Server'){
  if($Diagnostics -or $BufferedDiagnostics){$commands+=',stat unit'}
  $commands+=',r.ScreenPercentage '+$(if($MemoryBudget){50}else{100})
 }
 if($MemoryBudget -and $role -ne 'Server'){
  # Explicit same-machine review profile; retain DX12/SM6 and window size,
  # network frequency and CMC smoothing. Do not persist project/user settings.
  $commands+=',r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.ScreenPercentage 50'
  Write-Host 'Local 4GB review profile: Lumen atlas 2048, RT pool minimum 128 MiB, texture pool 256 MiB, internal resolution 50%.'
 }
 if($MemoryBudget -and $role -ne 'Server'){
  # Focus regression: measured headroom for both simultaneous review clients.
  # No frame cap, input delay, networking, smoothing or gameplay changes.
  $commands+=',r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'
  Write-Host 'Focus review: simplified lighting/reflections/shadows for two clients; cap and networking unchanged.'
 }
 $arguments+='-U04AReadOnlyFrames'
 $arguments+=@(('-ExecCmds="'+$commands+'"'),'-NoLiveCoding','-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False','-nop4','-nosplash','-U01FProbe','-U01Trace','-U02FProbe','-U02Trace','-ModelContextProtocolStartServer',('-U02SourceSHA='+$sha),('-U02RunId='+(Split-Path $run -Leaf)),('-U02FCommands="'+(Join-Path $run 'command.txt')+'"'),('-U01SourceSHA='+$sha),('-UserDir="'+$settingsRoot+'"'),('-abslog="'+$log+'"'),('-ModelContextProtocolPort='+($McpPort+$records.Count)))
 Write-Host ('Starting '+$role+'; log: '+$log)
 # Interactive review clients must be visible during loading, before readiness.
 # The dedicated background server continues to run hidden.
 $windowStyle=if($role -eq 'Server'){'Hidden'}else{'Normal'}
 $p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory (Split-Path $project) -WindowStyle $windowStyle -PassThru
 $r=[pscustomobject]@{role=$role;creationUTC=(Get-CimInstance Win32_Process -Filter ('ProcessId='+$p.Id)).CreationDate.ToUniversalTime().ToString('o');pid=$p.Id;project=$project;executable=$exe;arguments=$arguments;sourceSHA=$sha;moduleSHA256=(Get-FileHash (Join-Path (Split-Path $project) 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')).Hash;binarySHA256=(Get-FileHash $exe).Hash;userDir=$settingsRoot;log=$log;utc=[DateTime]::UtcNow.ToString('o');requestedMaxFPS=$cap;clientCount=$ClientCount;windowSize=$(if($role -ne 'Server'){@(900,540)});internalResolutionPercent=$(if($role -ne 'Server'){if($MemoryBudget){50}else{100}});memoryProfile=($MemoryBudget.IsPresent -and $role -ne 'Server');bufferedDiagnostics=$BufferedDiagnostics.IsPresent}
 $r | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $user 'process.json')
 $records+=$r;$records | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $run 'processes.json')
 if($role -eq 'Server'){Set-FServerTimer $r | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $run 'server-timer.json')}
 if($role -eq 'Server'){
  $ready=$false
  for($i=0;$i -lt 400;$i++){if($p.HasExited){throw ('Server exited ('+$p.ExitCode+'); log: '+$log)};if((Test-Path $log) -and (Select-String -LiteralPath $log -Pattern ('IpNetDriver.*listening on port '+$Port) -Quiet)){$ready=$true;break};Start-Sleep -Milliseconds 500}
  if(!$ready){throw ('Server not ready; inspect own PID '+$p.Id+' log '+$log)}
 }else{
  $ready=$false
  for($i=0;$i -lt 400;$i++){if($p.HasExited){throw ('Client exited ('+$p.ExitCode+'); log: '+$log)};if((Test-Path $log) -and (Select-String -LiteralPath $log -Pattern 'U01F_NET.*"local":true' -Quiet)){$ready=$true;break};if($i%20 -eq 0){Write-Host ($role+' loading / connecting...')};Start-Sleep -Milliseconds 500}
  if(!$ready){throw ('Client not ready; inspect own PID '+$p.Id+' log '+$log)}
 }
 Write-Host ($role+' ready (PID '+$p.Id+')')
}
}catch{
 $failure=$_
 foreach($record in $records){
  $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
  if($live -and $live.Name -eq 'UnrealEditor.exe' -and $live.CommandLine.Contains($record.project) -and $live.CommandLine.Contains($record.userDir)){
   try{Stop-Process -Id $record.pid;Wait-Process -Id $record.pid -Timeout 10 -ErrorAction SilentlyContinue;Restore-U03DStableSdkLog $record}catch{Write-Warning ('Could not stop/restore own failed-start process '+$record.pid+': '+$_.Exception.Message)}
  }
 }
 throw $failure
}
Write-Output $run
