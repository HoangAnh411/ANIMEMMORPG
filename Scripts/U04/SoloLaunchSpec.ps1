function New-U04SoloLaunchSpec {
 param([string]$Package,[string]$Output,[string]$SourceSHA,[string]$RunId,[int]$FPS,[switch]$Fixture,[switch]$InputDiagnostic,[switch]$TimingDiagnostic)
 $cmds='t.MaxFPS '+$FPS+',t.IdleWhenNotForeground 0,r.VSync 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'
 $map='/Game/AnimeMMORPG/Maps/L_CharacterCombatLab'+$(if($Fixture){'?U03Regression=1'}else{''})
 $argv=@($map,'-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-NoLiveCoding','-U01Trace',('-U01SourceSHA='+$SourceSHA),('-U02SourceSHA='+$SourceSHA),('-U02RunId='+$RunId),('-UserDir='+(Join-Path $Output 'User')),('-abslog='+(Join-Path $Output 'Game.log')),('-ExecCmds='+$cmds))
 if($Fixture){$argv+=@('-U04BFPSFixture',('-U04BOutput='+(Join-Path $Output 'Raw')))}
 if($InputDiagnostic){$argv+='-U04BInputDiagnostic'}
 if($TimingDiagnostic){$argv+='-U04BDiagnosticTiming'}
 [pscustomobject]@{executable=(Join-Path $Package 'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe');workingDirectory=$Package;arguments=$argv;map=$map;settings=(Join-Path $Output 'User');observation=@('-U01Trace')}
}
