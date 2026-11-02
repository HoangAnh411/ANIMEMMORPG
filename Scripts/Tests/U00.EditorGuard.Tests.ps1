$ErrorActionPreference='Stop'
$scriptPath=Join-Path $PSScriptRoot '../U00.ps1'
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($scriptPath,[ref]$null,[ref]$parseErrors)
if($parseErrors){throw $parseErrors}
$guard=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-EditorProjectSafe'},$true)
. ([scriptblock]::Create($guard.Extent.Text))
$testRoot=Join-Path ([IO.Path]::GetTempPath()) ('U00Guard-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$target=Join-Path $testRoot 'Same Project.uproject'
$other=Join-Path $testRoot 'Other Project.uproject'
Set-Content -LiteralPath $target -Value '{}'
Set-Content -LiteralPath $other -Value '{}'
$cases=@(
 @{Name='same absolute with spaces';Command='"Editor.exe" "'+$target+'"';Expected='Save and close'},
 @{Name='different absolute project';Command='"Editor.exe" "'+$other+'"';Expected='ALLOW'},
 @{Name='empty';Command='';Expected='Cannot identify project'},
 @{Name='relative path';Command='Editor.exe ".\Same Project.uproject"';Expected='Cannot identify project'},
 @{Name='project name';Command='Editor.exe AnimeMMORPG';Expected='Cannot identify project'},
 @{Name='explicit same project';Command='Editor.exe -project="'+$target+'"';Expected='Save and close'},
 @{Name='missing absolute file';Command='Editor.exe "'+(Join-Path $testRoot 'Missing.uproject')+'"';Expected='Cannot identify project'},
 @{Name='no project';Command='Editor.exe -log';Expected='Cannot identify project'}
)
foreach($case in $cases){
 $actual='ALLOW'
 try {Assert-EditorProjectSafe -CommandLine $case.Command -EditorPid 4321 -TargetProject $target}
 catch {$actual=$_.Exception.Message}
 if($case.Expected -eq 'ALLOW'){if($actual -ne 'ALLOW'){throw "FAIL $($case.Name): $actual"}}
 elseif(!$actual.StartsWith($case.Expected) -or $actual -notmatch '4321'){throw "FAIL $($case.Name): $actual"}
 Write-Output "PASS $($case.Name)"
}
Write-Output '8 guard cases passed; no build or process shutdown performed'
