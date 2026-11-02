$ErrorActionPreference='Stop'
$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../U00.ps1'),[ref]$null,[ref]$errors)
if($errors){throw $errors}
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-U00AutomationReport'},$true)
. ([scriptblock]::Create($fn.Extent.Text))
$root=Join-Path ([IO.Path]::GetTempPath()) ('U00Report-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $root | Out-Null
$report=Join-Path $root 'index.json'; $log=Join-Path $root 'Automation.log'
foreach($scenario in @('success','zero','failed','incomplete','missing-test','missing-completion','bad-summary')){
 $tests=@('Units','Axes','HalfOpenInterval','CallOrder') | ForEach-Object {@{fullTestPath='AnimeMMORPG.U00.Foundation.'+$_;state='Success'}}
 $data=@{tests=$tests;succeeded=4;succeededWithWarnings=0;failed=0;notRun=0;inProcess=0}
 $completion='Automation Test Queue Empty 4 tests performed.'
 switch($scenario){
  zero {$data.tests=@();$data.succeeded=0}
  failed {$data.tests[0].state='Fail';$data.failed=1;$data.succeeded=3}
  incomplete {$data.tests[0].state='InProcess';$data.inProcess=1;$data.succeeded=3}
  'missing-test' {$data.tests=@($data.tests | Select-Object -First 3);$data.succeeded=3}
  'missing-completion' {$completion='No completion marker'}
  'bad-summary' {$data.succeeded=3}
 }
 $data | ConvertTo-Json -Depth 5 | Set-Content $report
 Set-Content $log $completion
 $passed=$true
 try {$count=Assert-U00AutomationReport $report $log} catch {$passed=$false}
 if($passed -ne ($scenario -eq 'success')){throw "Unexpected validation outcome: $scenario"}
 Write-Output "PASS validator $scenario"
}
