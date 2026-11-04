#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "U01AnimInstance.generated.h"

// Pose selection only. CharacterMovement remains the sole authority for capsule motion.
UCLASS(Transient, Blueprintable)
class ANIMEMMORPG_API UU01AnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UU01AnimInstance();
    virtual void NativeInitializeAnimation() override;
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;
    UPROPERTY(BlueprintReadOnly, Category="U01") float GroundSpeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="U01") float VerticalSpeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="U01") FVector Acceleration = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="U01") bool bGrounded = false;
    UPROPERTY(BlueprintReadOnly, Category="U01") bool bFalling = false;
    UPROPERTY(BlueprintReadOnly, Category="U01") bool bSprinting = false;
    // Idle=0, locomotion BlendSpace=1, jump ascent=2, falling=3, landing=4.
    UPROPERTY(BlueprintReadOnly, Category="U01") int32 PoseIndex = 0;
private:
    bool bPreviouslyFalling = false;
    float LandingRemaining = 0;
};
