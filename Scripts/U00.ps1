param(
 [Parameter(Mandatory=$true)][ValidateSet('Build','Test','Package','Verify')][string]$Task,
 [Parameter(Mandatory=$true)][string]$ProjectPath,
 [Parameter(Mandatory=$true)][string]$EngineRoot,
 [Parameter(Mandatory=$true)][string]$OutputRoot
)
function Assert-EditorProjectSafe {
 param([string]$CommandLine,[int]$EditorPid,[string]$TargetProject)
 $unknown="Cannot identify project for Editor PID $EditorPid; inspect its project before building"
 if([string]::IsNullOrWhiteSpace($CommandLine)){throw $unknown}
 # Accept only balanced, plainly quoted Windows arguments; ambiguous input fails closed.
 if(([regex]::Matches($CommandLine,'"').Count % 2) -ne 0){throw $unknown}
 $tokens=@([regex]::Matches($CommandLine,'(?:[^\s"]+|"[^"]*")+') | ForEach-Object {$_.Value.Replace('"','')})
 if($tokens.Count -lt 2){throw $unknown}
 $candidates=@()
 for($i=1;$i -lt $tokens.Count;$i++){
  $token=$tokens[$i]
  if($token -match '^(?i)-project=(.*)$'){$candidates+= $Matches[1]}
  elseif($token -ieq '-project'){
   if($i+1 -ge $tokens.Count){throw $unknown}
   $i++; $candidates+=$tokens[$i]
  }
  elseif($i -eq 1 -and !$token.StartsWith('-')){$candidates+=$token}
 }
 if($candidates.Count -ne 1){throw $unknown}
 $candidate=$candidates[0].Replace('/','\')
 # Drive-relative, root-relative and project-name arguments are not proof of another project.
 if($candidate -notmatch '^(?:[A-Za-z]:\\|\\\\[^\\]+\\[^\\]+\\)' -or [IO.Path]::GetExtension($candidate) -ine '.uproject'){throw $unknown}
 if(!(Test-Path -LiteralPath $candidate -PathType Leaf)){throw $unknown}
 $identified=(Resolve-Path -LiteralPath $candidate).ProviderPath
 $target=(Resolve-Path -LiteralPath $TargetProject).ProviderPath
 if([string]::Equals($identified,$target,[StringComparison]::OrdinalIgnoreCase)){
  throw "Save and close Editor PID $EditorPid for this project before full build"
 }
}
function Assert-U00AutomationReport {
 param([string]$ReportPath,[string]$LogPath)
 $result=Get-Content -Raw -LiteralPath $ReportPath | ConvertFrom-Json
 $tests=@($result.tests | Where-Object {$null -ne $_})
 if($tests.Count -eq 0){throw 'Zero Automation tests executed'}
 $expected=@('Units','Axes','HalfOpenInterval','CallOrder') | ForEach-Object {'AnimeMMORPG.U00.Foundation.'+$_}
 $actual=@($tests | ForEach-Object {$_.fullTestPath})
 if(@(Compare-Object $expected $actual).Count -ne 0){throw 'Expected U00 test set missing or unexpected'}
 foreach($test in $tests){if($test.state -cne 'Success'){throw 'Failed or incomplete Automation test'}}
 foreach($field in @('failed','notRun','inProcess')){if($null -eq $result.$field -or $result.$field -ne 0){throw 'Incomplete or failed Automation summary'}}
 if(($result.succeeded+$result.succeededWithWarnings) -ne $tests.Count){throw 'Inconsistent Automation success count'}
 $text=Get-Content -Raw -LiteralPath $LogPath
 if($text -notmatch 'Automation Test Queue Empty\s+([1-9][0-9]*) tests performed' -or [int]$Matches[1] -ne $tests.Count){throw 'Missing or inconsistent test queue completion'}
 return $tests.Count
}
$ErrorActionPreference='Stop'
try {
 foreach($path in @($ProjectPath,$EngineRoot,$OutputRoot)){if(![IO.Path]::IsPathRooted($path)){throw 'All paths must be absolute'}}
 $ProjectPath=(Resolve-Path -LiteralPath $ProjectPath).Path
 $EngineRoot=(Resolve-Path -LiteralPath $EngineRoot).Path
 $build=Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat'
 $version=Get-Content -Raw (Join-Path $EngineRoot 'Engine/Build/Build.version') | ConvertFrom-Json
 if($version.MajorVersion -ne 5 -or $version.MinorVersion -ne 8 -or $version.PatchVersion -ne 4 -or $version.Changelist -ne 58902052){throw 'Engine must be UE 5.8.4 CL 58902052'}
 if(!(Test-Path -LiteralPath $build)){throw 'Build.bat missing'}
 if($Task -eq 'Verify'){
  $run=Join-Path $OutputRoot ('Verify-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Path $run | Out-Null
  foreach($childTask in @('Build','Test','Package')){
   $childArgs=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath,'-Task',$childTask,'-ProjectPath',$ProjectPath,'-EngineRoot',$EngineRoot,'-OutputRoot',$run)
   @{StartedAt=(Get-Date -Format o);Executable='powershell.exe';Arguments=$childArgs} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $run ($childTask+'.command.json'))
   $ErrorActionPreference='Continue'
   & powershell.exe @childArgs 2>&1 | ForEach-Object {"$_"} | Tee-Object (Join-Path $run ($childTask+'.log'))
   $code=$LASTEXITCODE
   $ErrorActionPreference='Stop'
   @{CompletedAt=(Get-Date -Format o);ExitCode=$code} | ConvertTo-Json | Set-Content (Join-Path $run ($childTask+'.result.json'))
   if($code -ne 0){exit $code}
  }
  Write-Output "Verify succeeded: $run"
  exit 0
 }
 if($Task -eq 'Package'){
  $run=Join-Path $OutputRoot ('Package-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Path $run | Out-Null
  foreach($editor in @(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'")){
   Assert-EditorProjectSafe -CommandLine $editor.CommandLine -EditorPid $editor.ProcessId -TargetProject $ProjectPath
  }
  $uat=Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat'
  if(!(Test-Path -LiteralPath $uat)){throw 'RunUAT.bat missing'}
  $config=Get-Content -Raw -LiteralPath (Join-Path (Split-Path $ProjectPath) 'Config/DefaultGame.ini')
  $maps=@([regex]::Matches($config,'(?m)^\+MapsToCook=\(FilePath="([^"]+)"\)') | ForEach-Object {$_.Groups[1].Value})
  $expected=@('/Game/AnimeMMORPG/Maps/L_Boot','/Game/AnimeMMORPG/Maps/L_CharacterCombatLab','/Game/AnimeMMORPG/Maps/L_NetworkLab')
  if(@(Compare-Object $expected $maps).Count -ne 0 -or $maps.Count -ne 3){throw 'Cook map configuration must contain exactly the three U00 maps'}
  $archive=Join-Path $run 'Archive'
  $uatArgs=@('BuildCookRun',"-project=$ProjectPath",'-noP4','-platform=Win64','-clientconfig=Development','-build','-cook','-stage','-pak','-archive',"-archivedirectory=$archive",('-map='+($maps -join '+')),'-unattended','-utf8output','-nocompileeditor')
  @{StartedAt=(Get-Date -Format o);Executable=$uat;Arguments=$uatArgs;Project=$ProjectPath;Engine=$version} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $run 'Package.command.json')
  $ErrorActionPreference='Continue'
  & $uat @uatArgs 2>&1 | ForEach-Object {"$_"} | Tee-Object (Join-Path $run 'Package.log')
  $code=$LASTEXITCODE
  $ErrorActionPreference='Stop'
  @{CompletedAt=(Get-Date -Format o);ExitCode=$code;Archive=$archive} | ConvertTo-Json | Set-Content (Join-Path $run 'Package.result.json')
  if($code -ne 0){exit $code}
  Write-Output "Package succeeded: $archive"
  exit 0
 }
 if($Task -eq 'Test'){
  $run=Join-Path $OutputRoot ('Test-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Path $run | Out-Null
  $exe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
  if(!(Test-Path -LiteralPath $exe)){throw 'UnrealEditor-Cmd.exe missing'}
  $report=Join-Path $run 'Report'
  $log=Join-Path $run 'Automation.log'
  $arguments=@(('"'+$ProjectPath+'"'),'-unattended','-nop4','-nosplash','-ModelContextProtocolPort=18001','-NullRHI','-nosound','-ExecCmds="Automation RunTests AnimeMMORPG.U00"','-TestExit="Automation Test Queue Empty"',('-ReportExportPath="'+$report+'"'),('-abslog="'+$log+'"'))
  @{StartedAt=(Get-Date -Format o);Executable=$exe;Arguments=$arguments;Project=$ProjectPath} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $run 'Test.command.json')
  $process=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
  if(!$process.WaitForExit(600000)){throw "Automation timed out; process PID $($process.Id) left running for inspection"}
  $process.Refresh()
  if($process.ExitCode -ne 0){throw "Automation process exit code $($process.ExitCode)"}
  $index=Join-Path $report 'index.json'
  if(!(Test-Path -LiteralPath $index)){throw 'Automation report missing; no success inferred from process exit'}
  $count=Assert-U00AutomationReport -ReportPath $index -LogPath $log
  @{CompletedAt=(Get-Date -Format o);ExitCode=0;Executed=$count;Report=$index} | ConvertTo-Json | Set-Content (Join-Path $run 'Test.result.json')
  Write-Output "PASS: $count completed tests; evidence: $run"
  exit 0
 }
 $editors=@(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe'")
 foreach($editor in $editors){
  Assert-EditorProjectSafe -CommandLine $editor.CommandLine -EditorPid $editor.ProcessId -TargetProject $ProjectPath
 }
 $run=Join-Path $OutputRoot ('Build-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
 New-Item -ItemType Directory -Path $run | Out-Null
 $steps=@(@{Name='Generate';Args=@('-projectfiles',"-project=$ProjectPath",'-game','-rocket')},@{Name='Editor';Args=@('AnimeMMORPGEditor','Win64','Development',"-Project=$ProjectPath",'-WaitMutex','-NoHotReloadFromIDE')},@{Name='Game';Args=@('AnimeMMORPG','Win64','Development',"-Project=$ProjectPath",'-WaitMutex','-NoHotReloadFromIDE')})
 foreach($step in $steps){
  $log=Join-Path $run ($step.Name+'.log')
  $argsForBuild=$step.Args
  @{StartedAt=(Get-Date -Format o);Executable=$build;Arguments=$argsForBuild;Project=$ProjectPath;Engine=$version} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $run ($step.Name+'.command.json'))
  $ErrorActionPreference='Continue'
  & $build @argsForBuild 2>&1 | ForEach-Object {"$_"} | Tee-Object -FilePath $log
  $code=$LASTEXITCODE
  $ErrorActionPreference='Stop'
  @{CompletedAt=(Get-Date -Format o);ExitCode=$code} | ConvertTo-Json | Set-Content (Join-Path $run ($step.Name+'.result.json'))
  if($code -ne 0){exit $code}
 }
 Write-Output "Evidence: $run"
 exit 0
} catch {if($run -and (Test-Path -LiteralPath $run)){@{FailedAt=(Get-Date -Format o);ErrorType=$_.Exception.GetType().FullName;Message=$_.Exception.Message;ExitCode=1} | ConvertTo-Json | Set-Content (Join-Path $run 'failure.json')}; [Console]::Error.WriteLine($_.Exception.Message); exit 1}
