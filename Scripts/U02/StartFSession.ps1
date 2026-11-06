param(
 [Parameter(Mandatory=$true)][string]$CloneProject,
 [Parameter(Mandatory=$true)][string]$OutputRoot,
 [switch]$ReproducePython,
 [switch]$Diagnostics,
 [switch]$MemoryBudget,
 [ValidateSet(30,60)][int]$ClientMaxFPS=30,
 [ValidateSet(1,2)][int]$ClientCount=2,
 [switch]$BufferedDiagnostics,
 [int]$Port=17877,
 [ValidateSet('F')][string]$Stage='F'
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
$project=(Resolve-Path -LiteralPath $CloneProject).Path
if($project -notlike ("*\Artifacts\U02\"+$Stage+"\Source\*")){throw 'Isolated stage clone required'}
& python (Join-Path $PSScriptRoot 'PrepareFCloneConfig.py') --root (Split-Path $project)
if($LASTEXITCODE -ne 0){throw 'Clone config guard failed'}
if(@(git -C (Split-Path $project) status --porcelain --untracked-files=no).Count){throw 'Clone tracked tree is dirty'}
$sha=git -C (Split-Path $project) rev-parse HEAD
$exe='D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$run=Join-Path $OutputRoot ($(if($ReproducePython){'PythonBefore-'}else{'Session-'})+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$records=@()
try{
$roles=if($ClientCount -eq 1){@('Server','ClientA')}else{@('Server','ClientA','ClientB')}
foreach($role in $roles){
 $user=Join-Path $run $role;New-Item -ItemType Directory -Path $user | Out-Null
 $log=Join-Path $user ($role+'.log')
 $arguments=@(('"'+$project+'"'))
 if($role -eq 'Server'){$arguments+=@('/Game/AnimeMMORPG/Maps/L_NetworkLab','-server',('-port='+$Port),'-NullRHI','-nosound')}
 else{$arguments+=@(('127.0.0.1:'+$Port),'-game','-windowed','-ResX=900','-ResY=540',('-WinX='+$(if($role -eq 'ClientA'){0}else{940})),'-WinY=100')}
 if($ReproducePython){if($role -ne 'Server'){$arguments+='-NullRHI'}}else{$arguments+='-DisablePython'}
 if($Diagnostics){$arguments+='-U01FPerf'}
 if($BufferedDiagnostics){$arguments+=('-U01FPerfFile="'+(Join-Path $user 'Frames.jsonl')+'"')}
 $cap=if($role -eq 'Server'){30}else{$ClientMaxFPS}
 $commands='t.MaxFPS '+$cap+',t.IdleWhenNotForeground 0'
 if($role -ne 'Server'){
  if($Diagnostics -or $BufferedDiagnostics){$commands+=',stat unit'}
  $commands+=',r.ScreenPercentage '+$(if($MemoryBudget){50}else{100})
 }
 if($MemoryBudget -and $role -ne 'Server'){
  # Explicit same-machine review profile; retain DX12/SM6, Lumen, window size,
  # network frequency and CMC smoothing. Do not persist project/user settings.
  $commands+=',r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.ScreenPercentage 50'
  Write-Host 'Local 4GB review profile: Lumen atlas 2048, RT pool minimum 128 MiB, texture pool 256 MiB, internal resolution 50%.'
 }
 if($MemoryBudget -and $role -ne 'Server'){
  # Focus regression: measured headroom for both simultaneous review clients.
  # No frame cap, input delay, networking, smoothing or gameplay changes.
  $commands+=',r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'
 }
 $arguments+=@(('-ExecCmds="'+$commands+'"'),'-NoLiveCoding','-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False','-nop4','-nosplash','-U01FProbe','-U01Trace','-U02FProbe','-U02Trace','-ModelContextProtocolStartServer',('-U02SourceSHA='+$sha),('-U02RunId='+(Split-Path $run -Leaf)),('-U02FCommands="'+(Join-Path $run 'command.txt')+'"'),('-U01SourceSHA='+$sha),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'),('-ModelContextProtocolPort='+(18410+$records.Count)))
 Write-Host ('Starting '+$role+'; log: '+$log)
 # Interactive review clients must be visible during loading, before readiness.
 # The dedicated background server continues to run hidden.
 $windowStyle=if($role -eq 'Server'){'Hidden'}else{'Normal'}
 $p=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory (Split-Path $project) -WindowStyle $windowStyle -PassThru
 $r=[pscustomobject]@{role=$role;pid=$p.Id;project=$project;executable=$exe;arguments=$arguments;sourceSHA=$sha;moduleSHA256=(Get-FileHash (Join-Path (Split-Path $project) 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')).Hash;binarySHA256=(Get-FileHash $exe).Hash;userDir=$user;log=$log;utc=[DateTime]::UtcNow.ToString('o');requestedMaxFPS=$cap;clientCount=$ClientCount;windowSize=$(if($role -ne 'Server'){@(900,540)});internalResolutionPercent=$(if($role -ne 'Server'){if($MemoryBudget){50}else{100}});memoryProfile=($MemoryBudget.IsPresent -and $role -ne 'Server');bufferedDiagnostics=$BufferedDiagnostics.IsPresent}
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
   try{Stop-Process -Id $record.pid}catch{Write-Warning ('Could not stop own failed-start process '+$record.pid)}
  }
 }
 throw $failure
}
Write-Output $run
