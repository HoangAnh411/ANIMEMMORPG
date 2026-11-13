#include "U02CombatComponent.h"
#include <limits>
#include "U02CollisionWorld.h"
#include "U02VitalComponent.h"
#include "U01/U01Character.h"
#include "U01/U01PlayerController.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "GameFramework/GameStateBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Animation/AnimInstance.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "DrawDebugHelpers.h"
#include "Sound/SoundWaveProcedural.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogU02Combat, Log, All);
using namespace AnimeMMORPG::U02;

namespace
{
class FU03NoEvents final : public AnimeMMORPG::U03::ITimelineResolver
{
public:
    TOptional<double> NextEvent(const AnimeMMORPG::U03::FTimelineModel&,double) override {return {};}
    void ResolveInterval(const AnimeMMORPG::U03::FActiveInterval&) override {}
    void ResolveEvent(AnimeMMORPG::U03::FTimelineModel&,double) override {checkNoEntry();}
};
}
UU02CombatComponent::UU02CombatComponent()
{
    PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickGroup=TG_PrePhysics;SetIsReplicatedByDefault(true);
}
AU01Character* UU02CombatComponent::Character() const {return Cast<AU01Character>(GetOwner());}
void UU02CombatComponent::BeginPlay()
{
    Super::BeginPlay();auto* C=Character();
    if(!C||!GetWorld()||(GetWorld()->WorldType!=EWorldType::Game&&GetWorld()->WorldType!=EWorldType::PIE)){SetComponentTickEnabled(false);return;}
    C->GetU01Movement()->AddTickPrerequisiteComponent(this);
    TArray<UPrimitiveComponent*> Parts;C->GetComponents(Parts);for(auto* P:Parts)P->SetCollisionResponseToChannel(ECC_GameTraceChannel2,ECR_Ignore);
    if(C->GetMesh()->GetSkeletalMeshAsset())if(auto* Class=LoadClass<UAnimInstance>(nullptr,TEXT("/Game/AnimeMMORPG/U03/Animation/ABP_U03.ABP_U03_C")))C->GetMesh()->SetAnimInstanceClass(Class);
    if(C->HasAuthority())
    {
        Model=MakeUnique<AnimeMMORPG::U03::FTimelineModel>(FLifeId{C->NetworkPawnId,1},GetWorld()->GetTimeSeconds());
        Publish(Model->Time(),true);GetWorld()->GetSubsystem<UU02CollisionWorld>()->RegisterCombat(this);
    }
}
void UU02CombatComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if(GetWorld())if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())W->UnregisterCombat(this);
    OnActiveInterval.Clear();BeforeActionMutation.Unbind();Super::EndPlay(Reason);
}
void UU02CombatComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(UU02CombatComponent,Snapshot);DOREPLIFETIME_CONDITION(UU02CombatComponent,OwnerAdmission,COND_OwnerOnly);}
void UU02CombatComponent::SubmitAttackIntent(uint64 Sequence,double Local,double Yaw)
{SubmitCombatIntent(AnimeMMORPG::U03::ECommand::Attack,Sequence,Local,Yaw);}
void UU02CombatComponent::SubmitCombatIntent(AnimeMMORPG::U03::ECommand Command,uint64 Sequence,double Local,double Yaw,FVector2D Direction)
{
    if(!Character())return;
    if(Character()->HasAuthority())ReceiveIntent(Command,Sequence,Local,Yaw,Snapshot.PawnId,Snapshot.LifeGeneration,Direction);
    else {LastSentCommand=Sequence;LastSentLife=Snapshot.LifeGeneration;ServerCombat(uint8(Command),Sequence,Local,Yaw,Snapshot.PawnId,Snapshot.LifeGeneration,Direction);}
}
void UU02CombatComponent::ServerAttack_Implementation(uint64 Sequence,double Local,double Yaw,FGuid Pawn,uint64 Life)
{ReceiveIntent(AnimeMMORPG::U03::ECommand::Attack,Sequence,Local,Yaw,Pawn,Life);}
void UU02CombatComponent::ServerCombat_Implementation(uint8 Command,uint64 Sequence,double Local,double Yaw,FGuid Pawn,uint64 Life,FVector2D Direction)
{ReceiveIntent(static_cast<AnimeMMORPG::U03::ECommand>(Command),Sequence,Local,Yaw,Pawn,Life,Direction);}
void UU02CombatComponent::ReceiveIntent(AnimeMMORPG::U03::ECommand Command,uint64 Sequence,double Local,double Yaw,FGuid Pawn,uint64 Life,FVector2D Direction)
{
    if(!Model||!Character()||!Character()->HasAuthority())return;
    if(QueuedIntents.Num()>=64){++RejectedCount;return;}
    QueuedIntents.Add({{Sequence,{Pawn,Life},Command,0,Yaw,Direction},Local,GetWorld()->GetTimeSeconds()});
}
void UU02CombatComponent::SetControlPlaying(bool Playing)
{
    if(!Character())return;
    if(Character()->HasAuthority())ServerControlPlaying_Implementation(Playing);else ServerControlPlaying(Playing);
}
void UU02CombatComponent::ServerControlPlaying_Implementation(bool Playing)
{
    bAuthorityPlaying=Playing;
    if(!Playing)DiscardPendingInputs();
}
void UU02CombatComponent::DiscardPendingInputs()
{
    if(!Model)return;
    if(BeforeActionMutation.IsBound())BeforeActionMutation.Execute(GetWorld()->GetTimeSeconds());
    for(const auto& E:QueuedIntents)if(E.Intent.Life==Model->GetLife())AdmissionWatermark=FMath::Max(AdmissionWatermark,E.Intent.Sequence);
    QueuedIntents.Empty();Model->DropGuardCurrent();Publish(Model->Time(),true);
}
void UU02CombatComponent::ServerAim_Implementation(double Yaw,FGuid Pawn,uint64 Life,uint64 Action)
{if(Model&&FMath::IsFinite(Yaw)&&QueuedAim.Num()<16)QueuedAim.Add({Yaw,Pawn,Life,Action});}
void UU02CombatComponent::ServerGuardAim_Implementation(double Yaw,FGuid Pawn,uint64 Life,uint64 Guard)
{if(Model&&Guard&&FMath::IsFinite(Yaw)&&QueuedAim.Num()<16)QueuedAim.Add({Yaw,Pawn,Life,0,Guard});}
void UU02CombatComponent::HandleAttack(uint64 Sequence,double Local,double Yaw,double Now)
{
    // Native test adapter uses the identical enqueue + world barrier path.
    ReceiveIntent(AnimeMMORPG::U03::ECommand::Attack,Sequence,Local,Yaw,Snapshot.PawnId,Snapshot.LifeGeneration);
    if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())W->DrainAt(Now);
}
void UU02CombatComponent::ProcessQueuedIntents(double Now)
{
    using namespace AnimeMMORPG::U03;
    if(!Model)return;
    for(const auto& A:QueuedAim)if(A.Pawn==Snapshot.PawnId&&A.Life==Snapshot.LifeGeneration&&
        (A.Guard?(Model->Defense().bGuard&&A.Guard==Model->Defense().GuardSequence):(!Model->Defense().bGuard&&A.Action==Snapshot.ActionSequence)))
        if(Model->UpdateAim(Now,A.Yaw)){StartupTurn.Retarget(Now,A.Yaw);Publish(Now,true);}
    QueuedAim.Empty();
    auto* C=Character();auto* M=C->GetU01Movement();FAdmissionContext Context;
    Context.bPlaying=bAuthorityPlaying&&!(M->GetLockMask()&(uint8(EU01MotorLock::Control)|uint8(EU01MotorLock::Interacting)));
    if(const auto* PC=Cast<AU01PlayerController>(C->GetController()))Context.bPlaying&=PC->ControlState==EU01ControlState::Playing;
    Context.bGrounded=M->IsMovingOnGround();Context.bDead=C->Vital&&C->Vital->GetSnapshot().bDead;
    Context.bDodgeEnabled=true;Context.bDefenseEnabled=true;
    auto Commands=MoveTemp(QueuedIntents);QueuedIntents.Empty();
    Commands.Sort([](const auto& A,const auto& B){return A.Receive!=B.Receive?A.Receive<B.Receive:A.Intent.Sequence<B.Intent.Sequence;});
    TSet<uint64> Conflicts;
    for(int32 A=0;A<Commands.Num();++A)for(int32 B=A+1;B<Commands.Num();++B)
        if(Commands[A].Intent.Sequence==Commands[B].Intent.Sequence && (Commands[A].Intent.Command!=Commands[B].Intent.Command||Commands[A].Intent.AimYaw!=Commands[B].Intent.AimYaw||Commands[A].Intent.Direction!=Commands[B].Intent.Direction||!(Commands[A].Intent.Life==Commands[B].Intent.Life)))Conflicts.Add(Commands[A].Intent.Sequence);
    TArray<TArray<FCombatIntent>> Admissible;
    TArray<double> ReceiveGroups;
    for(auto& Entry:Commands)
    {
        auto& I=Entry.Intent;I.Receive=Now;LastCommand=FMath::Max(LastCommand,I.Sequence);
        EAdmission Result=EAdmission::Invalid;
        if(I.Life==Model->GetLife())
        {
            if(Conflicts.Contains(I.Sequence)){Result=EAdmission::Invalid;AdmissionWatermark=FMath::Max(AdmissionWatermark,I.Sequence);}
            else if(I.Sequence==0||I.Sequence<=AdmissionWatermark)Result=EAdmission::Stale;
            else
            {
                AdmissionWatermark=I.Sequence;
                if(I.Command==ECommand::Attack||I.Command==ECommand::Dodge||I.Command==ECommand::Guard||I.Command==ECommand::GuardRelease||I.Command==ECommand::Escape)
                {
                    int32 Group=ReceiveGroups.Find(Entry.Receive);
                    if(Group==INDEX_NONE){Group=ReceiveGroups.Add(Entry.Receive);Admissible.AddDefaulted();}
                    Admissible[Group].Add(I);continue;
                }
                else Result=EAdmission::Unsupported;
            }
        }
        OwnerAdmission.Command=I.Sequence;OwnerAdmission.Admission=uint8(Result);++OwnerAdmission.Revision;
        const bool Success=Result==EAdmission::Accepted||Result==EAdmission::Queued||Result==EAdmission::Replaced;
        if(Success){++AcceptedCount;if(Result==EAdmission::Queued)++QueuedCount;if(Result==EAdmission::Replaced)++ReplacedCount;LastReject=EReject::None;}
        else {++RejectedCount;LastReject=Result==EAdmission::Stale||!(I.Life==Model->GetLife())?EReject::StaleCommand:!Context.bPlaying?EReject::NotPlaying:!Context.bGrounded?EReject::Airborne:Context.bDead?EReject::Defeated:!FMath::IsFinite(I.AimYaw)?EReject::InvalidAim:EReject::Busy;}
        Publish(Now,true);
        Trace(Success?TEXT("Admitted"):TEXT("Rejected"),Now,FString::Printf(TEXT("command=%llu admission=%u localInput=%.17g receive=%.17g accept=%.17g"),I.Sequence,uint8(Result),Entry.LocalSeconds,Entry.Receive,Now));
    }
    const uint64 BeforeDodge=Model->Dodge().Sequence;
    FU03NoEvents ResolvedBarrier;TArray<FAdmissionResult> Results;
    for(auto& Group:Admissible)Results.Append(Model->SubmitBatch(MoveTemp(Group),Context,ResolvedBarrier));
    if((BeforeDodge!=Model->Dodge().Sequence||(!Model->Current()&&Model->Defense().bGuard)) && Snapshot.ActionSequence)
    {Snapshot.Phase=uint8(EPhase::Cancelled);Snapshot.ServerSeconds=Now;GetWorld()->GetSubsystem<UU02CollisionWorld>()->ObserveCombat(this);}
    for(const auto& R:Results)
    {
        OwnerAdmission.Command=R.Sequence;OwnerAdmission.Admission=uint8(R.Result);++OwnerAdmission.Revision;
        const bool Success=R.Result==EAdmission::Accepted||R.Result==EAdmission::Queued||R.Result==EAdmission::Replaced;
        if(Success){++AcceptedCount;if(R.Result==EAdmission::Queued)++QueuedCount;if(R.Result==EAdmission::Replaced)++ReplacedCount;LastReject=EReject::None;}
        else {++RejectedCount;LastReject=R.Result==EAdmission::Stale?EReject::StaleCommand:!Context.bPlaying?EReject::NotPlaying:!Context.bGrounded?EReject::Airborne:Context.bDead?EReject::Defeated:EReject::Busy;}
        Trace(Success?TEXT("Admitted"):TEXT("Rejected"),Now,FString::Printf(TEXT("command=%llu admission=%u accept=%.17g"),R.Sequence,uint8(R.Result),Now));
    }
    Publish(Now);
}
void UU02CombatComponent::RememberCurrent(double Now)
{
    if(!Model||!Model->Current())return;
    const auto& A=*Model->Current();const auto& D=A.GetDefinition();
    if(Snapshot.ActionSequence!=A.Identity.Sequence||Snapshot.LifeGeneration!=A.Identity.Source.Generation)
    {
        StartupTurn.Begin(Character()->GetActorRotation().Yaw,A.Yaw,A.Start,A.Start+D.ActiveStart);
        Snapshot.ActionSequence=A.Identity.Sequence;Snapshot.StartSeconds=A.Start;
    }
    Snapshot.DefinitionId=uint8(D.Id);Snapshot.DefinitionVersion=D.Version;Snapshot.RawDamage=D.RawDamage;
    Snapshot.ActiveStart=D.ActiveStart;Snapshot.ActiveEnd=D.ActiveEnd;Snapshot.Duration=D.Duration;
    Snapshot.AimYawDegrees=A.Yaw;
}
bool UU02CombatComponent::AdvanceAuthority(double Now,bool)
{if(!Model)return false;GetWorld()->GetSubsystem<UU02CollisionWorld>()->DrainAt(Now);return Model->Time()==Now;}
bool UU02CombatComponent::CancelAt(ECancel Reason,double Now)
{
    if(!Model)return false;
    if(Reason==ECancel::Menu||Reason==ECancel::Focus){DiscardPendingInputs();return false;}
    // Dodge/guard gameplay is not available until B1/B2.
    if(Reason==ECancel::Dodge||Reason==ECancel::Guard)return false;
    const auto Cut=Reason==ECancel::LostGround?AnimeMMORPG::U03::ECutoff::LostGround:AnimeMMORPG::U03::ECutoff::Death;
    return GetWorld()->GetSubsystem<UU02CollisionWorld>()->ApplyLifecycle(this,Now,Cut,false);
}
bool UU02CombatComponent::CancelAction(ECancel Reason){return CancelAt(Reason,GetWorld()->GetTimeSeconds());}
void UU02CombatComponent::HandleDefeat(double At)
{
    if(!Model||!Character()->HasAuthority())return;
    GetWorld()->GetSubsystem<UU02CollisionWorld>()->ApplyLifecycle(this,At,AnimeMMORPG::U03::ECutoff::Death,false);
    Character()->GetU01Movement()->SetMotorLock(EU01MotorLock::Defeated,true);Trace(TEXT("VitalDeath"),At);
}
void UU02CombatComponent::LostGround()
{if(Model)GetWorld()->GetSubsystem<UU02CollisionWorld>()->ApplyLifecycle(this,GetWorld()->GetTimeSeconds(),AnimeMMORPG::U03::ECutoff::LostGround,false);}
void UU02CombatComponent::Landed()
{if(Model)GetWorld()->GetSubsystem<UU02CollisionWorld>()->ApplyLifecycle(this,GetWorld()->GetTimeSeconds(),AnimeMMORPG::U03::ECutoff::LostGround,true);}
bool UU02CombatComponent::ResetLabCombat()
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if(!Model||!Character()->HasAuthority())return false;
    const double Now=FMath::Max(double(GetWorld()->GetTimeSeconds()),Model->Time());auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>();W->DrainAt(Now);
    auto Life=Model->GetLife();++Life.Generation;if(!Model->ResetLife(Life,Now))return false;
    QueuedIntents.Empty();QueuedAim.Empty();Snapshot.ActionSequence=0;Snapshot.Phase=uint8(EPhase::Idle);Snapshot.bLocked=false;Snapshot.DefenseEvent=0;Snapshot.DefenseResult=0;Snapshot.DefenseEventTime=0;
    OwnerAdmission.PendingCommand=0;OwnerAdmission.PendingExpires=0;
    if(Character()->Vital)Character()->Vital->ResetLabCombat(Life.Generation);
    Publish(Now,true);W->RebaseResetSubject(Character());Trace(TEXT("Reset"),Now);return true;
