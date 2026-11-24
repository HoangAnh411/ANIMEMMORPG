param([string]$Package,[string]$Output,[string]$SourceSHA,[string]$RunId,[int]$FPS)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'SoloLaunchSpec.ps1')
New-U04SoloLaunchSpec -Package $Package -Output $Output -SourceSHA $SourceSHA -RunId $RunId -FPS $FPS | ConvertTo-Json -Depth 6 -Compress
