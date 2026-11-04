#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "U01MotorPolicy.h"
#include "U01Character.generated.h"

class UCameraComponent;

enum class EU01MotorLock : uint8 { Control = 1, Interacting = 2, Defeated = 4 };

// Network saved moves/validation will be completed in F; the standalone motor is exercised in C.
UCLASS()
class ANIMEMMORPG_API UU01CharacterMovement : public UCharacterMovementComponent
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    void SetControlLocked(bool bLocked);
    void SetMotorLock(EU01MotorLock Reason, bool bEnabled);
    bool IsMotorLocked() const { return LockMask != 0; }
    uint8 GetLockMask() const { return LockMask; }
    void SetSprintRequested(bool bRequested) { bSprintRequested = bRequested && !IsMotorLocked(); }
    bool IsSprinting() const;
    virtual float GetMaxSpeed() const override;
    virtual void PerformMovement(float DeltaSeconds) override;
    virtual void StartFalling(int32 Iterations, float RemainingTime, float TimeTick, const FVector& Delta, const FVector& SubLocation) override;
    virtual void ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations) override;
    virtual void SetPostLandedPhysics(const FHitResult& Hit) override;
    void ObserveMovementMode(EMovementMode PreviousMode);
    bool TryJump(double Now, float DeltaSeconds);
    void PressJump(double Now) { if (!IsMotorLocked()) JumpWindow.Press(Now); }
    void ReleaseJump() { JumpWindow.Release(); }
    bool CanUseCoyote(double Now) const { return !IsMotorLocked() && JumpWindow.HasCoyote(Now); }
    bool HasBufferedJump(double Now) const { return JumpWindow.HasBuffer(Now); }
    double GetMotorTimeSeconds() const { return SimulationSeconds; }
    void ResetFixtureState();
private:
    uint8 LockMask = 0;
    bool bSprintRequested = false;
    bool bAttemptingJump = false;
    double FrameStartSeconds = 0;
    double SimulationSeconds = 0;
    float FrameDeltaSeconds = 0;
    TOptional<double> EventSeconds;
    AnimeMMORPG::U01::FJumpWindow JumpWindow;
};

UCLASS()
class ANIMEMMORPG_API AU01Character : public ACharacter
{
    GENERATED_BODY()
public:
    AU01Character(const FObjectInitializer& ObjectInitializer);
    virtual void Jump() override;
    virtual void StopJumping() override;
    virtual void CheckJumpInput(float DeltaTime) override;
    virtual bool CanJumpWhileFalling() const override;
    virtual void OnMovementModeChanged(EMovementMode PreviousMode, uint8 PreviousCustomMode = 0) override;
    bool ExecuteMotorJump(float DeltaSeconds);
    void ClearEngineJumpInput() { Super::StopJumping(); }
    UU01CharacterMovement* GetU01Movement() const;
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
