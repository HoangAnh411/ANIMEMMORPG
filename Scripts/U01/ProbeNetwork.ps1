param(
  [string]$EngineRoot='D:/Software/UE_5.8',
  [string]$ProjectPath='D:/Data/AnimeMMORPG/AnimeMMORPG.uproject',
  [int]$Port=17777
)
$ErrorActionPreference='Stop'
$project=(Resolve-Path -LiteralPath $ProjectPath).Path
$root=Split-Path -Parent $project
$out=Join-Path $root ('Artifacts/U01/A/Network-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $out | Out-Null
$exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
$started=@()
$records=@()
try {
  foreach($role in @('Server','ClientA','ClientB')) {
    $user=Join-Path $out $role
    New-Item -ItemType Directory -Path $user | Out-Null
    $log=Join-Path $user ($role+'.log')
    $args=@(('"'+$project+'"'))
    if($role -eq 'Server') {
      $args+=@('/Game/AnimeMMORPG/Maps/L_NetworkLab','-server',('-port='+$Port))
    } else {
      $args+=@(('127.0.0.1:'+$Port),'-game')
    }
    # NullRHI is a headless connection probe, never evidence of rendered UI/animation.
    $args+=@('-NullRHI','-nosound','-unattended','-nop4','-nosplash','-NoLiveCoding',
      ('-ModelContextProtocolPort='+(18110+$started.Count)),
      ('-UserDir="'+$user+'"'),('-abslog="'+$log+'"'),
      '-LogCmds="LogNet Verbose,LogSpawn Verbose"')
    $p=Start-Process -FilePath $exe -ArgumentList $args -PassThru -WindowStyle Hidden
    $started+=$p
    $records+= [pscustomobject]@{role=$role;pid=$p.Id;executable=$exe;arguments=$args;log=$log;userDir=$user;startedUtc=[DateTime]::UtcNow.ToString('o')}
    $records | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $out 'processes.json')
    Start-Sleep -Seconds 12
  }
  Start-Sleep -Seconds 15
  $records | ForEach-Object {
    $p=Get-Process -Id $_.pid -ErrorAction SilentlyContinue
    [pscustomobject]@{role=$_.role;pid=$_.pid;alive=($null -ne $p)}
  } | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $out 'alive.json')
} finally {
  # Only processes created in this invocation; never terminate the user's Editor.
  foreach($p in $started) {
    $p.Refresh()
    if(!$p.HasExited) { Stop-Process -Id $p.Id; $p.WaitForExit(10000) | Out-Null }
  }
  $records | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $out 'processes.json')
  Write-Output $out
}
