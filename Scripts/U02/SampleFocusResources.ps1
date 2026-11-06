param([Parameter(Mandatory=$true)][string]$SessionPath)
$ErrorActionPreference='Stop'
$session=(Resolve-Path -LiteralPath $SessionPath).Path
$records=Get-Content -Raw -Encoding UTF8 (Join-Path $session 'processes.json') | ConvertFrom-Json
$ids=@($records | ForEach-Object {[int]$_.pid})
$editorFile=Join-Path $session 'original-editor-windows.json'
if(Test-Path $editorFile){$editorRecords=Get-Content -Raw -Encoding UTF8 $editorFile | ConvertFrom-Json;foreach($editor in $editorRecords){$ids+=[int]$editor.pid}}
$ids=@($ids | Select-Object -Unique)
$file=Join-Path $session 'resources.jsonl'
while(!(Test-Path (Join-Path $session 'stop-resources'))){
 $utc=[DateTime]::UtcNow.ToString('o')
 $counters=Get-Counter '\GPU Process Memory(*)\Dedicated Usage','\GPU Process Memory(*)\Shared Usage','\GPU Engine(*)\Utilization Percentage' -ErrorAction SilentlyContinue
 $samples=@($counters.CounterSamples | Where-Object {$match=[regex]::Match($_.InstanceName,'pid_(\d+)_');$match.Success -and $ids.Contains([int]$match.Groups[1].Value)} | ForEach-Object {@{instance=$_.InstanceName;path=$_.Path;value=$_.CookedValue}})
 $gpu=& nvidia-smi --query-gpu=memory.total,memory.used,utilization.gpu,utilization.memory,power.draw,clocks.current.graphics --format=csv,noheader,nounits
 $processes=@(Get-Process -Id $ids -ErrorAction SilentlyContinue | Select-Object Id,CPU,WorkingSet64,PrivateMemorySize64)
 @{utc=$utc;gpuCsv=$gpu;counters=$samples;processes=$processes} | ConvertTo-Json -Compress -Depth 7 | Add-Content -Encoding UTF8 -LiteralPath $file
}
