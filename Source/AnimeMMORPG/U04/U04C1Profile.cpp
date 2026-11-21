#include "U04C1Profile.h"
#include "U01/U01Character.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02HurtboxComponent.h"
#include "U02/U02LabDummy.h"
#include "U02/U02VitalComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/App.h"
#include "GameFramework/WorldSettings.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "ProfilingDebugging/MiscTrace.h"
#include "ProfilingDebugging/CountersTrace.h"
#include "UnrealClient.h"

// Only setup can mutate fixture vital state; damage still takes the product path.
struct FU04C1Access
{
    static TSharedRef<FJsonObject> Registrations(UU02CollisionWorld* S)
    {
        auto J=MakeShared<FJsonObject>();TSet<AnimeMMORPG::U02::FLifeId> Subjects;int32 Boxes=0;
        for(const auto& R:S->Hurts)if(auto* H=R.Component.Get()){Subjects.Add(H->GetSubject());++Boxes;}
        J->SetNumberField(TEXT("registeredSubjects"),Subjects.Num());J->SetNumberField(TEXT("registeredHurtboxes"),Boxes);return J;
    }
    static void Prepare(UU02VitalComponent* V)
    {V->State.MaxHP=V->State.HP=1000000;V->State.Defense=0;V->State.Shields.Empty();V->Publish(V->GetWorld()->GetTimeSeconds());}
};
TRACE_DECLARE_INT_COUNTER(C1Visits,TEXT("U04C1/HurtboxVisits"));
TRACE_DECLARE_INT_COUNTER(C1Geometry,TEXT("U04C1/GeometryTests"));
TRACE_DECLARE_INT_COUNTER(C1Occlusion,TEXT("U04C1/OcclusionCalls"));
TRACE_DECLARE_INT_COUNTER(C1Candidates,TEXT("U04C1/Candidates"));
TRACE_DECLARE_INT_COUNTER(C1Hits,TEXT("U04C1/ConfirmedHits"));
TRACE_DECLARE_INT_COUNTER(C1Suppressed,TEXT("U04C1/DuplicateSuppression"));
TRACE_DECLARE_INT_COUNTER(C1Actions,TEXT("U04C1/Actions"));
namespace U04C1
{
namespace
{
struct FFrame {double Wall,World,Dt;uint64 Frame;FCounters Counts;bool Focus;};
struct FCapture
{
    FString Directory;FDelegateHandle Tick;
    TArray<TWeakObjectPtr<AU02LabDummy>> Targets;
    TArray<FFrame> Frames;TArray<TSharedPtr<FJsonValue>> Events;
    int32 Subjects=0,Boxes=0,DamageBegin=0;bool Inside=false,Closed=false;
    double Start=0,End=0,Duration=60;uint64 QueriesBegin=0;TSharedPtr<FJsonObject> RegistrationBegin;
};
TMap<UWorld*,TUniquePtr<FCapture>> Captures;
AU01Character* Player(UWorld* W)
{auto* PC=W->GetFirstPlayerController();return PC?Cast<AU01Character>(PC->GetPawn()):nullptr;}
TSharedRef<FJsonObject> Counts(const FCounters& C)
{
    auto J=MakeShared<FJsonObject>();
    J->SetNumberField(TEXT("hurtboxVisits"),C.Visits);J->SetNumberField(TEXT("geometryTests"),C.Geometry);
    J->SetNumberField(TEXT("occlusionCalls"),C.Occlusion);J->SetNumberField(TEXT("candidates"),C.Candidates);
    J->SetNumberField(TEXT("confirmedHits"),C.Confirmed);J->SetNumberField(TEXT("duplicateSuppression"),C.Suppressed);
    J->SetNumberField(TEXT("collectIntervals"),C.Intervals);J->SetNumberField(TEXT("actions"),C.Actions);return J;
}
void Command(const TArray<FString>& A,UWorld* W);
void Sample(UWorld* W,ELevelTick Type,float Dt)
{
    auto* F=Captures.Find(W);if(!F||Type==LEVELTICK_ViewportsOnly)return;
    auto* S=W->GetSubsystem<UU02CollisionWorld>();if(!S||!S->C1Profile.Active)return;
    (*F)->Frames.Add({FPlatformTime::Seconds(),W->GetTimeSeconds(),Dt,GFrameCounter,S->C1Profile,FApp::HasFocus()});
    TRACE_COUNTER_SET(C1Visits,S->C1Profile.Visits);TRACE_COUNTER_SET(C1Geometry,S->C1Profile.Geometry);
    TRACE_COUNTER_SET(C1Occlusion,S->C1Profile.Occlusion);TRACE_COUNTER_SET(C1Candidates,S->C1Profile.Candidates);
    TRACE_COUNTER_SET(C1Hits,S->C1Profile.Confirmed);TRACE_COUNTER_SET(C1Suppressed,S->C1Profile.Suppressed);TRACE_COUNTER_SET(C1Actions,S->C1Profile.Actions);
    if(FPlatformTime::Seconds()>=(*F)->Start+(*F)->Duration)Command({TEXT("end")},W);
}
void Command(const TArray<FString>& A,UWorld* W)
{
    auto* F=Captures.Find(W);if(!F||A.IsEmpty())return;auto& C=**F;
    auto* S=W->GetSubsystem<UU02CollisionWorld>();auto* P=Player(W);if(!S||!P)return;
    if(A[0]==TEXT("prepare")&&A.Num()==4&&!S->C1Profile.Active&&!C.Closed)
    {
        const int32 N=FCString::Atoi(*A[1]),H=FCString::Atoi(*A[2]);
        if((N!=1&&N!=10&&N!=40)||(H!=1&&H!=3)||(A[3]!=TEXT("in")&&A[3]!=TEXT("out")))return;
        // Remove ordinary lab dummies so registrations match the declared fixture.
        TArray<AU02LabDummy*> Old;for(TActorIterator<AU02LabDummy> I(W);I;++I)Old.Add(*I);for(auto* D:Old)D->Destroy();
        C.Targets.Empty();C.Subjects=N;C.Boxes=H;C.Inside=A[3]==TEXT("in");
        P->GetU01Movement()->ResetFixtureState();
        P->SetActorLocation(FVector(-10000,20000,100),false,nullptr,ETeleportType::TeleportPhysics);
        P->SetActorRotation(FRotator::ZeroRotator);P->GetController()->SetControlRotation(FRotator::ZeroRotator);
        S->SetLabCritRoll(.5);
        for(int32 I=0;I<N;++I)
        {
            // Every sphere is strictly inside the sword box (x 0..200,y +/-60,z 0..180).
            const FVector Pos(-10000+(C.Inside?70.:600.)+(I%8)*12.,20000+(I/8-2)*12.,0);
            FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            auto* D=W->SpawnActor<AU02LabDummy>(Pos,FRotator::ZeroRotator,Params);
            S->UnregisterHurtbox(D->Head);D->Head->DestroyComponent();
            D->Body->SetSphereRadius(4);D->Body->SetRelativeLocation(FVector(0,0,70));
            if(H==3)for(uint32 Id=2;Id<=3;++Id)
            {
                auto* B=NewObject<UU02HurtboxComponent>(D);D->AddInstanceComponent(B);B->SetupAttachment(D->GetRootComponent());
                B->StableHurtboxId=Id;B->InitSphereRadius(4);B->SetRelativeLocation(FVector(0,0,70+10*Id));
                B->SetFixtureSubject({D->NetworkPawnId,D->LifeGeneration});B->RegisterComponent();
            }
            FU04C1Access::Prepare(D->Vital);S->RebaseResetSubject(D);C.Targets.Add(D);
        }
        TRACE_BOOKMARK(TEXT("U04C1_WARMUP subjects=%d hurtboxes=%d placement=%s"),N,H,*A[3]);
    }
    if(A[0]==TEXT("begin")&&A.Num()==2&&!S->C1Profile.Active&&!C.Closed&&C.Subjects)
    {
        C.Duration=FCString::Atod(*A[1]);if(C.Duration<=0||C.Duration>60)return;
        C.Frames.Reserve(12000);C.Events.Reserve(512);C.DamageBegin=S->DamageResults.Num();C.QueriesBegin=S->Queries;C.RegistrationBegin=FU04C1Access::Registrations(S);
        S->C1Profile=FCounters{};S->C1Profile.Enabled=true;S->C1Profile.Active=true;C.Start=FPlatformTime::Seconds();
        TRACE_BOOKMARK(TEXT("U04C1_START"));TRACE_BEGIN_REGION(TEXT("U04C1_WINDOW"));
    }
    if(A[0]==TEXT("end")&&S->C1Profile.Active)
    {
        TRACE_END_REGION(TEXT("U04C1_WINDOW"));TRACE_BOOKMARK(TEXT("U04C1_END"));C.End=FPlatformTime::Seconds();S->C1Profile.Active=false;C.Closed=true;
        auto J=Counts(S->C1Profile);J->SetObjectField(TEXT("registrationBegin"),C.RegistrationBegin);J->SetObjectField(TEXT("registrationEnd"),FU04C1Access::Registrations(S));J->SetNumberField(TEXT("requestedSeconds"),C.Duration);J->SetNumberField(TEXT("startWall"),C.Start);J->SetNumberField(TEXT("endWall"),C.End);
        J->SetNumberField(TEXT("subjects"),C.Subjects);J->SetNumberField(TEXT("hurtboxesPerSubject"),C.Boxes);J->SetBoolField(TEXT("inside"),C.Inside);
        J->SetNumberField(TEXT("queriesPostContactDelta"),S->Queries-C.QueriesBegin);
        J->SetNumberField(TEXT("pid"),FPlatformProcess::GetCurrentProcessId());J->SetStringField(TEXT("world"),W->GetPathName());
        J->SetBoolField(TEXT("fixedTimeStep"),FApp::UseFixedTimeStep());J->SetBoolField(TEXT("fixedFrameRate"),GEngine->bUseFixedFrameRate);
        J->SetBoolField(TEXT("smoothing"),GEngine->bSmoothFrameRate);J->SetNumberField(TEXT("dilation"),W->GetWorldSettings()->GetEffectiveTimeDilation());
        auto CV=MakeShared<FJsonObject>();for(const auto* Name:{TEXT("t.MaxFPS"),TEXT("t.IdleWhenNotForeground"),TEXT("r.VSync"),TEXT("r.ScreenPercentage"),TEXT("r.LumenScene.SurfaceCache.AtlasSize"),TEXT("r.RenderTargetPoolMin"),TEXT("r.Streaming.PoolSize"),TEXT("r.Lumen.DiffuseIndirect.Allow"),TEXT("r.Lumen.Reflections.Allow"),TEXT("r.Shadow.Virtual.Enable"),TEXT("r.ShadowQuality")})
        {auto* V=IConsoleManager::Get().FindConsoleVariable(Name);CV->SetNumberField(Name,V?V->GetFloat():-999);}J->SetObjectField(TEXT("cvars"),CV);
        if(auto* V=W->GetGameViewport())if(V->Viewport){auto Size=V->Viewport->GetSizeXY();J->SetNumberField(TEXT("width"),Size.X);J->SetNumberField(TEXT("height"),Size.Y);}
        TArray<TSharedPtr<FJsonValue>> Targets;
        for(auto Weak:C.Targets)if(auto* D=Weak.Get())
        {
            auto T=D->Vital->GetDiagnostics();T->SetStringField(TEXT("subject"),D->NetworkPawnId.ToString());T->SetNumberField(TEXT("life"),D->LifeGeneration);
            TArray<UU02HurtboxComponent*> Boxes;D->GetComponents(Boxes);TArray<TSharedPtr<FJsonValue>> Ids;
            for(auto* B:Boxes)Ids.Add(MakeShared<FJsonValueNumber>(B->StableHurtboxId));T->SetArrayField(TEXT("stableHurtboxIds"),Ids);Targets.Add(MakeShared<FJsonValueObject>(T));
        }J->SetArrayField(TEXT("targets"),Targets);
        TArray<TSharedPtr<FJsonValue>> Hits;
        for(int32 I=C.DamageBegin;I<S->DamageResults.Num();++I)
        {
            const auto& R=S->DamageResults[I];auto H=MakeShared<FJsonObject>();
            H->SetStringField(TEXT("source"),R.Hit.Id.Action.Source.Pawn.ToString());H->SetNumberField(TEXT("sourceLife"),R.Hit.Id.Action.Source.Generation);
            H->SetStringField(TEXT("target"),R.Hit.Id.Target.Pawn.ToString());H->SetNumberField(TEXT("targetLife"),R.Hit.Id.Target.Generation);
            H->SetNumberField(TEXT("action"),R.Hit.Id.Action.Sequence);H->SetNumberField(TEXT("hurtboxId"),R.Hit.HurtboxId);H->SetNumberField(TEXT("at"),R.Hit.TimestampSeconds);
            H->SetNumberField(TEXT("damage"),R.Result.Damage);H->SetNumberField(TEXT("beforeHP"),R.Result.BeforeHP);H->SetNumberField(TEXT("afterHP"),R.Result.AfterHP);
            H->SetBoolField(TEXT("crit"),R.Result.bCrit);H->SetBoolField(TEXT("death"),R.Result.bDied);H->SetNumberField(TEXT("absorbed"),R.Result.Absorbed);Hits.Add(MakeShared<FJsonValueObject>(H));
        }J->SetArrayField(TEXT("damageEvents"),Hits);J->SetArrayField(TEXT("actionEvents"),C.Events);
        FString Text;FJsonSerializer::Serialize(J,TJsonWriterFactory<>::Create(&Text));
        const FString Result=C.Directory/TEXT("summary.json");if(!FPaths::FileExists(Result))FFileHelper::SaveStringToFile(Text,*Result,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
        TArray<FString> Lines;Lines.Add(TEXT("wall,world,dt,frame,focus,visits,geometry,occlusion,candidates,confirmed,suppressed,intervals,actions"));
        for(const auto& R:C.Frames)Lines.Add(FString::Printf(TEXT("%.17g,%.17g,%.17g,%llu,%d,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu"),R.Wall,R.World,R.Dt,R.Frame,R.Focus,R.Counts.Visits,R.Counts.Geometry,R.Counts.Occlusion,R.Counts.Candidates,R.Counts.Confirmed,R.Counts.Suppressed,R.Counts.Intervals,R.Counts.Actions));
        const FString Frames=C.Directory/TEXT("frames.csv");if(!FPaths::FileExists(Frames))FFileHelper::SaveStringArrayToFile(Lines,*Frames,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    }
}
FAutoConsoleCommandWithWorldAndArgs Control(TEXT("U04C1"),TEXT("Opt-in profiling: prepare N H in|out, begin, end. No synthetic gameplay."),FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&Command));
}
bool Enabled(const UWorld* W)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    return W&&W->WorldType==EWorldType::Game&&W->GetNetMode()==NM_Standalone&&W->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))&&FParse::Param(FCommandLine::Get(),TEXT("U04C1Profile"));
#endif
}
void BeginWorld(UWorld& W)
{
    if(!Enabled(&W))return;auto C=MakeUnique<FCapture>();
    if(!FParse::Value(FCommandLine::Get(),TEXT("U04C1Output="),C->Directory)||!FPaths::DirectoryExists(C->Directory))return;
    auto* Floor=W.SpawnActor<AStaticMeshActor>(FVector(0,20000,-50),FRotator::ZeroRotator);
    auto* Mesh=Floor->GetStaticMeshComponent();Mesh->SetMobility(EComponentMobility::Movable);Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Floor->SetActorScale3D(FVector(300,30,1));Mesh->SetCollisionProfileName(TEXT("BlockAll"));
    C->Tick=FWorldDelegates::OnWorldPostActorTick.AddStatic(&Sample);Captures.Add(&W,MoveTemp(C));
}
void EndWorld(UWorld* W)
{if(auto* F=Captures.Find(W)){FWorldDelegates::OnWorldPostActorTick.Remove((*F)->Tick);Captures.Remove(W);}}
void Event(UWorld* W,const TCHAR* Kind,TSharedRef<FJsonObject> J)
{
    auto* F=Captures.Find(W);if(!F)return;auto* S=W->GetSubsystem<UU02CollisionWorld>();if(!S||!S->C1Profile.Active)return;
    if(FCString::Strcmp(Kind,TEXT("ActionStarted"))==0)++S->C1Profile.Actions;
    J->SetStringField(TEXT("kind"),Kind);J->SetNumberField(TEXT("wall"),FPlatformTime::Seconds());(*F)->Events.Add(MakeShared<FJsonValueObject>(J));
}
}
