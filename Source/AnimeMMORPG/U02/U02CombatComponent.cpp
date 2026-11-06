#include "U02CombatComponent.h"
#include "U02CollisionWorld.h"
#include "U01/U01Character.h"
#include "U01/U01PlayerController.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
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

DEFINE_LOG_CATEGORY_STATIC(LogU02Combat, Log, All);
using namespace AnimeMMORPG::U02;

UU02CombatComponent::UU02CombatComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PrePhysics;
    SetIsReplicatedByDefault(true);
}
AU01Character* UU02CombatComponent::Character() const { return Cast<AU01Character>(GetOwner()); }
void UU02CombatComponent::BeginPlay()
{
    Super::BeginPlay();
    auto* C = Character();
    if (!C || !GetWorld() || (GetWorld()->WorldType != EWorldType::Game && GetWorld()->WorldType != EWorldType::PIE))
    { SetComponentTickEnabled(false); return; }
    C->GetU01Movement()->AddTickPrerequisiteComponent(this);
    TArray<UPrimitiveComponent*> PresentationAndBody;C->GetComponents(PresentationAndBody);
    for(auto* P:PresentationAndBody)P->SetCollisionResponseToChannel(ECC_GameTraceChannel2,ECR_Ignore);
    // C owns a separate graph; keep the accepted U01 AnimBP bytes untouched.
    if(C->GetMesh()->GetSkeletalMeshAsset())
    {
        auto* PresentationClass=LoadClass<UAnimInstance>(nullptr,TEXT("/Game/AnimeMMORPG/U02/Animation/ABP_U02.ABP_U02_C"));
        if(PresentationClass)C->GetMesh()->SetAnimInstanceClass(PresentationClass);
    }
    if (C->HasAuthority())
    {
        check(C->NetworkPawnId.IsValid());
        check(FAttack1Definition().IsValid());
        Model = MakeUnique<FActionModel>(FLifeId{C->NetworkPawnId,1});
        Publish(GetWorld()->GetTimeSeconds(),true);
        GetWorld()->GetSubsystem<UU02CollisionWorld>()->RegisterCombat(this);
    }
}
void UU02CombatComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Model) CancelAt(ECancel::Removed,GetWorld()->GetTimeSeconds());
    if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())W->UnregisterCombat(this);
    OnActiveInterval.Clear();
    BeforeActionMutation.Unbind();
    Super::EndPlay(Reason);
}
void UU02CombatComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UU02CombatComponent,Snapshot);
}
void UU02CombatComponent::SubmitAttackIntent(uint64 Sequence, double LocalInputSeconds, double Yaw)
{
    if (!Character()) return;
    if (Character()->HasAuthority()) HandleAttack(Sequence,LocalInputSeconds,Yaw,GetWorld()->GetTimeSeconds());
    else ServerAttack(Sequence,LocalInputSeconds,Yaw);
}
void UU02CombatComponent::ServerAttack_Implementation(uint64 Sequence, double LocalInputSeconds, double Yaw)
{
    HandleAttack(Sequence,LocalInputSeconds,Yaw,GetWorld()->GetTimeSeconds());
}
void UU02CombatComponent::SetControlPlaying(bool bPlaying)
{
    if (!Character()) return;
    if (Character()->HasAuthority()) bAuthorityPlaying = bPlaying;
    else ServerControlPlaying(bPlaying);
}
void UU02CombatComponent::ServerControlPlaying_Implementation(bool bPlaying) { bAuthorityPlaying = bPlaying; }
void UU02CombatComponent::ServerAim_Implementation(double Yaw)
{
    if (!Model || !FMath::IsFinite(Yaw)) return;
    const double Now = GetWorld()->GetTimeSeconds();
    // Drain first: aim received at/after entry can never retroactively turn active.
    AdvanceAuthority(Now);
    if (Model->UpdateAim(Now,Yaw)) { StartupTurn.Retarget(Now,Yaw); Publish(Now); }
}
void UU02CombatComponent::HandleAttack(uint64 Sequence, double LocalInputSeconds, double Yaw, double Now)
{
    if (!Model || !Character()->HasAuthority()) return;
    // Mandatory adapter invariant: deliver the OLD interval before overwriting action.
    if (!AdvanceAuthority(Now)) return;
    BeforeActionMutation.ExecuteIfBound(Now);
    auto* M = Character()->GetU01Movement();
    FAttackContext Context;
    Context.bPlaying = bAuthorityPlaying && !(M->GetLockMask() & uint8(EU01MotorLock::Control));
    if (const auto* PC = Cast<AU01PlayerController>(Character()->GetController()))
        Context.bPlaying &= PC->ControlState == EU01ControlState::Playing;
    Context.bGrounded = M->IsMovingOnGround();
    Context.bInteracting = (M->GetLockMask() & uint8(EU01MotorLock::Interacting)) != 0;
    Context.bDefeated = (M->GetLockMask() & uint8(EU01MotorLock::Defeated)) != 0;
    LastCommand = Sequence;
    // The client clock is diagnostic only; invalid local stamps are discarded, never backdated.
    LastReject = Model->SubmitAttackIntent(Sequence,Now,Yaw,Context);
    if (LastReject == EReject::None)
    {
        ++AcceptedCount;
        StartupTurn.Begin(Character()->GetActorRotation().Yaw,Yaw,Now,Now+.16);
    }
    else ++RejectedCount;
    Publish(Now,true);
    Trace(LastReject == EReject::None ? TEXT("Accepted") : TEXT("Rejected"),Now,
        FString::Printf(TEXT("command=%llu reason=%d localInput=%.17g receive=%.17g"),Sequence,int32(LastReject),
            FMath::IsFinite(LocalInputSeconds) ? LocalInputSeconds : -1.,Now));
}
bool UU02CombatComponent::AdvanceAuthority(double Now, bool bExcludeEnd)
{
    if (!Model) return false;
    const auto Before = Model->GetCombatSnapshot(Now);
    const double Previous = Before.LastAdvanceSeconds;
    FActiveSlice Slice;
    if (!Model->AdvanceAction(Now,Slice)) return false;
    if (bExcludeEnd && Slice.bEvaluate && Slice.EndSeconds==Now)
    {
        Slice.bEndExclusive=true;
        if(Slice.BeginSeconds==Slice.EndSeconds)Slice.bEvaluate=false;
    }
    if (Before.Action.Sequence && Before.Phase != EPhase::Cancelled)
    {
        const double Boundaries[] = {Before.ActiveStartSeconds,Before.ActiveEndSeconds,Before.EndSeconds};
        const TCHAR* Names[] = {TEXT("Active"),TEXT("Recovery"),TEXT("Finished")};
        for (int32 I=0;I<3;++I) if (Previous < Boundaries[I] && Now >= Boundaries[I]) Trace(Names[I],Boundaries[I]);
    }
    // Complete the gameplay orientation boundary BEFORE handing any active interval to D.
    // This also holds when a single update skips the entire active window.
    if (Before.Action.Sequence && Before.Phase!=EPhase::Cancelled && Previous<Before.EndSeconds && Now>=Before.StartSeconds)
    {
        const double BodyYaw=StartupTurn.Sample(Now);
        Character()->GetU01Movement()->ApplyCombatAuthority(true,Now>=Before.ActiveStartSeconds,BodyYaw);
        Character()->SetActorRotation(FRotator(0,BodyYaw,0));
    }
    if (Slice.bEvaluate)
    {
        LastInterval = Slice; ++IntervalCount;
        Trace(TEXT("ActiveInterval"),Slice.BeginSeconds,
            FString::Printf(TEXT("begin=%.17g end=%.17g beginAlpha=%.17g endAlpha=%.17g endExclusive=%d"),
                Slice.BeginSeconds,Slice.EndSeconds,Slice.BeginAlpha,Slice.EndAlpha,Slice.bEndExclusive));
        OnActiveInterval.Broadcast(Before.Action,Slice); // D's collector must not apply damage in this callback.
    }
    Publish(Now);
    return true;
}
bool UU02CombatComponent::CancelAt(ECancel Reason, double Now)
{
    if (!Model || !Character()->HasAuthority()) return false;
    const EPhase Phase=Model->PhaseAt(Now);
    const bool WillCancel=Reason!=ECancel::Menu && Reason!=ECancel::Focus && Phase!=EPhase::Idle && Phase!=EPhase::Finished && Phase!=EPhase::Cancelled
        && ((Reason!=ECancel::Dodge && Reason!=ECancel::Guard) || Phase==EPhase::Startup);
    if(!AdvanceAuthority(Now,WillCancel))return false;
    BeforeActionMutation.ExecuteIfBound(Now);
    const bool Cancelled = Model->CancelAction(Reason,Now);
    if(Cancelled&&(Reason==ECancel::Death||Reason==ECancel::Removed))GetWorld()->GetSubsystem<UU02CollisionWorld>()->MarkDead(Model->GetLife());
    Publish(Now,true);
    Trace(Cancelled ? TEXT("Cancelled") : TEXT("CancelRejected"),Now,FString::Printf(TEXT("reason=%d"),int32(Reason)));
    return Cancelled;
}
bool UU02CombatComponent::CancelAction(ECancel Reason) { return CancelAt(Reason,GetWorld()->GetTimeSeconds()); }
void UU02CombatComponent::LostGround()
{
    if (Snapshot.bLocked && Model) CancelAt(ECancel::LostGround,GetWorld()->GetTimeSeconds());
}
bool UU02CombatComponent::ResetLabCombat()
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if (!Model || !Character()->HasAuthority()) return false;
    const double Now = GetWorld()->GetTimeSeconds();
    if (!AdvanceAuthority(Now,true)) return false;
    BeforeActionMutation.ExecuteIfBound(Now);
    if (!Model->ResetLabCombat(Now)) return false;
    Publish(Now,true); Trace(TEXT("Reset"),Now); return true;
