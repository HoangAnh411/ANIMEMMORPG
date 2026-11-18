param([Parameter(Mandatory=$true)][string]$Session)
$ErrorActionPreference='Stop'
$root=(Resolve-Path $env:U04B_WORKSPACE_ROOT).Path
$path=(Resolve-Path -LiteralPath $Session).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U04/B/'))
if(!$path.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Only D placement records'}
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
$expected=Get-Content -Raw -Encoding UTF8 (Join-Path $path 'original-editor-windows.json') | ConvertFrom-Json
$valid=@();$stale=@()
foreach($record in $expected){
 $live=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$record.pid)
 [uint32]$owner=0;[FReviewHostNative]::GetWindowThreadProcessId([IntPtr][long]$record.hwnd,[ref]$owner) | Out-Null
 if($live -and $live.CommandLine.Replace('/','\').IndexOf($record.project.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -ge 0 -and $owner -eq $record.pid){$valid+=$record}else{$stale+=$record}
}
if($stale.Count){
 @{status='STALE_IDENTITY_SKIPPED';utc=[DateTime]::UtcNow.ToString('o');stale=$stale;current=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'));note='No placement from a closed or replaced process/window is applied to a new Editor identity.'} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $path 'editor-placement-stale.json')
 Write-Warning ('Skipped '+$stale.Count+' stale Editor window identities; current replacement windows were not modified.')
}
$expected=$valid
if(!$expected.Count -and $stale.Count){return}
for($attempt=0;$attempt -lt 4;$attempt++){
 Restore-FOriginalEditorWindows $expected
 Start-Sleep -Milliseconds 500
 $observed=@(Get-U02OriginalEditorWindows (Join-Path $root 'AnimeMMORPG.uproject'))
 $ok=$true
 foreach($before in $expected){
  $after=@($observed | Where-Object { $_.pid -eq $before.pid -and $_.hwnd -eq $before.hwnd })
  if($after.Count -ne 1){$ok=$false;continue}
  if($after[0].placement.Show -ne $before.placement.Show){$ok=$false}
  foreach($edge in @('Left','Top','Right','Bottom')){if($after[0].placement.Normal.$edge -ne $before.placement.Normal.$edge){$ok=$false}}
 }
 if($ok){ConvertTo-Json -InputObject $observed -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $path 'editor-restored-verified.json');return}
}
throw 'Original Editor placement did not settle; inspect D session records'
