$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
foreach($kind in @('Review','Solo')){
 $latest=Join-Path $root ('Artifacts/U03/C1/Latest'+$kind+'.txt')
 if(Test-Path -LiteralPath $latest){
  $session=(Get-Content -LiteralPath $latest -Raw -Encoding UTF8).Trim()
  $recordFile=if($kind -eq 'Solo'){Join-Path $session 'process.json'}elseif(Test-Path (Join-Path $session 'all-processes.json')){Join-Path $session 'all-processes.json'}else{Join-Path $session 'processes.json'}
  $records=Get-Content -Raw -Encoding UTF8 -LiteralPath $recordFile | ConvertFrom-Json
  $live=@(foreach($b2Record in $records){
   $b2Process=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$b2Record.pid)
   if($b2Process -and $b2Process.ExecutablePath -ieq $b2Record.executable -and $b2Process.CommandLine.Contains($b2Record.userDir) -and $b2Process.CommandLine.Contains('-U02SourceSHA='+$b2Record.sourceSHA)){$b2Record}
  })
  # A completed old solo review must not overwrite a later network placement restore.
  if(!$live.Count -and (Test-Path (Join-Path $session 'editor-restored-verified.json'))){continue}
  if($kind -eq 'Review'){& (Join-Path $PSScriptRoot 'StopC1Session.ps1') -SessionPath $session}
  else{& (Join-Path $PSScriptRoot 'StopC1Package.ps1') -Session $session}
 }
}