#endif
}
void UU02CombatComponent::Publish(double Now,bool Force)
{
    if(!Model)return;const auto Before=Snapshot;RememberCurrent(Now);const auto Life=Model->GetLife();
    Snapshot.PawnId=Life.Pawn;Snapshot.LifeGeneration=Life.Generation;Snapshot.ServerSeconds=Now;
    if(Before.DodgeSequence!=Model->Dodge().Sequence && Snapshot.ActionSequence && !Model->Current())
    {Snapshot.Phase=uint8(EPhase::Cancelled);GetWorld()->GetSubsystem<UU02CollisionWorld>()->ObserveCombat(this);}
    if(const auto* A=Model->Current())
    {
        Snapshot.Phase=uint8(Now>=A->Cutoff?EPhase::Cancelled:Now<A->Start+Snapshot.ActiveStart?EPhase::Startup:Now<A->Start+Snapshot.ActiveEnd?EPhase::Active:EPhase::Recovery);
        Snapshot.bLocked=Now<A->Cutoff&&Now<A->End();Snapshot.bYawLocked=Snapshot.bLocked&&Now>=A->Start+Snapshot.ActiveStart;
    }
    else {Snapshot.bLocked=false;Snapshot.bYawLocked=false;if(Snapshot.ActionSequence&&Snapshot.Phase!=uint8(EPhase::Cancelled))Snapshot.Phase=uint8(EPhase::Finished);}
    const auto& D=Model->Dodge();if(Snapshot.DodgeSequence!=D.Sequence)Snapshot.DodgeOrigin=Character()->GetActorLocation();Snapshot.DodgeSequence=D.Sequence;Snapshot.DodgeCharges=D.Charges;Snapshot.DodgeStart=D.Start;Snapshot.DodgeMotionEnd=D.MotionEnd;Snapshot.DodgeLockEnd=D.LockEnd;Snapshot.DodgeNextStart=D.NextStart;Snapshot.DodgeRestoreAt=D.RestoreAt;Snapshot.DodgeDirection=D.Direction;
    if(D.Locked(Now)){Snapshot.bLocked=true;Snapshot.bYawLocked=true;}
    Snapshot.Energy=Model->Resources().Energy();Snapshot.QReadyAt=Model->Resources().ReadyAt(AnimeMMORPG::U03::EAction::Q);Snapshot.EReadyAt=Model->Resources().ReadyAt(AnimeMMORPG::U03::EAction::E);
    const auto& Defense=Model->Defense();Snapshot.bGuard=Defense.bGuard;Snapshot.GuardSequence=Defense.GuardSequence;Snapshot.GuardYaw=Defense.Yaw;Snapshot.Posture=Defense.Posture;
    Snapshot.bParryOpen=Defense.bParryOpen;Snapshot.ParryStart=Defense.ParryStart;Snapshot.ParryEnd=Defense.ParryEnd;Snapshot.ParryReadyAt=Defense.ParryReadyAt;
    Snapshot.HardCC=uint8(Defense.Hard);Snapshot.HardEnd=Defense.HardEnd;Snapshot.LockedBudget=Defense.LockedBudget;Snapshot.ImmuneEnd=Defense.ImmuneEnd;Snapshot.SlowFraction=Defense.Slow(Now);Snapshot.XReadyAt=Defense.XReadyAt;
    if(Defense.Locked(Now)){Snapshot.bLocked=true;Snapshot.bYawLocked=true;}
    if(Defense.bGuard)Snapshot.AimYawDegrees=Defense.Yaw;
    const auto& Pending=Model->GetPendingDodge().IsSet()?Model->GetPendingDodge():Model->GetPending();OwnerAdmission.PendingCommand=Pending.IsSet()?Pending->Sequence:0;OwnerAdmission.PendingExpires=Pending.IsSet()?Pending->Receive+.15:0;
    Snapshot.TurnFromYaw=StartupTurn.FromYaw;Snapshot.TurnStartSeconds=StartupTurn.SegmentStart;
    Snapshot.LastCommand=LastCommand;Snapshot.Accepted=AcceptedCount;Snapshot.Rejected=RejectedCount;Snapshot.RejectReason=uint8(LastReject);
    ++Snapshot.Revision;ApplyMotorSnapshot();
    if(Force||Before.Phase!=Snapshot.Phase||Before.ActionSequence!=Snapshot.ActionSequence||Before.AimYawDegrees!=Snapshot.AimYawDegrees||Before.Energy!=Snapshot.Energy)Character()->ForceNetUpdate();
    if(Before.ActionSequence!=Snapshot.ActionSequence&&Snapshot.ActionSequence)Trace(TEXT("ActionStarted"),Snapshot.StartSeconds);
}
void UU02CombatComponent::ApplyMotorSnapshot()
{
    if(auto* C=Character())
    {
        const auto* GS=GetWorld()->GetGameState();const double Now=C->HasAuthority()?Snapshot.ServerSeconds:(GS?GS->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds());
        FStartupTurn Turn;Turn.Begin(Snapshot.TurnFromYaw,Snapshot.AimYawDegrees,Snapshot.TurnStartSeconds,Snapshot.StartSeconds+Snapshot.ActiveStart);
        const bool DodgeLock=Snapshot.DodgeSequence&&Now>=Snapshot.DodgeStart&&Now<Snapshot.DodgeLockEnd;
        const double Yaw=Snapshot.bGuard?Snapshot.GuardYaw:DodgeLock?Snapshot.DodgeDirection.Rotation().Yaw:Turn.Sample(Now);
        C->GetU01Movement()->ApplyDefenseAuthority(Snapshot.bGuard,Snapshot.SlowFraction);
        C->GetU01Movement()->ApplyCombatAuthority(Snapshot.bLocked,Snapshot.bYawLocked||Snapshot.bGuard,Yaw);
        if(Snapshot.bLocked)C->SetActorRotation(FRotator(0,Yaw,0));
    }
}
void UU02CombatComponent::OnRep_Snapshot(){ApplyMotorSnapshot();}
void UU02CombatComponent::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt,Type,Function);auto* C=Character();if(!C)return;const double Now=GetWorld()->GetTimeSeconds();
    if(C->IsLocallyControlled()&&C->GetController()&&(Snapshot.bGuard||Snapshot.Phase==uint8(EPhase::Startup))&&Now-LastAimSend>=1./30)
    {
        if(Snapshot.bGuard){if(Model)ServerGuardAim_Implementation(C->GetControlRotation().Yaw,Snapshot.PawnId,Snapshot.LifeGeneration,Snapshot.GuardSequence);else ServerGuardAim(C->GetControlRotation().Yaw,Snapshot.PawnId,Snapshot.LifeGeneration,Snapshot.GuardSequence);}
        else {if(Model)ServerAim_Implementation(C->GetControlRotation().Yaw,Snapshot.PawnId,Snapshot.LifeGeneration,Snapshot.ActionSequence);else ServerAim(C->GetControlRotation().Yaw,Snapshot.PawnId,Snapshot.LifeGeneration,Snapshot.ActionSequence);}
        LastAimSend=Now;
    }
    if(!Model)ApplyMotorSnapshot();
    const auto* FeedbackClock=GetWorld()->GetGameState();const double FeedbackNow=FeedbackClock?FeedbackClock->GetServerWorldTimeSeconds():Now;
    if(PresentedDefenseLife!=Snapshot.LifeGeneration){PresentedDefenseLife=Snapshot.LifeGeneration;PresentedDefenseEvent=0;}
    if(Snapshot.DefenseEvent!=PresentedDefenseEvent)
    {
        PresentedDefenseEvent=Snapshot.DefenseEvent;
        if(Snapshot.DefenseResult==uint8(AnimeMMORPG::U03::EDefense::Parry)&&FeedbackNow-Snapshot.DefenseEventTime<1.2&&C->IsLocallyControlled())
        {
            ParryTone=NewObject<USoundWaveProcedural>(this);ParryTone->SetSampleRate(24000);ParryTone->NumChannels=1;ParryTone->Duration=.24f;
            TArray<int16> PCM;PCM.SetNumZeroed(5760);
            for(int I=0;I<PCM.Num();++I){const double T=I/24000.,Local=FMath::Fmod(T,.12);const double Envelope=FMath::Min(1.,Local/.005)*FMath::Max(0.,1.-Local/.12);PCM[I]=int16(6000.*Envelope*FMath::Sin(2.*PI*(T<.12?660.:990.)*Local));}
            ParryTone->QueueAudio(reinterpret_cast<const uint8*>(PCM.GetData()),PCM.Num()*sizeof(int16));UGameplayStatics::PlaySound2D(this,ParryTone);
        }
    }
    if(Snapshot.bGuard)DrawDebugBox(GetWorld(),C->GetActorLocation()+FRotator(0,Snapshot.GuardYaw,0).Vector()*45,FVector(3,35,55),FRotator(0,Snapshot.GuardYaw,0).Quaternion(),FColor::Blue,false,0,0,2);
    if(FeedbackNow-Snapshot.DefenseEventTime<1.2&&Snapshot.DefenseEvent&&Snapshot.DefenseResult==uint8(AnimeMMORPG::U03::EDefense::Parry))
        DrawDebugCircle(GetWorld(),C->GetActorLocation(),65+30*FMath::Clamp(FeedbackNow-Snapshot.DefenseEventTime,0.,1.2),32,FColor::White,false,0,0,3,FVector::ForwardVector,FVector::RightVector,false);
    if(C->IsLocallyControlled()&&GEngine)
    {
        FString AttackKey=TEXT("LMB");if(const auto* PC=Cast<AU01PlayerController>(C->GetController()))AttackKey=PC->GetPreferences().Keys[AnimeMMORPG::U01::Attack].GetDisplayName().ToString();
        const TCHAR* Reasons[]={TEXT("Accepted"),TEXT("Queued"),TEXT("Replaced"),TEXT("Stale"),TEXT("Invalid"),TEXT("Locked"),TEXT("Busy"),TEXT("Energy"),TEXT("Cooldown"),TEXT("Unsupported")};
        GEngine->AddOnScreenDebugMessage(uint64(C->GetUniqueID())+200000,.15f,FColor::Cyan,FString::Printf(TEXT("%s Attack %u/3 | action %llu | energy %.0f/100 | pending %llu | %s"),*AttackKey,Snapshot.DefinitionId+1,Snapshot.ActionSequence,Snapshot.Energy,OwnerAdmission.PendingCommand,Reasons[FMath::Min<int32>(OwnerAdmission.Admission,9)]));
        FString DodgeKey=TEXT("Shift");if(const auto* PC=Cast<AU01PlayerController>(C->GetController()))DodgeKey=PC->GetPreferences().Keys[AnimeMMORPG::U01::Dodge].GetDisplayName().ToString();
        const auto* Clock=GetWorld()->GetGameState();const double AuthorityNow=C->HasAuthority()?Now:Clock?Clock->GetServerWorldTimeSeconds():Snapshot.ServerSeconds;
        GEngine->AddOnScreenDebugMessage(uint64(C->GetUniqueID())+210000,.15f,FColor::Yellow,FString::Printf(TEXT("%s Dodge %d/2 | recharge %.2fs | %s"),*DodgeKey,Snapshot.DodgeCharges,Snapshot.DodgeCharges<2?FMath::Max(0.,Snapshot.DodgeRestoreAt-AuthorityNow):0.,AuthorityNow<Snapshot.DodgeMotionEnd?TEXT("DODGE"):AuthorityNow<Snapshot.DodgeLockEnd?TEXT("RECOVERY"):TEXT("READY")));
        FString GuardKey=TEXT("RMB"),XKey=TEXT("X");if(const auto* PC=Cast<AU01PlayerController>(C->GetController())){GuardKey=PC->GetPreferences().Keys[AnimeMMORPG::U01::Guard].GetDisplayName().ToString();XKey=PC->GetPreferences().Keys[AnimeMMORPG::U01::EscapeCC].GetDisplayName().ToString();}
        const TCHAR* CCNames[]={TEXT("FREE"),TEXT("STUN"),TEXT("KNOCKDOWN"),TEXT("LAUNCH (fixture; no impulse)"),TEXT("GRAB"),TEXT("!! GUARD BREAK !!")};
        GEngine->AddOnScreenDebugMessage(uint64(C->GetUniqueID())+220000,.15f,FColor::White,FString::Printf(TEXT("[%s] %s | POSTURE [%.0f/100] | %s %.2fs | IMMUNE %.2fs | [%s] X %.2fs | slow %.0f%%"),*GuardKey,Snapshot.bGuard?TEXT("[BLOCK]"):TEXT("released"),Snapshot.Posture,CCNames[FMath::Min<int32>(Snapshot.HardCC,5)],FMath::Max(0.,Snapshot.HardEnd-AuthorityNow),FMath::Max(0.,Snapshot.ImmuneEnd-AuthorityNow),*XKey,FMath::Max(0.,Snapshot.XReadyAt-AuthorityNow),Snapshot.SlowFraction*100));
        if(Snapshot.DefenseEvent&&AuthorityNow-Snapshot.DefenseEventTime<1.2)GEngine->AddOnScreenDebugMessage(uint64(C->GetUniqueID())+220001,.15f,FColor::White,Snapshot.DefenseResult==2?TEXT("(( PARRY ))"):Snapshot.HardCC==5?TEXT("!! BREAK !!"):TEXT("[ BLOCK ]"));
    }
}
TSharedRef<FJsonObject> UU02CombatComponent::GetDiagnostics() const
{
    auto J=MakeShared<FJsonObject>();
    J->SetStringField(TEXT("pawnId"),Snapshot.PawnId.ToString());
    J->SetStringField(TEXT("lifeId"),FString::Printf(TEXT("%s:%llu"),*Snapshot.PawnId.ToString(),Snapshot.LifeGeneration));
    J->SetStringField(TEXT("actionId"),FString::Printf(TEXT("%s:%llu:%llu"),*Snapshot.PawnId.ToString(),Snapshot.LifeGeneration,Snapshot.ActionSequence));
    J->SetStringField(TEXT("commandId"),FString::Printf(TEXT("%llu"),Model?LastCommand:Snapshot.LastCommand));
    J->SetNumberField(TEXT("life"),Snapshot.LifeGeneration); J->SetNumberField(TEXT("action"),Snapshot.ActionSequence);
    J->SetNumberField(TEXT("phase"),Snapshot.Phase); J->SetNumberField(TEXT("start"),Snapshot.StartSeconds);
    J->SetNumberField(TEXT("definition"),Snapshot.DefinitionId);J->SetNumberField(TEXT("raw"),Snapshot.RawDamage);
    J->SetNumberField(TEXT("energy"),Snapshot.Energy);J->SetNumberField(TEXT("qReady"),Snapshot.QReadyAt);J->SetNumberField(TEXT("eReady"),Snapshot.EReadyAt);
    J->SetNumberField(TEXT("dodge"),Snapshot.DodgeSequence);J->SetNumberField(TEXT("dodgeCharges"),Snapshot.DodgeCharges);J->SetNumberField(TEXT("dodgeStart"),Snapshot.DodgeStart);J->SetNumberField(TEXT("dodgeMotionEnd"),Snapshot.DodgeMotionEnd);J->SetNumberField(TEXT("dodgeLockEnd"),Snapshot.DodgeLockEnd);J->SetNumberField(TEXT("dodgeNextStart"),Snapshot.DodgeNextStart);J->SetNumberField(TEXT("dodgeRestoreAt"),Snapshot.DodgeRestoreAt);J->SetStringField(TEXT("dodgeDirection"),Snapshot.DodgeDirection.ToString());
    J->SetStringField(TEXT("dodgeOrigin"),Snapshot.DodgeOrigin.ToString());
    J->SetBoolField(TEXT("guard"),Snapshot.bGuard);J->SetNumberField(TEXT("guardYaw"),Snapshot.GuardYaw);J->SetNumberField(TEXT("posture"),Snapshot.Posture);
    J->SetBoolField(TEXT("parryOpen"),Snapshot.bParryOpen);J->SetNumberField(TEXT("parryStart"),Snapshot.ParryStart);J->SetNumberField(TEXT("parryEnd"),Snapshot.ParryEnd);J->SetNumberField(TEXT("parryReady"),Snapshot.ParryReadyAt);
    J->SetNumberField(TEXT("hardCC"),Snapshot.HardCC);J->SetNumberField(TEXT("hardEnd"),Snapshot.HardEnd);J->SetNumberField(TEXT("lockedBudget"),Snapshot.LockedBudget);J->SetNumberField(TEXT("immuneEnd"),Snapshot.ImmuneEnd);J->SetNumberField(TEXT("slow"),Snapshot.SlowFraction);J->SetNumberField(TEXT("xReady"),Snapshot.XReadyAt);
    J->SetNumberField(TEXT("defenseEvent"),Snapshot.DefenseEvent);J->SetNumberField(TEXT("defenseResult"),Snapshot.DefenseResult);J->SetNumberField(TEXT("defenseEventTime"),Snapshot.DefenseEventTime);
    J->SetNumberField(TEXT("admission"),OwnerAdmission.Admission);J->SetNumberField(TEXT("pendingCommand"),OwnerAdmission.PendingCommand);
    J->SetNumberField(TEXT("pendingExpires"),OwnerAdmission.PendingExpires);J->SetNumberField(TEXT("queued"),QueuedCount);J->SetNumberField(TEXT("replaced"),ReplacedCount);
    J->SetNumberField(TEXT("activeStart"),Snapshot.StartSeconds+Snapshot.ActiveStart); J->SetNumberField(TEXT("activeEnd"),Snapshot.StartSeconds+Snapshot.ActiveEnd);
    J->SetNumberField(TEXT("end"),Snapshot.StartSeconds+Snapshot.Duration); J->SetNumberField(TEXT("serverSnapshotSeconds"),Snapshot.ServerSeconds);
    J->SetNumberField(TEXT("gameplayBodyYaw"),Character()?Character()->GetActorRotation().Yaw:0.);
    J->SetNumberField(TEXT("meshWorldYaw"),Character()?Character()->GetMesh()->GetComponentRotation().Yaw:0.);
    J->SetNumberField(TEXT("aimYaw"),Snapshot.AimYawDegrees);
    J->SetNumberField(TEXT("turnFromYaw"),Snapshot.TurnFromYaw);
    J->SetNumberField(TEXT("turnStart"),Snapshot.TurnStartSeconds);
    const auto* Clock=GetWorld()->GetGameState();const double ServerNow=Model?GetWorld()->GetTimeSeconds():(Clock?Clock->GetServerWorldTimeSeconds():Snapshot.ServerSeconds);
    J->SetNumberField(TEXT("actionSeconds"),ServerNow-Snapshot.StartSeconds);
    J->SetNumberField(TEXT("yaw"),Snapshot.AimYawDegrees); J->SetBoolField(TEXT("locked"),Snapshot.bLocked);
    J->SetBoolField(TEXT("yawLocked"),Snapshot.bYawLocked); J->SetNumberField(TEXT("accepted"),Model?AcceptedCount:Snapshot.Accepted);
    J->SetNumberField(TEXT("rejected"),Model?RejectedCount:Snapshot.Rejected); J->SetNumberField(TEXT("lastReject"),Model?uint8(LastReject):Snapshot.RejectReason);
    J->SetNumberField(TEXT("command"),Model?LastCommand:Snapshot.LastCommand); J->SetNumberField(TEXT("intervals"),IntervalCount);
    J->SetNumberField(TEXT("lastSliceBegin"),LastInterval.BeginSeconds); J->SetNumberField(TEXT("lastSliceEnd"),LastInterval.EndSeconds);
    if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())
    {J->SetNumberField(TEXT("geometryConfirmed"),W->Confirmed.Num());J->SetNumberField(TEXT("geometryQueries"),W->Queries);J->SetNumberField(TEXT("geometryBlocked"),W->Blocked);J->SetNumberField(TEXT("geometryUnsupportedShapes"),W->UnsupportedObstructions);
        J->SetNumberField(TEXT("damageResults"),W->DamageResults.Num());J->SetNumberField(TEXT("critRolls"),W->CritRolls);J->SetNumberField(TEXT("fixtureCritRoll"),W->FixtureCritRoll);
        if(!W->DamageResults.IsEmpty())
        {
            const auto& R=W->DamageResults.Last();J->SetNumberField(TEXT("lastDamage"),R.Result.Damage);J->SetNumberField(TEXT("lastAbsorbed"),R.Result.Absorbed);
            J->SetNumberField(TEXT("lastTargetHP"),R.Result.AfterHP);J->SetBoolField(TEXT("lastCrit"),R.Result.bCrit);J->SetBoolField(TEXT("lastDeath"),R.Result.bDied);
            J->SetStringField(TEXT("lastDamageTarget"),R.Hit.Id.Target.Pawn.ToString());J->SetNumberField(TEXT("lastDamageTargetLife"),R.Hit.Id.Target.Generation);
        }}
    if(Character()&&Character()->Vital)J->SetObjectField(TEXT("vital"),Character()->Vital->GetDiagnostics());
    return J;
}
void UU02CombatComponent::Trace(const TCHAR* Event, double GameplaySeconds, const FString& Detail) const
{
    auto J=GetDiagnostics(); const auto* C=Character();
    J->SetNumberField(TEXT("phase"),Snapshot.Phase);
    FString SHA,Run; FParse::Value(FCommandLine::Get(),TEXT("U02SourceSHA="),SHA); FParse::Value(FCommandLine::Get(),TEXT("U02RunId="),Run);
    J->SetStringField(TEXT("sourceSHA"),SHA); J->SetStringField(TEXT("runId"),Run); J->SetStringField(TEXT("event"),Event);
    J->SetStringField(TEXT("utc"),FDateTime::UtcNow().ToIso8601()); J->SetNumberField(TEXT("pid"),FPlatformProcess::GetCurrentProcessId());
    J->SetStringField(TEXT("world"),GetWorld()->GetPathName()); J->SetNumberField(TEXT("worldType"),int32(GetWorld()->WorldType));
    J->SetNumberField(TEXT("netMode"),int32(GetWorld()->GetNetMode())); J->SetStringField(TEXT("pawn"),GetPathNameSafe(C));
    J->SetStringField(TEXT("owner"),GetPathNameSafe(C?C->GetOwner():nullptr));
    J->SetNumberField(TEXT("localRole"),C?int32(C->GetLocalRole()):0); J->SetNumberField(TEXT("remoteRole"),C?int32(C->GetRemoteRole()):0);
    J->SetNumberField(TEXT("gameplaySeconds"),GameplaySeconds); J->SetNumberField(TEXT("observedSeconds"),GetWorld()->GetTimeSeconds());
    J->SetStringField(TEXT("detail"),Detail);
    FString Text; FJsonSerializer::Serialize(J,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text));
    UE_LOG(LogU02Combat,Display,TEXT("U02B_EVENT %s"),*Text);
}

