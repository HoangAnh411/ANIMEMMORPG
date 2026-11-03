#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "U01Character.generated.h"

class UCameraComponent;

// U01-B only supplies the control lock. Sprint/coyote/buffer and network moves belong to C/F.
UCLASS()
class ANIMEMMORPG_API UU01CharacterMovement : public UCharacterMovementComponent
{
    GENERATED_BODY()
public:
    void SetControlLocked(bool bLocked);
    virtual void PerformMovement(float DeltaSeconds) override;
private:
    bool bControlLocked = false;
};

UCLASS()
class ANIMEMMORPG_API AU01Character : public ACharacter
{
    GENERATED_BODY()
public:
    AU01Character(const FObjectInitializer& ObjectInitializer);
    virtual void CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult) override;
    void SetControlLocked(bool bLocked);
    void ToggleShoulder();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U01|Camera")
    TObjectPtr<UCameraComponent> FollowCamera;

    FVector CameraPivot = FVector::ZeroVector;
    FVector DesiredCamera = FVector::ZeroVector;
    bool bCameraHit = false;
    bool bOwnerMeshHidden = false;
    float CameraDistance = 350.f;
    float ShoulderOffset = 45.f;
private:
    float ShoulderStart = 45.f;
    float ShoulderTarget = 45.f;
    float ShoulderElapsed = .15f;
    bool bCameraInitialized = false;
};
