function Assert-BIdentity([string]$Clone,[string]$SourceSHA,[string]$Manifest,[string]$Output,[string]$Settings){
 $root=[IO.Path]::GetFullPath((Join-Path $env:U04B_WORKSPACE_ROOT 'Artifacts/U04/B'))
 foreach($path in @($Clone,$Output,$Settings,$Manifest)){
  if(!$path -or ![IO.Path]::GetFullPath($path).StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'U04 path isolation required'}
 }
 if((git -C $Clone rev-parse HEAD) -ne $SourceSHA){throw 'Source mismatch'}
 if(@(git -C $Clone status --porcelain --untracked-files=no).Count){throw 'Clone dirty'}
 $m=Get-Content -Raw -Encoding UTF8 $Manifest | ConvertFrom-Json
 if($m.sourceSHA -ne $SourceSHA){throw 'Manifest source mismatch'}
 if((Get-FileHash (Join-Path $Clone 'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')).Hash -ine $m.moduleSHA256){throw 'Editor module hash mismatch'}
 if((Get-FileHash $m.engineExecutable).Hash -ine $m.engineSHA256){throw 'Engine hash mismatch'}
 return $m
}
