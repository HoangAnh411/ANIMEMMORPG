param([Parameter(Mandatory=$true)][ValidateSet('off','block','unparryable','bypass','slow','stun','knockdown','launch','grab','multi')][string]$Label)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$session=(Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Artifacts/U03/B2/LatestReview.txt')).Trim()
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/B2/'))
if(!$session.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'B2 session required'}
$server=Get-Content -Raw -Encoding UTF8 (Join-Path $session 'processes.json') | ConvertFrom-Json | Where-Object role -eq Server
$live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$server.pid)
if(!$live -or $live.ExecutablePath -ine $server.executable -or !$live.CommandLine.Contains($server.project) -or !$live.CommandLine.Contains('-U02SourceSHA='+$server.sourceSHA) -or (Get-FileHash $server.executable).Hash -ine $server.binarySHA256){throw 'Server identity mismatch'}
([string][DateTime]::UtcNow.Ticks+' b2-'+$Label) | Set-Content -Encoding UTF8 (Join-Path $session 'command.txt')
Write-Host ('B2 enemy fixture: '+$Label+'; guard/X use real client input.')
