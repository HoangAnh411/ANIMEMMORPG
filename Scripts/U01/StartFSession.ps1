param(
 [Parameter(Mandatory=$true)][string]$CloneProject,
 [Parameter(Mandatory=$true)][string]$OutputRoot,
 [switch]$ReproducePython,
 [int]$Port=17877
)
$ErrorActionPreference='Stop'
$project=(Resolve-Path -LiteralPath $CloneProject).Path
if($project -notlike '*\Artifacts\U01\F\Source\*'){throw 'F clone required'}
$sha=git -C (Split-Path $project) rev-parse HEAD
$exe='D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$run=Join-Path $OutputRoot ($(if($ReproducePython){'PythonBefore-'}else{'Session-'})+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $run | Out-Null
$records=@()
foreach($role in @('Server','ClientA','ClientB')){
 $user=Join-Path $run $role;New-Item -ItemType Directory -Path $user | Out-Null
 $log=Join-Path $user ($role+'.log')
 $arguments=@(('"'+$project+'"'))
 if($role -eq 'Server'){$arguments+=@('/Game/AnimeMMORPG/Maps/L_NetworkLab','-server',('-port='+$Port),'-NullRHI','-nosound')}
 else{$arguments+=@(('127.0.0.1:'+$Port),'-game','-windowed','-ResX=900','-ResY=540',('-WinX='+$(if($role -eq 'ClientA'){0}else{940})),'-WinY=100')}
 if($ReproducePython){if($role -ne 'Server'){$arguments+='-NullRHI'}}else{$arguments+='-DisablePython'}
 $arguments+=@('-NoLiveCoding','-nop4','-nosplash','-U01FProbe','-U01Trace',('-U01SourceSHA='+$sha),('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'),('-ModelContextProtocolPort='+(18310+$records.Count)))
 $p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
 $r=[pscustomobject]@{role=$role;pid=$p.Id;project=$project;executable=$exe;arguments=$arguments;sourceSHA=$sha;userDir=$user;log=$log;utc=[DateTime]::UtcNow.ToString('o')}
 $r | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $user 'process.json')
 $records+=$r;$records | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $run 'processes.json')
 if($role -eq 'Server'){
  $ready=$false
  for($i=0;$i -lt 50;$i++){if((Test-Path $log) -and (Select-String -LiteralPath $log -Pattern 'listening on port' -Quiet)){$ready=$true;break};Start-Sleep -Milliseconds 500}
  if(!$ready){throw ('Server not ready; inspect own PID '+$p.Id+' log '+$log)}
 }else{Start-Sleep -Seconds 3}
}
Write-Output $run