#endif
}
void UU02CombatComponent::Publish(double Now, bool bForce)
{
    if (!Model) return;
    const auto S = Model->GetCombatSnapshot(Now);
    const bool Changed = Snapshot.Phase != uint8(S.Phase) || Snapshot.ActionSequence != S.Action.Sequence
        || Snapshot.LifeGeneration != S.Life.Generation || Snapshot.AimYawDegrees != S.AimYawDegrees;
    if (!Changed && !bForce) return;
    Snapshot.PawnId = S.Life.Pawn; Snapshot.LifeGeneration = S.Life.Generation;
    Snapshot.ActionSequence = S.Action.Sequence; Snapshot.Phase = uint8(S.Phase);
    Snapshot.StartSeconds = S.StartSeconds; Snapshot.ServerSeconds = Now; Snapshot.AimYawDegrees = S.AimYawDegrees;
    Snapshot.TurnFromYaw=StartupTurn.FromYaw; Snapshot.TurnStartSeconds=StartupTurn.SegmentStart;
    Snapshot.bLocked = S.bCombatLocked; Snapshot.bYawLocked = S.bYawLocked; ++Snapshot.Revision;
    if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())W->ObserveCombat(this);
    ApplyMotorSnapshot(); Character()->ForceNetUpdate();
}
void UU02CombatComponent::ApplyMotorSnapshot()
{
    if (auto* C=Character())
    {
        const auto* GS=GetWorld()->GetGameState();
        const double Now=C->HasAuthority()?Snapshot.ServerSeconds:(GS?GS->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds());
        FStartupTurn Turn;Turn.Begin(Snapshot.TurnFromYaw,Snapshot.AimYawDegrees,Snapshot.TurnStartSeconds,Snapshot.StartSeconds+.16);
        const double BodyYaw=Turn.Sample(Now);
        C->GetU01Movement()->ApplyCombatAuthority(Snapshot.bLocked,Snapshot.bYawLocked,BodyYaw);
        // Simulated proxies do not run PhysicsRotation. Sample the action trajectory
        // explicitly there too; hit direction remains exclusively server-owned.
        if (!C->HasAuthority() && Snapshot.bLocked) C->SetActorRotation(FRotator(0,BodyYaw,0));
    }
}
void UU02CombatComponent::OnRep_Snapshot() { ApplyMotorSnapshot(); }
void UU02CombatComponent::TickComponent(float Dt, ELevelTick Type, FActorComponentTickFunction* Function)
{
    Super::TickComponent(Dt,Type,Function);
    const double Now=GetWorld()->GetTimeSeconds();
    auto* C=Character(); if (!C) return;
    if (Model)
    {
        AdvanceAuthority(Now);
        // Remote aim arrives through ServerAim. A stale replicated controller rotation must not overwrite it.
        if (C->IsLocallyControlled() && C->GetController() && Model->UpdateAim(Now,C->GetControlRotation().Yaw))
        { StartupTurn.Retarget(Now,C->GetControlRotation().Yaw); Publish(Now); }
    }
    else if (C->IsLocallyControlled() && Snapshot.Phase==uint8(EPhase::Startup) && Now-LastAimSend>=1./30)
    { ServerAim(C->GetControlRotation().Yaw); LastAimSend=Now; }
    if (!Model) ApplyMotorSnapshot();
    if (C->IsLocallyControlled() && GEngine && FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))
    {
        const TCHAR* Phases[]={TEXT("Ready"),TEXT("Startup"),TEXT("Active"),TEXT("Recovery"),TEXT("Ready"),TEXT("Cancelled")};
        GEngine->AddOnScreenDebugMessage(uint64(C->GetUniqueID())+200000,.1f,FColor::Cyan,
            FString::Printf(TEXT("U02 combat lab | LMB | %s | action %llu | lock %d"),Phases[FMath::Min<int32>(Snapshot.Phase,5)],Snapshot.ActionSequence,Snapshot.bLocked));
    }
}
TSharedRef<FJsonObject> UU02CombatComponent::GetDiagnostics() const
{
    auto J=MakeShared<FJsonObject>();
    J->SetStringField(TEXT("pawnId"),Snapshot.PawnId.ToString());
    J->SetStringField(TEXT("lifeId"),FString::Printf(TEXT("%s:%llu"),*Snapshot.PawnId.ToString(),Snapshot.LifeGeneration));
    J->SetStringField(TEXT("actionId"),FString::Printf(TEXT("%s:%llu:%llu"),*Snapshot.PawnId.ToString(),Snapshot.LifeGeneration,Snapshot.ActionSequence));
    J->SetStringField(TEXT("commandId"),FString::Printf(TEXT("%llu"),LastCommand));
    J->SetNumberField(TEXT("life"),Snapshot.LifeGeneration); J->SetNumberField(TEXT("action"),Snapshot.ActionSequence);
    J->SetNumberField(TEXT("phase"),Snapshot.Phase); J->SetNumberField(TEXT("start"),Snapshot.StartSeconds);
    J->SetNumberField(TEXT("activeStart"),Snapshot.StartSeconds+.16); J->SetNumberField(TEXT("activeEnd"),Snapshot.StartSeconds+.22);
    J->SetNumberField(TEXT("end"),Snapshot.StartSeconds+.4); J->SetNumberField(TEXT("serverSnapshotSeconds"),Snapshot.ServerSeconds);
    J->SetNumberField(TEXT("gameplayBodyYaw"),Character()?Character()->GetActorRotation().Yaw:0.);
    J->SetNumberField(TEXT("meshWorldYaw"),Character()?Character()->GetMesh()->GetComponentRotation().Yaw:0.);
    J->SetNumberField(TEXT("aimYaw"),Snapshot.AimYawDegrees);
    J->SetNumberField(TEXT("turnFromYaw"),Snapshot.TurnFromYaw);
    J->SetNumberField(TEXT("turnStart"),Snapshot.TurnStartSeconds);
    J->SetNumberField(TEXT("actionSeconds"),GetWorld()->GetTimeSeconds()-Snapshot.StartSeconds);
    J->SetNumberField(TEXT("yaw"),Snapshot.AimYawDegrees); J->SetBoolField(TEXT("locked"),Snapshot.bLocked);
    J->SetBoolField(TEXT("yawLocked"),Snapshot.bYawLocked); J->SetNumberField(TEXT("accepted"),AcceptedCount);
    J->SetNumberField(TEXT("rejected"),RejectedCount); J->SetNumberField(TEXT("lastReject"),uint8(LastReject));
    J->SetNumberField(TEXT("command"),LastCommand); J->SetNumberField(TEXT("intervals"),IntervalCount);
    J->SetNumberField(TEXT("lastSliceBegin"),LastInterval.BeginSeconds); J->SetNumberField(TEXT("lastSliceEnd"),LastInterval.EndSeconds);
    if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())
    {J->SetNumberField(TEXT("geometryConfirmed"),W->Confirmed.Num());J->SetNumberField(TEXT("geometryQueries"),W->Queries);J->SetNumberField(TEXT("geometryBlocked"),W->Blocked);}
    return J;
}
void UU02CombatComponent::Trace(const TCHAR* Event, double GameplaySeconds, const FString& Detail) const
{
    auto J=GetDiagnostics(); const auto* C=Character();
    if(Model)J->SetNumberField(TEXT("phase"),uint8(Model->PhaseAt(GameplaySeconds)));
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
