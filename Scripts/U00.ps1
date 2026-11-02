param(
 [Parameter(Mandatory=$true)][ValidateSet('Build')][string]$Task,
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
$ErrorActionPreference='Stop'
try {
 foreach($path in @($ProjectPath,$EngineRoot,$OutputRoot)){if(![IO.Path]::IsPathRooted($path)){throw 'All paths must be absolute'}}
 $ProjectPath=(Resolve-Path -LiteralPath $ProjectPath).Path
 $EngineRoot=(Resolve-Path -LiteralPath $EngineRoot).Path
 $build=Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat'
 $version=Get-Content -Raw (Join-Path $EngineRoot 'Engine/Build/Build.version') | ConvertFrom-Json
 if($version.MajorVersion -ne 5 -or $version.MinorVersion -ne 8 -or $version.PatchVersion -ne 4 -or $version.Changelist -ne 58902052){throw 'Engine must be UE 5.8.4 CL 58902052'}
 if(!(Test-Path -LiteralPath $build)){throw 'Build.bat missing'}
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
  & $build @argsForBuild 2>&1 | ForEach-Object {"$_"} | Tee-Object -FilePath $log
  $code=$LASTEXITCODE
  @{CompletedAt=(Get-Date -Format o);ExitCode=$code} | ConvertTo-Json | Set-Content (Join-Path $run ($step.Name+'.result.json'))
  if($code -ne 0){exit $code}
 }
 Write-Output "Evidence: $run"
 exit 0
} catch {if($run -and (Test-Path -LiteralPath $run)){@{FailedAt=(Get-Date -Format o);ErrorType=$_.Exception.GetType().FullName;Message=$_.Exception.Message;ExitCode=1} | ConvertTo-Json | Set-Content (Join-Path $run 'failure.json')}; [Console]::Error.WriteLine($_.Exception.Message); exit 1}
