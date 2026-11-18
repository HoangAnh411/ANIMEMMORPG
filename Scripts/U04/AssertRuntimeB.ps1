function Assert-BRuntime([string]$Clone,[string]$SourceSHA){
 if($SourceSHA -notmatch '^[0-9a-f]{40}$'){throw 'Full source SHA required'}
 $resolved=& git -C $Clone rev-parse --verify ($SourceSHA+'^{commit}') 2>$null
 if($LASTEXITCODE -ne 0 -or $resolved -ne $SourceSHA){throw 'Unknown source commit'}
 & git -C $Clone diff --quiet $SourceSHA -- Source Content Config Plugins AnimeMMORPG.uproject
 if($LASTEXITCODE -ne 0){throw 'Runtime source differs from build'}
 $status=@(& git -C $Clone status --porcelain --untracked-files=all -- Source Content Config Plugins AnimeMMORPG.uproject)
 if($LASTEXITCODE -ne 0 -or $status.Count){throw 'Dirty or untracked runtime inputs'}
}
