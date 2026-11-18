param([Parameter(Mandatory=$true)][string]$Session)
$ErrorActionPreference='Stop'
$readiness=Get-Content -Raw (Join-Path $Session 'READINESS.json') | ConvertFrom-Json
if(!$readiness.completed){throw 'Readiness required before minimizing original Editor'}
. (Join-Path $PSScriptRoot '../U01/FReviewHost.ps1')
. (Join-Path $PSScriptRoot '../U02/EnsureEditorMinimized.ps1')
$project=[IO.Path]::GetFullPath((Join-Path $env:U04B_WORKSPACE_ROOT 'AnimeMMORPG.uproject'))
$file=Join-Path $Session 'original-editor-windows.json'
if(Test-Path $file){Move-Item -LiteralPath $file -Destination (Join-Path $Session 'editor-before-loading.json')}
$windows=@(Suspend-FOriginalEditorWindows $project)
ConvertTo-Json -InputObject $windows -Depth 8 | Set-Content -Encoding UTF8 $file
ConvertTo-Json -InputObject @(Confirm-U02EditorMinimized $windows) -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $Session 'editor-minimized-verified.json')
