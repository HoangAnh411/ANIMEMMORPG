#include "U04BFPSFixture.h"
#include "U01/U01Character.h"
#include "U01/U01PlayerController.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02LabDummy.h"
#include "U02/U02VitalComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/GameViewportClient.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/App.h"
#include "Misc/CoreDelegates.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "UnrealClient.h"

namespace U04B
{
namespace
{
struct FCapture
{
    TWeakObjectPtr<UWorld> World;
    TWeakObjectPtr<AU02LabDummy> Target;
    FDelegateHandle Tick, BeginFrame, WorldBegin;
    double FrameBeginWall=0, WorldBeginWall=0;
    uint64 FrameBeginCounter=0, WorldBeginCounter=0, EventSerial=0;
    TArray<TSharedRef<FJsonObject>> Buffer;
    FString Trial, Directory;
    bool Recording=false;
    uint64 Reset=0;
};
TMap<UWorld*,TUniquePtr<FCapture>> Captures;
void Vector(TSharedRef<FJsonObject> J,const TCHAR* Key,FVector V)
{TArray<TSharedPtr<FJsonValue>> A;for(double X:{V.X,V.Y,V.Z})A.Add(MakeShared<FJsonValueNumber>(X));J->SetArrayField(Key,A);}
AU01Character* Player(UWorld* W)
{for(TActorIterator<AU01Character> I(W);I;++I)if(I->IsLocallyControlled())return *I;return nullptr;}
TSharedRef<FJsonObject> Base(UWorld* W,const TCHAR* Kind)
{
    auto J=MakeShared<FJsonObject>();J->SetStringField(TEXT("kind"),Kind);
    J->SetNumberField(TEXT("wall"),FPlatformTime::Seconds());J->SetNumberField(TEXT("worldTime"),W->GetTimeSeconds());
    J->SetNumberField(TEXT("frame"),double(GFrameCounter));J->SetNumberField(TEXT("pid"),FPlatformProcess::GetCurrentProcessId());
    FString Source;FParse::Value(FCommandLine::Get(),TEXT("U02SourceSHA="),Source);J->SetStringField(TEXT("source"),Source);
    J->SetStringField(TEXT("world"),W->GetPathName());J->SetNumberField(TEXT("worldType"),int32(W->WorldType));
    J->SetNumberField(TEXT("netMode"),int32(W->GetNetMode()));return J;
}
void WorldBegin(UWorld* W,ELevelTick Type,float Dt)
{if(auto* C=Captures.Find(W))if(Enabled(W)){(*C)->WorldBeginWall=FPlatformTime::Seconds();(*C)->WorldBeginCounter=GFrameCounter;}}
void FrameBegin()
{const double At=FPlatformTime::Seconds();for(auto& Pair:Captures)if(Enabled(Pair.Key)){Pair.Value->FrameBeginWall=At;Pair.Value->FrameBeginCounter=GFrameCounter;}}
void Sample(UWorld* W,ELevelTick Type,float Dt)
{
    const double SampleEntry=FPlatformTime::Seconds();
    auto* F=Captures.Find(W);if(!F||!(*F)->Recording||Type==LEVELTICK_ViewportsOnly)return;
    auto& C=**F;auto J=Base(W,TEXT("frame"));
    // Primary cadence clock: captured once before collection. Event only stamps wall.
    J->SetNumberField(TEXT("sampleEntryWall"),SampleEntry);J->SetNumberField(TEXT("dt"),Dt);
    J->SetBoolField(TEXT("focus"),FApp::HasFocus());J->SetNumberField(TEXT("reset"),double(C.Reset));
    J->SetNumberField(TEXT("dilation"),W->GetWorldSettings()->GetEffectiveTimeDilation());
    J->SetBoolField(TEXT("fixed"),FApp::UseFixedTimeStep());J->SetNumberField(TEXT("fixedDelta"),FApp::GetFixedDeltaTime());
    J->SetBoolField(TEXT("smoothing"),GEngine->bSmoothFrameRate);J->SetBoolField(TEXT("useFixedFrameRate"),GEngine->bUseFixedFrameRate);
    J->SetNumberField(TEXT("fixedFrameRate"),GEngine->FixedFrameRate);
    auto CV=MakeShared<FJsonObject>();for(const auto* Name:{TEXT("t.MaxFPS"),TEXT("t.IdleWhenNotForeground"),TEXT("r.VSync"),TEXT("r.ScreenPercentage"),TEXT("r.LumenScene.SurfaceCache.AtlasSize"),TEXT("r.RenderTargetPoolMin"),TEXT("r.Streaming.PoolSize"),TEXT("r.Lumen.DiffuseIndirect.Allow"),TEXT("r.Lumen.Reflections.Allow"),TEXT("r.Shadow.Virtual.Enable"),TEXT("r.ShadowQuality")})
    {const auto* V=IConsoleManager::Get().FindConsoleVariable(Name);CV->SetNumberField(Name,V?V->GetFloat():-999);}J->SetObjectField(TEXT("cvars"),CV);
    if(const auto* V=W->GetGameViewport())if(V->Viewport){const auto S=V->Viewport->GetSizeXY();J->SetNumberField(TEXT("width"),S.X);J->SetNumberField(TEXT("height"),S.Y);}
    if(auto* P=Player(W))
    {
        J->SetStringField(TEXT("pawn"),P->NetworkPawnId.ToString());J->SetStringField(TEXT("pawnPath"),P->GetPathName());
        Vector(J,TEXT("position"),P->GetActorLocation());Vector(J,TEXT("velocity"),P->GetVelocity());
        J->SetNumberField(TEXT("mode"),int32(P->GetU01Movement()->MovementMode));J->SetObjectField(TEXT("combat"),P->Combat->GetDiagnostics());
        if(InputDiagnosticEnabled(W))if(auto* PC=Cast<AU01PlayerController>(P->GetController()))J->SetObjectField(TEXT("input"),PC->GetU04InputDiagnostic());
        J->SetBoolField(TEXT("local"),P->IsLocallyControlled());J->SetStringField(TEXT("controller"),GetPathNameSafe(P->GetController()));
    }
    if(C.Target.IsValid()){J->SetStringField(TEXT("target"),C.Target->NetworkPawnId.ToString());J->SetNumberField(TEXT("targetLife"),double(C.Target->LifeGeneration));J->SetObjectField(TEXT("targetVital"),C.Target->Vital->GetDiagnostics());}
    TArray<TSharedPtr<FJsonValue>> Hits;
    for(const auto& R:W->GetSubsystem<UU02CollisionWorld>()->DamageResults)
    {
        auto H=MakeShared<FJsonObject>();const auto& I=R.Hit.Id;
        H->SetStringField(TEXT("source"),I.Action.Source.Pawn.ToString());H->SetNumberField(TEXT("sourceLife"),double(I.Action.Source.Generation));H->SetNumberField(TEXT("action"),double(I.Action.Sequence));
        H->SetStringField(TEXT("target"),I.Target.Pawn.ToString());H->SetNumberField(TEXT("targetLife"),double(I.Target.Generation));H->SetNumberField(TEXT("time"),R.Hit.TimestampSeconds);
        H->SetNumberField(TEXT("damage"),R.Result.Damage);H->SetNumberField(TEXT("hpBefore"),R.Result.BeforeHP);H->SetNumberField(TEXT("hpAfter"),R.Result.AfterHP);
        H->SetBoolField(TEXT("crit"),R.Result.bCrit);H->SetNumberField(TEXT("absorbed"),R.Result.Absorbed);H->SetNumberField(TEXT("defense"),R.Result.Defense);H->SetNumberField(TEXT("roll"),R.Roll);
        Hits.Add(MakeShared<FJsonValueObject>(H));
    }J->SetArrayField(TEXT("hits"),Hits);
    if(Enabled(W)){J->SetNumberField(TEXT("worldBeginWall"),C.WorldBeginWall);J->SetNumberField(TEXT("worldBeginCounter"),double(C.WorldBeginCounter));J->SetNumberField(TEXT("frameBeginWall"),C.FrameBeginWall);J->SetNumberField(TEXT("frameBeginCounter"),double(C.FrameBeginCounter));}
    Event(W,TEXT("frame"),J);
    J->SetNumberField(TEXT("collectorExitWall"),FPlatformTime::Seconds());
}
void Command(const TArray<FString>& A,UWorld* W)
{
    if(!Enabled(W)||A.IsEmpty())return;auto* F=Captures.Find(W);if(!F)return;auto& C=**F;
    if(A[0]==TEXT("prepare"))
    {
        ++C.Reset;Event(W,TEXT("reset"),Base(W,TEXT("reset")));if(C.Recording)return;
        auto* P=Player(W);if(!P)return;P->GetU01Movement()->ResetFixtureState();
        P->SetActorLocation(FVector(-10000,20000,100),false,nullptr,ETeleportType::TeleportPhysics);P->SetActorRotation(FRotator::ZeroRotator);
        if(auto* PC=Cast<AU01PlayerController>(P->GetController()))PC->SetControlRotation(FRotator::ZeroRotator);
        if(C.Target.IsValid())C.Target->Destroy();C.Target.Reset();
        if(A.Num()>1&&A[1]==TEXT("combo"))C.Target=W->SpawnActor<AU02LabDummy>(FVector(-9880,20000,0),FRotator::ZeroRotator);
        W->GetSubsystem<UU02CollisionWorld>()->SetLabCritRoll(.5);
    }
    if(A[0]==TEXT("begin")&&A.Num()==2&&!C.Recording&&C.Buffer.IsEmpty())
    {if(A[1].Contains(TEXT("/"))||A[1].Contains(TEXT("\\"))||A[1].Contains(TEXT("..")))return;C.Trial=A[1];C.Recording=true;Event(W,TEXT("begin"),Base(W,TEXT("begin")));}
    if(A[0]==TEXT("end")&&C.Recording)
    {
        Event(W,TEXT("end"),Base(W,TEXT("end")));C.Recording=false;
        const FString Path=C.Directory/(C.Trial+TEXT(".jsonl"));if(FPaths::FileExists(Path))return;
        TArray<FString> Lines;for(const auto& J:C.Buffer){FString S;FJsonSerializer::Serialize(J,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&S));Lines.Add(MoveTemp(S));}
        if(FFileHelper::SaveStringArrayToFile(Lines,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))C.Buffer.Reset();
    }
}
FAutoConsoleCommandWithWorldAndArgs Control(TEXT("U04B"),TEXT("Opt-in FPS fixture prepare [combo], begin <trial>, end. Never invokes gameplay input."),FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&Command));
}
bool Enabled(const UWorld* W)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    return W&&W->WorldType==EWorldType::Game&&W->GetNetMode()==NM_Standalone&&W->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))&&FParse::Param(FCommandLine::Get(),TEXT("U04BFPSFixture"));
#endif
}
bool InputDiagnosticEnabled(const UWorld* W){return Enabled(W)&&FParse::Param(FCommandLine::Get(),TEXT("U04BInputDiagnostic"));}
bool TimingDiagnosticEnabled(const UWorld* W){return Enabled(W)&&FParse::Param(FCommandLine::Get(),TEXT("U04BDiagnosticTiming"));}
void Event(UWorld* W,const TCHAR* Kind,TSharedRef<FJsonObject> J)
{
    auto* F=Captures.Find(W);if(!F||!(*F)->Recording)return;auto& C=**F;
    J->SetNumberField(TEXT("wall"),FPlatformTime::Seconds());J->SetNumberField(TEXT("frame"),double(GFrameCounter));J->SetNumberField(TEXT("observedWorld"),W->GetTimeSeconds());
    if(InputDiagnosticEnabled(W))J->SetNumberField(TEXT("diagnosticSerial"),double(++C.EventSerial));
    J->SetStringField(TEXT("kind"),Kind);J->SetStringField(TEXT("trial"),C.Trial);C.Buffer.Add(J);
}
void BeginWorld(UWorld& W)
{
    if(!Enabled(&W))return;auto C=MakeUnique<FCapture>();C->World=&W;
    if(!FParse::Value(FCommandLine::Get(),TEXT("U04BOutput="),C->Directory)||!FPaths::DirectoryExists(C->Directory))return;
    auto* Floor=W.SpawnActor<AStaticMeshActor>(FVector(0,20000,-50),FRotator::ZeroRotator);
    auto* Mesh=Floor->GetStaticMeshComponent();Mesh->SetMobility(EComponentMobility::Movable);Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Floor->SetActorScale3D(FVector(300,30,1));Mesh->SetCollisionProfileName(TEXT("BlockAll"));
    if(Enabled(&W)){C->BeginFrame=FCoreDelegates::OnBeginFrame.AddStatic(&FrameBegin);C->WorldBegin=FWorldDelegates::OnWorldTickStart.AddStatic(&WorldBegin);}
    C->Tick=FWorldDelegates::OnWorldPostActorTick.AddStatic(&Sample);Captures.Add(&W,MoveTemp(C));
}
void EndWorld(UWorld* W)
{if(auto* F=Captures.Find(W)){FWorldDelegates::OnWorldPostActorTick.Remove((*F)->Tick);FCoreDelegates::OnBeginFrame.Remove((*F)->BeginFrame);FWorldDelegates::OnWorldTickStart.Remove((*F)->WorldBegin);Captures.Remove(W);}}
void DodgeCommit(AU01Character* P,double At,bool End)
{
    if(!P||!Enabled(P->GetWorld()))return;auto J=Base(P->GetWorld(),TEXT("dodgeCommit"));
    J->SetNumberField(TEXT("at"),At);J->SetBoolField(TEXT("trajectoryEnd"),End);Vector(J,TEXT("position"),P->GetActorLocation());J->SetObjectField(TEXT("combat"),P->Combat->GetDiagnostics());Event(P->GetWorld(),TEXT("dodgeCommit"),J);
}
}
