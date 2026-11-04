param(
 [Parameter(Mandatory=$true)][string]$CloneProject,
 [string]$EngineRoot='D:/Software/UE_5.8',
 [int]$Port=18013,
 [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference='Stop'
$project=(Resolve-Path -LiteralPath $CloneProject).Path
$original=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../AnimeMMORPG.uproject')).Path
if($project -ieq $original -or $project -notlike '*\Artifacts\*') { throw 'Requires isolated C build clone' }
$out=Join-Path $OutputRoot ('MCPTests-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $out | Out-Null
$sourceSHA=(& git -C (Split-Path $project) rev-parse HEAD)
$exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
$arguments=@(('"'+$project+'"'),'-NullRHI','-nosound','-unattended','-NoLiveCoding','-ModelContextProtocolStartServer',('-ModelContextProtocolPort='+$Port),('-U01SourceSHA='+$sourceSHA),('-abslog="'+(Join-Path $out 'Editor.log')+'"'))
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
@{pid=$p.Id;exe=$exe;arguments=$arguments;sourceSHA=$sourceSHA} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out 'process.json')
$uri='http://127.0.0.1:'+ $Port + '/mcp'
$script:requestId=0
$headers=@{Accept='application/json, text/event-stream'}
function Rpc([string]$method, $parameters) {
 $script:requestId++
 $body=@{jsonrpc='2.0';id=$script:requestId;method=$method;params=$parameters} | ConvertTo-Json -Depth 12
 $reply=Invoke-WebRequest -UseBasicParsing -Uri $uri -Method Post -ContentType application/json -Headers $headers -Body $body -TimeoutSec 30
 $data=$reply.Content | ConvertFrom-Json
 if($data.error) { throw ($data.error | ConvertTo-Json -Compress) }
 return @{response=$reply;data=$data.result}
}
function Tool([string]$toolset,[string]$name,$argsObject) {
 $r=Rpc 'tools/call' @{name='call_tool';arguments=@{toolset_name=$toolset;tool_name=$name;arguments=$argsObject}}
 if($r.data.isError) { throw ($r.data | ConvertTo-Json -Depth 10) }
 return $r.data
}
$ready=$false
for($i=0;$i -lt 40;$i++) {
 try {
  $r=Rpc 'initialize' @{protocolVersion='2025-11-25';capabilities=@{};clientInfo=@{name='U01-C-disk-tests';version='1'}}
  $headers['Mcp-Session-Id']=$r.response.Headers['Mcp-Session-Id'];$ready=$true;break
 } catch { Start-Sleep -Seconds 3 }
}
if(!$ready) { throw ('Clone MCP not ready; inspect only PID '+$p.Id) }
Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'run_automation_tests' @{filter='AnimeMMORPG'} |
 ConvertTo-Json -Depth 10 | Set-Content (Join-Path $out 'trigger.json')
$done=$false
for($i=0;$i -lt 60;$i++) {
 Start-Sleep -Seconds 3
 $logs=Tool 'EditorToolset.LogsToolset' 'GetLogEntries' @{category='';pattern='Test Completed|Automation Test Queue Empty|No automation tests matched|U01C_MEASURE|Error:';maxEntries=250}
 $logs | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $out 'mcp-results.json')
 $lines=($logs.content[0].text | ConvertFrom-Json).returnValue
 if(@($lines | Where-Object {$_ -match 'Automation Test Queue Empty'}).Count) { $done=$true;break }
}
try { Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'execute_console_command' @{command='QUIT_EDITOR'} | Out-Null } catch {}
$p.WaitForExit(15000) | Out-Null
$success=@($lines | Where-Object {$_ -match 'Test Completed. Result=\{Success\}'})
$expected=@('U00.Foundation.Axes','U00.Foundation.CallOrder','U00.Foundation.HalfOpenInterval','U00.Foundation.Units',
 'U01.B.CameraPolicy','U01.B.ReleaseGate','U01.C.JumpWindows','U01.C.FlatMovement','U01.C.JumpPhysics','U01.C.Terrain','U01.C.MotorLocks')
foreach($name in $expected){if(@($success | Where-Object {$_ -match [regex]::Escape('Path={AnimeMMORPG.'+$name+'}')}).Count -ne 1){throw ('Missing success '+$name+'; '+$out)}}
if(!$done -or $success.Count -ne 11 -or (($lines -join "`n") -notmatch '11 tests performed')){throw ('Incomplete tests: '+$out)}
Write-Output ('Eleven tests completed via clone MCP TestRunner: '+$out)
