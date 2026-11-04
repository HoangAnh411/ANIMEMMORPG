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
    GroundSpeed = Character->GetVelocity().Size2D();
    VerticalSpeed = Character->GetVelocity().Z;
    Acceleration = Motor->GetCurrentAcceleration();
    bGrounded = Motor->IsMovingOnGround();
    bFalling = Motor->IsFalling();
    bSprinting = Motor->IsSprinting();
    if (bPreviouslyFalling && bGrounded) LandingRemaining = .25f;
    else LandingRemaining = FMath::Max(0.f, LandingRemaining - Dt);
    if (bFalling) LandingRemaining = 0;
    PoseIndex = bFalling ? (VerticalSpeed > 10.f ? 2 : 3)
        : (LandingRemaining > 0 ? 4 : (GroundSpeed > 3.f ? 1 : 0));
    bPreviouslyFalling = bFalling;
}
