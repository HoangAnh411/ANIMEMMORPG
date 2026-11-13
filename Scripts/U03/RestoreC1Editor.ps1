param([Parameter(Mandatory=$true)][string]$Session)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$path=(Resolve-Path -LiteralPath $Session).Path
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'Artifacts/U03/C1/'))
if(!$path.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Only C1 placement records'}
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
$expected=Get-Content -Raw -Encoding UTF8 (Join-Path $path 'original-editor-windows.json') | ConvertFrom-Json
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
throw 'Original Editor placement did not settle; inspect C1 session records'
