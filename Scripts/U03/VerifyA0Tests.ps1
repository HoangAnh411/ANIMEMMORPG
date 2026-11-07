param(
 [Parameter(Mandatory=$true)][string]$CloneProject,
 [string]$EngineRoot='D:/Software/UE_5.8',
 [int]$Port=18022,
 [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference='Stop'
$project=(Resolve-Path -LiteralPath $CloneProject).Path
$original=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../AnimeMMORPG.uproject')).Path
if($project -ieq $original -or $project -notlike '*\Artifacts\U03\A0\Source\*') { throw 'Requires isolated U03-A0 source clone' }
$sourceRoot=Split-Path $project
if(@(& git -C $sourceRoot status --porcelain --untracked-files=no).Count){throw 'Clone tracked tree must be clean'}
$out=Join-Path $OutputRoot ('MCPTests-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $out | Out-Null
$sourceSHA=(& git -C $sourceRoot rev-parse HEAD)
$exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
$module=Join-Path $sourceRoot 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'
if(!(Test-Path -LiteralPath $module)){throw 'Full build module missing'}
$expected=@([regex]::Matches(((Get-ChildItem (Join-Path $sourceRoot 'Source/AnimeMMORPG/Tests') -Filter *.cpp | ForEach-Object {Get-Content -Raw $_.FullName}) -join "`n"),'"(AnimeMMORPG\.[^"]+)"') | ForEach-Object {$_.Groups[1].Value})
if($expected.Count -eq 0){throw 'Zero registered A tests'}
$arguments=@(('"'+$project+'"'),'-NullRHI','-nosound','-unattended','-NoLiveCoding','-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False','-ModelContextProtocolStartServer',('-ModelContextProtocolPort='+$Port),('-abslog="'+(Join-Path $out 'Editor.log')+'"'))
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
@{runId=Split-Path $out -Leaf;utc=[DateTime]::UtcNow.ToString('o');pid=$p.Id;exe=$exe;arguments=$arguments;sourceSHA=$sourceSHA;exeSHA256=(Get-FileHash -LiteralPath $exe).Hash;module=$module;moduleSHA256=(Get-FileHash -LiteralPath $module).Hash;scope='pure model Automation; no gameplay pawn/world/net evidence'} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out 'process.json')
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
  $r=Rpc 'initialize' @{protocolVersion='2025-11-25';capabilities=@{};clientInfo=@{name='U03-A0-disk-tests';version='1'}}
  $headers['Mcp-Session-Id']=$r.response.Headers['Mcp-Session-Id'];$ready=$true;break
 } catch { Start-Sleep -Seconds 3 }
}
if(!$ready) { throw ('Clone MCP not ready; PID '+$p.Id+' left for inspection') }
# Discover schema on the actual clone, not merely the original Editor.
foreach($toolset in @('test_runner.toolsets.test_runner.TestRunnerTools','EditorToolset.LogsToolset')) {
 $r=Rpc 'tools/call' @{name='describe_toolset';arguments=@{toolset_name=$toolset}}
 $r.data | ConvertTo-Json -Depth 15 | Set-Content (Join-Path $out (($toolset.Split('.')[-1])+'.schema.json'))
}
Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'run_automation_tests' @{filter='AnimeMMORPG'} |
 ConvertTo-Json -Depth 10 | Set-Content (Join-Path $out 'trigger.json')
$done=$false
for($i=0;$i -lt 60;$i++) {
 Start-Sleep -Seconds 3
 $logs=Tool 'EditorToolset.LogsToolset' 'GetLogEntries' @{category='';pattern='Test Completed|Automation Test Queue Empty|No automation tests matched|U03A0_|Error:';maxEntries=500}
 $logs | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $out 'mcp-results.json')
 $lines=($logs.content[0].text | ConvertFrom-Json).returnValue
 if(@($lines | Where-Object {$_ -match 'Automation Test Queue Empty'}).Count) { $done=$true;break }
}
# Quit only this freshly started clone via its own MCP port; never the original.
try { Tool 'test_runner.toolsets.test_runner.TestRunnerTools' 'execute_console_command' @{command='QUIT_EDITOR'} | Out-Null } catch {}
$p.WaitForExit(15000) | Out-Null
$success=@($lines | Where-Object {$_ -match 'Test Completed. Result=\{Success\}'})
foreach($name in $expected){if(@($success | Where-Object {$_ -match [regex]::Escape('Path={'+$name+'}')}).Count -ne 1){throw ('Missing success '+$name+'; '+$out)}}
if(!$done -or $success.Count -ne $expected.Count -or (($lines -join "`n") -notmatch ([regex]::Escape([string]$expected.Count)+' tests performed'))){throw ('Incomplete tests: '+$out)}
@{sourceSHA=$sourceSHA;executed=$success.Count;failed=0;tests=$expected;method='MCP TestRunner trigger and GetLogEntries completion, cold full-build clone';utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'result.json')
Write-Output ('PASS '+$success.Count+' completed U03-A0 Automation tests: '+$out)
