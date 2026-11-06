#include "U02NetworkState.h"
#include "U02CombatComponent.h"
#include "U02VitalComponent.h"
#include "U02LabDummy.h"
#include "U01/U01Character.h"
#include "U01/U01PlayerController.h"
#include "U01/U01AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/GameStateBase.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "HAL/IConsoleManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"
DEFINE_LOG_CATEGORY_STATIC(LogU02Network,Log,All);
using namespace AnimeMMORPG::U02;
namespace {
FString Json(TSharedRef<FJsonObject> J){FString S;FJsonSerializer::Serialize(J,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&S));return S;}
TSharedRef<FJsonObject> ResultJson(const FU02ConfirmedResult& R){auto J=MakeShared<FJsonObject>();J->SetNumberField(TEXT("serial"),R.Serial);J->SetStringField(TEXT("source"),R.Source.ToString());J->SetNumberField(TEXT("sourceLife"),R.SourceLife);J->SetNumberField(TEXT("action"),R.Action);J->SetStringField(TEXT("target"),R.Target.ToString());J->SetNumberField(TEXT("targetLife"),R.TargetLife);J->SetNumberField(TEXT("hurtbox"),R.Hurtbox);J->SetNumberField(TEXT("timestamp"),R.Timestamp);J->SetNumberField(TEXT("damage"),R.Damage);J->SetNumberField(TEXT("absorbed"),R.Absorbed);J->SetNumberField(TEXT("hp"),R.HP);J->SetBoolField(TEXT("crit"),R.Crit);J->SetBoolField(TEXT("death"),R.Death);return J;}
}
AU02NetworkState::AU02NetworkState(){bReplicates=true;bAlwaysRelevant=true;PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickGroup=TG_PostPhysics;}
void AU02NetworkState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(AU02NetworkState,Results);DOREPLIFETIME(AU02NetworkState,CritMode);}
void AU02NetworkState::Confirm(const UU02CollisionWorld::FConfirmedDamage& D)
{
    if(!HasAuthority())return;FU02ConfirmedResult R;R.Serial=++NextSerial;R.Source=D.Hit.Id.Action.Source.Pawn;R.SourceLife=D.Hit.Id.Action.Source.Generation;R.Action=D.Hit.Id.Action.Sequence;R.Target=D.Hit.Id.Target.Pawn;R.TargetLife=D.Hit.Id.Target.Generation;R.Hurtbox=D.Hit.HurtboxId;R.Timestamp=D.Hit.TimestampSeconds;R.Damage=D.Result.Damage;R.Absorbed=D.Result.Absorbed;R.HP=D.Result.AfterHP;R.Crit=D.Result.bCrit;R.Death=D.Result.bDied;Results.Add(R);if(Results.Num()>64)Results.RemoveAt(0,Results.Num()-64);ForceNetUpdate();OnRep_Results();
}
void AU02NetworkState::OnRep_Results()
{
    for(const auto& R:Results)if(R.Serial>LastSeenSerial){UE_LOG(LogU02Network,Display,TEXT("U02F_RESULT %s"),*Json(ResultJson(R)));LastSeenSerial=R.Serial;}
}
void AU02NetworkState::Tick(float Dt)
{
    Super::Tick(Dt);
    if(HasAuthority()){const double R=GetWorld()->GetSubsystem<UU02CollisionWorld>()->FixtureCritRoll;const int32 M=R<0?0:R<.05?2:1;if(M!=CritMode){CritMode=M;ForceNetUpdate();}}
    if(FParse::Param(FCommandLine::Get(),TEXT("U02FProbe")))
    {if(HasAuthority())ProcessFixture();ProbeElapsed+=Dt;if(ProbeElapsed>=.1f){ProbeElapsed=0;EmitState();}}
    if(GetNetMode()!=NM_DedicatedServer&&GEngine)
    {
        AU01Character* Local=nullptr;for(TActorIterator<AU01Character> It(GetWorld());It;++It)if(It->IsLocallyControlled())Local=*It;
        if(Local){const auto V=Local->Vital->GetSnapshot();GEngine->AddOnScreenDebugMessage(290001,.2f,FColor::White,FString::Printf(TEXT("U02-F | HP %d/%d | shield %d | server confirmed %d | %s"),V.HP,V.MaxHP,V.Shield,Results.Num(),CritMode==0?TEXT("server crit5%"):CritMode==1?TEXT("FIXTURE CRIT OFF"):TEXT("FIXTURE CRIT FORCED")));}
        if(!Results.IsEmpty()){const auto& R=Results.Last();const double Now=GetWorld()->GetGameState()?GetWorld()->GetGameState()->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();bool CurrentLife=false;for(TActorIterator<AU02LabDummy> It(GetWorld());It;++It)if(It->NetworkPawnId==R.Target&&It->Vital->GetSnapshot().Generation==R.TargetLife)CurrentLife=true;if(CurrentLife&&Now-R.Timestamp<1.5)GEngine->AddOnScreenDebugMessage(290002,.2f,FColor::Green,FString::Printf(TEXT("CONFIRMED action %llu | damage %d | absorbed %d | HP %d%s%s"),R.Action,R.Damage,R.Absorbed,R.HP,R.Crit?TEXT(" CRIT"):TEXT(""),R.Death?TEXT(" DEFEATED"):TEXT("")));}
    }
}
void AU02NetworkState::EmitState()
{
    auto J=MakeShared<FJsonObject>();FString SHA,Run;FParse::Value(FCommandLine::Get(),TEXT("U02SourceSHA="),SHA);FParse::Value(FCommandLine::Get(),TEXT("U02RunId="),Run);
    J->SetStringField(TEXT("sourceSHA"),SHA);J->SetStringField(TEXT("run"),Run);J->SetStringField(TEXT("utc"),FDateTime::UtcNow().ToIso8601());J->SetNumberField(TEXT("pid"),FPlatformProcess::GetCurrentProcessId());J->SetNumberField(TEXT("time"),GetWorld()->GetTimeSeconds());J->SetNumberField(TEXT("netMode"),GetNetMode());J->SetNumberField(TEXT("worldType"),GetWorld()->WorldType);J->SetStringField(TEXT("world"),GetWorld()->GetPathName());J->SetNumberField(TEXT("critMode"),CritMode);J->SetNumberField(TEXT("localPlayers"),GetGameInstance()?GetGameInstance()->GetNumLocalPlayers():0);
    for(const TCHAR* Name:{TEXT("t.MaxFPS"),TEXT("r.ScreenPercentage"),TEXT("r.Streaming.PoolSize"),TEXT("r.LumenScene.SurfaceCache.AtlasSize"),TEXT("r.RenderTargetPoolMin")})if(auto* V=IConsoleManager::Get().FindConsoleVariable(Name))J->SetNumberField(Name,V->GetFloat());
    TArray<TSharedPtr<FJsonValue>> Pawns,Targets,Events;
    for(TActorIterator<AU01Character> It(GetWorld());It;++It){auto P=It->Combat->GetDiagnostics();P->SetStringField(TEXT("id"),It->NetworkPawnId.ToString());P->SetBoolField(TEXT("local"),It->IsLocallyControlled());P->SetNumberField(TEXT("role"),It->GetLocalRole());P->SetNumberField(TEXT("remoteRole"),It->GetRemoteRole());P->SetStringField(TEXT("owner"),GetPathNameSafe(It->GetOwner()));P->SetStringField(TEXT("position"),It->GetActorLocation().ToString());P->SetNumberField(TEXT("speed"),It->GetVelocity().Size2D());P->SetNumberField(TEXT("lockMask"),It->GetU01Movement()->GetLockMask());P->SetBoolField(TEXT("montage"),It->GetMesh()->GetAnimInstance()&&It->GetMesh()->GetAnimInstance()->IsAnyMontagePlaying());if(auto* PC=Cast<AU01PlayerController>(It->GetController()))P->SetNumberField(TEXT("control"),int32(PC->ControlState));Pawns.Add(MakeShared<FJsonValueObject>(P));}
    for(TActorIterator<AU02LabDummy> It(GetWorld());It;++It){auto T=It->Vital->GetDiagnostics();T->SetStringField(TEXT("id"),It->NetworkPawnId.ToString());T->SetNumberField(TEXT("identityLife"),It->LifeGeneration);T->SetStringField(TEXT("position"),It->GetActorLocation().ToString());Targets.Add(MakeShared<FJsonValueObject>(T));}
    for(const auto& R:Results)Events.Add(MakeShared<FJsonValueObject>(ResultJson(R)));J->SetArrayField(TEXT("pawns"),Pawns);J->SetArrayField(TEXT("targets"),Targets);J->SetArrayField(TEXT("results"),Events);UE_LOG(LogU02Network,Display,TEXT("U02F_STATE %s"),*Json(J));
}
void AU02NetworkState::ProcessFixture()
{
#if !UE_BUILD_SHIPPING
    FString File,Command;if(!FParse::Value(FCommandLine::Get(),TEXT("U02FCommands="),File)||!FFileHelper::LoadFileToString(Command,*File)||Command==LastFixtureCommand)return;LastFixtureCommand=Command;
    TArray<FString> A;Command.ParseIntoArrayWS(A);if(A.Num()<2)return;const FString Mode=A[1];auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>();W->DrainAt(GetWorld()->GetTimeSeconds());
    if(Mode==TEXT("shield")){for(TActorIterator<AU02LabDummy> It(GetWorld());It;++It)It->Vital->AddFixtureShield(1,40,GetWorld()->GetTimeSeconds()+60,GetWorld()->GetTimeSeconds());}
    else if(Mode==TEXT("crit"))W->FixtureCritRoll=0;
    else if(Mode==TEXT("reset"))W->ResetLabDummies();
    else if(Mode==TEXT("concurrent")){for(TActorIterator<AU01Character> It(GetWorld());It;++It)It->Combat->SubmitAttackIntent(It->Combat->GetLastCommand()+1,0,0);}
    else
    {
        W->FixtureCritRoll=1.-1e-9;W->ResetLabDummies();TArray<AU01Character*> P;for(TActorIterator<AU01Character> It(GetWorld());It;++It)P.Add(*It);P.Sort([](const AU01Character& X,const AU01Character& Y){return X.NetworkPawnId<Y.NetworkPawnId;});
        const int Lane=Mode==TEXT("wall")?1:Mode==TEXT("partial")?2:0;
        for(int I=0;I<P.Num();++I){auto* C=P[I];C->GetU01Movement()->ResetFixtureState();FVector Pos(Mode==TEXT("miss")?-450:0,-6000-1000*Lane+(I?50:-50),110);C->SetActorLocation(Pos,false,nullptr,ETeleportType::TeleportPhysics);C->SetActorRotation(FRotator::ZeroRotator);C->GetU01Movement()->ForceReplicationUpdate();C->GetU01Movement()->ForceClientAdjustment();if(auto* PC=Cast<APlayerController>(C->GetController())){PC->SetControlRotation(FRotator::ZeroRotator);PC->ClientSetLocation(Pos,FRotator::ZeroRotator);}}
        if(Mode==TEXT("lethal")){for(TActorIterator<AU02LabDummy> It(GetWorld());It;++It){FHitCandidate H;H.Id.Target={It->NetworkPawnId,It->LifeGeneration};for(int I=0;I<9;++I)It->Vital->ApplyResolved(H,1,.5);}}
    }
    UE_LOG(LogU02Network,Display,TEXT("U02F_FIXTURE %s"),*Command);EmitState();
#endif
}

void AU01PlayerController::U02NetProbe(const FString& Kind)
{if(auto* C=Cast<AU01Character>(GetPawn()))C->Combat->SendNetworkFixtureProbe(Kind);}