void UU02CombatComponent::SendNetworkFixtureProbe(const FString& Kind)
{
#if !UE_BUILD_SHIPPING
    if(!FParse::Param(FCommandLine::Get(),TEXT("U02FProbe"))||!Character()||!Character()->IsLocallyControlled()||!GetWorld()->GetMapName().EndsWith(TEXT("L_NetworkLab")))return;
    if(Kind==TEXT("duplicate"))ServerAttack(LastSentCommand,GetWorld()->GetTimeSeconds(),0,Snapshot.PawnId,LastSentLife);
    if(Kind==TEXT("stale"))ServerAttack(LastSentCommand+1,GetWorld()->GetTimeSeconds(),0,Snapshot.PawnId,Snapshot.LifeGeneration-1);
    if(Kind==TEXT("nan"))ServerAttack(FMath::Max(LastSentCommand,Snapshot.LastCommand)+1,GetWorld()->GetTimeSeconds(),std::numeric_limits<double>::quiet_NaN(),Snapshot.PawnId,Snapshot.LifeGeneration);
    if(Kind==TEXT("other"))for(TActorIterator<AU01Character> It(GetWorld());It;++It)if(*It!=Character()){It->Combat->ServerAttack(1,0,0,It->NetworkPawnId,It->Combat->Snapshot.LifeGeneration);break;}
    if(Kind==TEXT("dodgeduplicate"))ServerCombat(uint8(AnimeMMORPG::U03::ECommand::Dodge),LastSentCommand,0,0,Snapshot.PawnId,LastSentLife,FVector2D(1,0));
    if(Kind==TEXT("dodgestale"))ServerCombat(uint8(AnimeMMORPG::U03::ECommand::Dodge),LastSentCommand+1,0,0,Snapshot.PawnId,Snapshot.LifeGeneration-1,FVector2D(1,0));
    if(Kind==TEXT("dodgenan"))ServerCombat(uint8(AnimeMMORPG::U03::ECommand::Dodge),LastSentCommand+1,0,std::numeric_limits<double>::quiet_NaN(),Snapshot.PawnId,Snapshot.LifeGeneration,FVector2D(1,0));
    if(Kind==TEXT("dodgeother"))for(TActorIterator<AU01Character> It(GetWorld());It;++It)if(*It!=Character()){It->Combat->ServerCombat(uint8(AnimeMMORPG::U03::ECommand::Dodge),1,0,0,It->NetworkPawnId,It->Combat->Snapshot.LifeGeneration,FVector2D(1,0));break;}
    // No damage/HP payload exists in the gameplay RPC schema.
    Trace(TEXT("ClientProbe"),GetWorld()->GetTimeSeconds(),Kind);
#endif
}
