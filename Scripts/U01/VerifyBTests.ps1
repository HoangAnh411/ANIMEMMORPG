param(
 [Parameter(Mandatory=$true)][string]$CloneProject,
 [string]$EngineRoot='D:/Software/UE_5.8',
 [int]$Port=18012,
 [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference='Stop'
$project=(Resolve-Path -LiteralPath $CloneProject).Path
$original=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../AnimeMMORPG.uproject')).Path
if($project -ieq $original -or $project -notlike '*\Artifacts\*') { throw 'Requires isolated build clone, never the original Editor' }
$out=Join-Path $OutputRoot ('MCPTests-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $out | Out-Null
$exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
$args=@(('"'+$project+'"'),'-NullRHI','-nosound','-unattended','-NoLiveCoding','-ModelContextProtocolStartServer',('-ModelContextProtocolPort='+$Port),('-abslog="'+(Join-Path $out 'Editor.log')+'"'))
$p=Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden -PassThru
@{pid=$p.Id;exe=$exe;arguments=$args;sourceSHA=(& git -C (Split-Path $project) rev-parse HEAD)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out 'process.json')
$uri='http://127.0.0.1:'+ $Port + '/mcp'
$script:requestId=0
$headers=@{Accept='application/json, text/event-stream'}
function Rpc([string]$method, $parameters) {
 $script:requestId++
 $body=@{jsonrpc='2.0';id=$script:requestId;method=$method;params=$parameters} | ConvertTo-Json -Depth 12
 $reply=Invoke-WebRequest -UseBasicParsing -Uri $uri -Method Post -ContentType application/json -Headers $headers -Body $body -TimeoutSec 5
 $data=$reply.Content | ConvertFrom-Json
 if($data.error) { throw ($data.error | ConvertTo-Json -Compress) }
 return @{response=$reply;data=$data.result}
}
function Tool([string]$toolset, [string]$name, $arguments) {
 $r=Rpc 'tools/call' @{name='call_tool';arguments=@{toolset_name=$toolset;tool_name=$name;arguments=$arguments}}
 if($r.data.isError) { throw ($r.data | ConvertTo-Json -Depth 10) }
 return $r.data
}
$ready=$false
for($i=0;$i -lt 40;$i++) {
 try {
  $r=Rpc 'initialize' @{protocolVersion='2025-11-25';capabilities=@{};clientInfo=@{name='U01-B-disk-tests';version='1'}}
  $headers['Mcp-Session-Id']=$r.response.Headers['Mcp-Session-Id'];$ready=$true;break
 } catch { Start-Sleep -Seconds 3 }
}
if(!$ready) { throw ('Clone MCP not ready; inspect only PID '+$p.Id) }
$trigger=Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'run_automation_tests' @{filter='AnimeMMORPG'}
$trigger | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $out 'trigger.json')
$done=$false
for($i=0;$i -lt 40;$i++) {
 Start-Sleep -Seconds 3
 $logs=Tool 'EditorToolset.LogsToolset' 'GetLogEntries' @{category='';pattern='Test Completed|Automation Test Queue Empty|No automation tests matched';maxEntries=30}
 $logs | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $out 'mcp-results.json')
 $text=$logs | ConvertTo-Json -Depth 10
 if($text -match 'Automation Test Queue Empty') { $done=$true;break }
}
# Close only the dedicated verification Editor via its own MCP endpoint.
try { Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'execute_console_command' @{command='QUIT_EDITOR'} | Out-Null } catch {}
$p.WaitForExit(15000) | Out-Null
if(!$done -or $text -notmatch '6 tests performed' -or $text -match 'Result=\{Failed\}|No automation tests matched') { throw ('Tests incomplete/failed: '+$out) }
Write-Output ('Six tests completed via clone MCP TestRunner: '+$out)
