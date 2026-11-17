# Stable preferences are intentional; AutoSDKInfo is an Editor runtime log, not
# a preference. Archive the new log per session and restore any pre-existing one.
function Backup-U03DStableSdkLog([string]$SessionUser,[string]$SettingsRoot){
 $file=Join-Path $SettingsRoot 'Saved/Logs/AutoSDKInfo.json'
 if(Test-Path -LiteralPath $file){
  $backup=Join-Path $SessionUser 'AutoSDKInfo.before.json'
  Copy-Item -LiteralPath $file -Destination $backup
  @{userDir=[IO.Path]::GetFullPath($SettingsRoot);sha256=(Get-FileHash -LiteralPath $backup).Hash} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $SessionUser 'autosdk-preservation.json')
 }
}
function Restore-U03DStableSdkLog($Record){
 $sessionUser=Split-Path $Record.log
 $metaFile=Join-Path $sessionUser 'autosdk-preservation.json'
 if(!(Test-Path -LiteralPath $metaFile)){return}
 $meta=Get-Content -LiteralPath $metaFile -Raw -Encoding UTF8 | ConvertFrom-Json
 $allowed=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../Artifacts/U04/A/'))
 $userDir=[IO.Path]::GetFullPath($Record.userDir)
 if(!$userDir.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase) -or $userDir -ine $meta.userDir){throw 'SDK log restore user-directory identity mismatch'}
 $others=@(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'" | Where-Object {$_.CommandLine -and $_.CommandLine.Contains($userDir) -and (Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue)})
 if($others.Count){throw 'Refusing SDK log restore while its user directory is still in use'}
 $backup=Join-Path $sessionUser 'AutoSDKInfo.before.json'
 if((Get-FileHash -LiteralPath $backup).Hash -ine $meta.sha256){throw 'SDK log baseline hash mismatch'}
 $file=Join-Path $userDir 'Saved/Logs/AutoSDKInfo.json';$runtime=Join-Path $sessionUser 'AutoSDKInfo.runtime.json'
 if(Test-Path -LiteralPath (Join-Path $sessionUser 'autosdk-restored.json')){
  if((Get-FileHash -LiteralPath $file).Hash -ine $meta.sha256){throw 'Previously restored SDK log changed; refusing to overwrite an unrelated later run'}
  return
 }
 if(Test-Path -LiteralPath $file){Copy-Item -LiteralPath $file -Destination $runtime}
 Copy-Item -LiteralPath $backup -Destination $file
 if((Get-FileHash -LiteralPath $file).Hash -ine $meta.sha256){throw 'SDK log byte restoration failed'}
 @{restored=$true;sha256=$meta.sha256;runtimeLog=$runtime;userDir=$userDir} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $sessionUser 'autosdk-restored.json')
}
