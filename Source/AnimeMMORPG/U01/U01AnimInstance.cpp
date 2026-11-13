#include "U01AnimInstance.h"
#include "U01Character.h"
#include "U02/U02Presentation.h"
#include "GameFramework/GameStateBase.h"
#include "Engine/World.h"
#include "Animation/AnimMontage.h"
#include "UObject/ConstructorHelpers.h"

UU01AnimInstance::UU01AnimInstance()
{
    RootMotionMode = ERootMotionMode::IgnoreRootMotion;
    static ConstructorHelpers::FObjectFinder<UAnimMontage> QAsset(TEXT("/Game/AnimeMMORPG/U03/Animation/AM_U03_Q"));
    static ConstructorHelpers::FObjectFinder<UAnimMontage> EAsset(TEXT("/Game/AnimeMMORPG/U03/Animation/AM_U03_E"));
    QMontage=QAsset.Object;EMontage=EAsset.Object;
}
void UU01AnimInstance::NativeInitializeAnimation()
{
    Super::NativeInitializeAnimation();
    bPreviouslyFalling = false;
    LandingRemaining = 0;
    PoseIndex = 0;
    bAttackPresented=false;AttackBlendWeight=0;PresentedAction=PresentedLife=0;PresentedPawn.Invalidate();
}
void UU01AnimInstance::NativeUpdateAnimation(float Dt)
{
    Super::NativeUpdateAnimation(Dt);
    const auto* Character = Cast<AU01Character>(TryGetPawnOwner());
    if (!Character) return;
    const auto* Motor = Character->GetU01Movement();
    // Proxy simulation may extrapolate a full background frame beyond the latest
    // packet. Present the authoritative movement sample; never move the actor.
    const FVector PresentationVelocity=Character->GetLocalRole()==ROLE_SimulatedProxy
        ?Character->GetReplicatedMovement().LinearVelocity:Character->GetVelocity();
    GroundSpeed = PresentationVelocity.Size2D();
    VerticalSpeed = PresentationVelocity.Z;
    Acceleration = Motor->GetCurrentAcceleration();
    bGrounded = Motor->IsMovingOnGround();
    bFalling = Motor->IsFalling();
    bSprinting = Motor->IsSprinting();
    if (bPreviouslyFalling && bGrounded && GroundSpeed <= 3.f) LandingRemaining = .25f;
    else LandingRemaining = FMath::Max(0.f, LandingRemaining - Dt);
    // Presentation never delays movement: moving landings and movement begun
    // during a stationary landing immediately relinquish the landing pose.
    if (bFalling || !bGrounded || GroundSpeed > 3.f || LandingRemaining < 1.e-6f) LandingRemaining = 0;
    PoseIndex = bFalling ? (VerticalSpeed > 10.f ? 2 : 3)
        : (LandingRemaining > 0 ? 4 : (GroundSpeed > 3.f ? 1 : 0));
    bPreviouslyFalling = bFalling;
    if(Character->Combat)
    {
        const auto* State=GetWorld()->GetGameState();
        const double ServerNow=State ? State->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
        const auto& Snapshot=Character->Combat->GetCombatSnapshot();
        if(Snapshot.DodgeSequence && ServerNow>=Snapshot.DodgeStart && ServerNow<Snapshot.DodgeMotionEnd)
        {PoseIndex=1;GroundSpeed=1200;LandingRemaining=0;} // Existing locomotion blockout only; no motor/root-motion authority.
        PresentCombat(Character->Combat->GetCombatSnapshot(),ServerNow);
    }
}

void UU01AnimInstance::PresentCombat(const FU02RepCombatSnapshot& S,double Now)
{
    UAnimMontage* Selected=S.DefinitionId==3?QMontage.Get():S.DefinitionId==4?EMontage.Get():S.DefinitionId==1?Attack2Montage.Get():S.DefinitionId==2?Attack3Montage.Get():AttackMontage.Get();
    if(!Selected)return;
    // Stale snapshots/stops from an older life/action cannot stop a newer montage.
    if(PresentedPawn==S.PawnId && (S.LifeGeneration<PresentedLife ||
        (S.LifeGeneration==PresentedLife && S.ActionSequence && S.ActionSequence<PresentedAction)))return;
    const bool NewLife=PresentedPawn!=S.PawnId || PresentedLife!=S.LifeGeneration;
    const bool NewAction=NewLife || PresentedAction!=S.ActionSequence;
    const auto Sample=AnimeMMORPG::U02::SamplePresentation(S,Now);
    AttackBlendWeight=Sample.bPlay?1.f:0.f;
    if(NewLife || NewAction)
    {
        if(bAttackPresented)Montage_Stop(.04f,ActiveMontage);
        ActiveMontage=Selected;PresentedPawn=S.PawnId;PresentedLife=S.LifeGeneration;PresentedAction=S.ActionSequence;bAttackPresented=false;
    }
    if(!Sample.bPlay)
    {
        if(bAttackPresented)Montage_Stop(.04f,ActiveMontage);
        bAttackPresented=false;AttackPositionSeconds=0;return;
    }
    if(!bAttackPresented)
    {
        Montage_Play(ActiveMontage,1.f,EMontagePlayReturnType::MontageLength,float(Sample.PositionSeconds),false);
        bAttackPresented=true;
    }
    // Seek late snapshots/correct drift against authority time; not notify-driven.
    AttackPositionSeconds=Sample.PositionSeconds;
    if(FMath::Abs(Montage_GetPosition(ActiveMontage)-AttackPositionSeconds)>.025)
        Montage_SetPosition(ActiveMontage,float(AttackPositionSeconds));
}
