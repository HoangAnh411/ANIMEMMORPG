#include "U01AnimInstance.h"
#include "U01Character.h"

UU01AnimInstance::UU01AnimInstance()
{
    RootMotionMode = ERootMotionMode::IgnoreRootMotion;
}
void UU01AnimInstance::NativeInitializeAnimation()
{
    Super::NativeInitializeAnimation();
    bPreviouslyFalling = false;
    LandingRemaining = 0;
    PoseIndex = 0;
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
}
