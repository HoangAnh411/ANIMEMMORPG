param([Parameter(Mandatory=$true)][string]$FinalSourceSHA,[Parameter(Mandatory=$true)][string]$Run,[int]$Port=19470)
$ErrorActionPreference='Stop'
if(Test-Path $Run){throw 'Immutable Live Coding run exists'}
New-Item -ItemType Directory -Path $Run | Out-Null
$clone=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../Artifacts/U04/A/Source'))
$project=Join-Path $clone 'AnimeMMORPG.uproject'
$exe='D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$argsA=@(('"'+$project+'"'),'-NullRHI','-nosound','-unattended',('-UserDir="'+(Join-Path $Run 'Settings')+'"'),'-ModelContextProtocolStartServer',('-ModelContextProtocolPort='+$Port),('-abslog="'+(Join-Path $Run 'Editor.log')+'"'),'-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False')
$p=Start-Process -FilePath $exe -ArgumentList $argsA -WindowStyle Hidden -PassThru
@{pid=$p.Id;executable=$exe;arguments=$argsA;initialSHA=(git -C $clone rev-parse HEAD);finalSHA=$FinalSourceSHA;utc=[DateTime]::UtcNow.ToString('o');scope='Required diagnostic Live Coding workflow only; never acceptance binary'} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Run 'process.json')
$uri='http://127.0.0.1:'+ $Port + '/mcp';$script:requestId=0;$headers=@{Accept='application/json, text/event-stream'}
function Rpc([string]$method,$parameters){
 $script:requestId++;$body=@{jsonrpc='2.0';id=$script:requestId;method=$method;params=$parameters}|ConvertTo-Json -Depth 15
 $reply=Invoke-WebRequest -UseBasicParsing -Uri $uri -Method Post -ContentType application/json -Headers $headers -Body $body -TimeoutSec 45
 $data=$reply.Content|ConvertFrom-Json;if($data.error){throw ($data.error|ConvertTo-Json -Compress)}
 return @{response=$reply;data=$data.result}
}
function Tool([string]$set,[string]$name,$argumentsA){$r=Rpc 'tools/call' @{name='call_tool';arguments=@{toolset_name=$set;tool_name=$name;arguments=$argumentsA}};if($r.data.isError){throw ($r.data|ConvertTo-Json -Depth 12)};return $r.data}
$ready=$false
for($i=0;$i -lt 60;$i++){try{$r=Rpc 'initialize' @{protocolVersion='2025-11-25';capabilities=@{};clientInfo=@{name='U04-A-LiveCoding';version='1'}};$headers['Mcp-Session-Id']=$r.response.Headers['Mcp-Session-Id'];$ready=$true;break}catch{Start-Sleep -Seconds 2}}
if(!$ready){throw 'Clone MCP not ready; owned PID retained'}
try{
 $r=Rpc 'tools/call' @{name='list_toolsets';arguments=@{}};$r.data|ConvertTo-Json -Depth 20|Set-Content (Join-Path $Run 'toolsets.json')
 foreach($set in @('EditorToolset.LogsToolset','test_runner.toolsets.test_runner.TestRunnerTools')){$r=Rpc 'tools/call' @{name='describe_toolset';arguments=@{toolset_name=$set}};$r.data|ConvertTo-Json -Depth 20|Set-Content (Join-Path $Run ($set.Split('.')[-1]+'.schema.json'))}
 Tool 'EditorToolset.LogsToolset' 'GetLogCategories' @{filter='LiveCoding'}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $Run 'categories.json')
 & python (Join-Path $PSScriptRoot 'PrepareA.py') --root $clone
 if($LASTEXITCODE -ne 0){throw 'Clone config normalization failed'}
 git -C $clone fetch origin u04/a-windows-regression *> (Join-Path $Run 'fetch.log')
 if($LASTEXITCODE -ne 0){throw 'Clone fetch failed'}
 git -C $clone checkout --detach $FinalSourceSHA *> (Join-Path $Run 'checkout.log')
 if($LASTEXITCODE -ne 0){throw 'Clone checkout failed'}
 Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'live_coding_compile' @{}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $Run 'trigger.json')
 for($i=0;$i -lt 60;$i++){
  Start-Sleep -Seconds 4
  $logs=Tool 'EditorToolset.LogsToolset' 'GetLogEntries' @{category='LogLiveCoding';pattern='Live coding succeeded|Failed to compile|Error:|succeeded|Live coding';maxEntries=100}
  $logs|ConvertTo-Json -Depth 15|Set-Content (Join-Path $Run ('poll-'+$i+'.json'))
  if(($logs|ConvertTo-Json -Depth 15) -match 'Live coding succeeded|Failed to compile'){break}
 }
}finally{try{Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'execute_console_command' @{command='QUIT_EDITOR'}|Out-Null}catch{};$p.WaitForExit(20000)|Out-Null}
Write-Output $Run
