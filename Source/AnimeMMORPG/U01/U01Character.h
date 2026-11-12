#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "U01MotorPolicy.h"
#include "U01Character.generated.h"

class UCameraComponent;
class UStaticMeshComponent;
class UU02CombatComponent;
class UU02VitalComponent;

enum class EU01MotorLock : uint8 { Control = 1, Interacting = 2, Defeated = 4, Combat = 8 };

class FSavedMove_U01;
UCLASS()
class ANIMEMMORPG_API UU01CharacterMovement : public UCharacterMovementComponent
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual FNetworkPredictionData_Client* GetPredictionData_Client() const override;
    virtual void UpdateFromCompressedFlags(uint8 Flags) override;
    virtual bool ClientUpdatePositionAfterServerUpdate() override;
    int32 CorrectionCount=0;
    float ProbeSpeed=0;
    void SetControlLocked(bool bLocked);
    void SetMotorLock(EU01MotorLock Reason, bool bEnabled);
    bool IsMotorLocked() const { return GetLockMask() != 0; }
    uint8 GetLockMask() const { return LockMask | (bCombatAuthorityLocked ? uint8(EU01MotorLock::Combat) : 0); }
    void ApplyCombatAuthority(bool bLocked, bool bYawLocked, double YawDegrees);
    void SetSprintRequested(bool bRequested) { bSprintRequested = bRequested && !IsMotorLocked(); }
    bool IsSprinting() const;
    virtual float GetMaxSpeed() const override;
    virtual void PerformMovement(float DeltaSeconds) override;
    virtual void PhysicsRotation(float DeltaSeconds) override;
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
    // Authority-only swept walking preview. Deferred transforms/overlaps are reverted;
    // only CommitDodge moves the actor, at the world resolver's selected event time.
    void PlanDodge(double Begin,double End,FVector Direction,uint64 Life,uint64 Sequence,const TArray<AActor*>& BatchPawns={});
    void CommitDodge(double At);
    bool HasDodgePlan() const { return bDodgePlan; }
    FVector DodgeOffsetAt(double At) const;
    FVector DodgePlanOrigin() const { return PlanOrigin; }
    FVector DodgePositionAt(double At) const;
    double NextDodgePathBoundary(double At,double Through) const;
    bool ClipDodgePath(double At);
    bool CanClipDodgePath(double At) const { return bDodgePlan&&At<PlanClip; }
    void InvalidateDodgePath() { bDodgePlan=false; }
    bool DodgeLostGround() const { return bDodgeLostGround; }
    bool DodgeBlocked() const { return bDodgeBlocked; }
    bool IsDodgePreview() const { return bPreviewDodge; }
    virtual void HandleImpact(const FHitResult& Hit,float TimeSlice=0.f,const FVector& MoveDelta=FVector::ZeroVector) override;
    virtual bool MoveUpdatedComponentImpl(const FVector& Delta,const FQuat& Rotation,bool bSweep,FHitResult* Hit=nullptr,ETeleportType Teleport=ETeleportType::None) override;
private:
    friend class FSavedMove_U01;
    bool bNetworkJumpHeld=false;
    uint8 LockMask = 0;
    // Never restored from a saved move or client compressed flag.
    bool bCombatAuthorityLocked = false, bCombatYawLocked = false;
    double CombatYawDegrees = 0;
    bool bSprintRequested = false;
    bool bAttemptingJump = false;
    double FrameStartSeconds = 0;
    double SimulationSeconds = 0;
    float FrameDeltaSeconds = 0;
    TOptional<double> EventSeconds;
    AnimeMMORPG::U01::FJumpWindow JumpWindow;
    bool bDodgePlan=false,bPreviewDodge=false,bDodgeLostGround=false,bDodgeBlocked=false;
    double PlanBegin=0,PlanEnd=0,PlanCommitted=0;
    FVector PlanOrigin=FVector::ZeroVector,PlanDestination=FVector::ZeroVector,PlanDirection=FVector::ZeroVector;
    uint64 PlanLife=0,PlanSequence=0;
    struct FDodgeKnot {double At;FVector Position;};
    TArray<FDodgeKnot> DodgePath;
    TArray<FVector> NativeDodgePath;
    FFindFloorResult PlanFloor;
    double PlanClip=TNumericLimits<double>::Max();
    TArray<TWeakObjectPtr<AActor>> PlanBatch;
    void TrimNativeDodgePath(FVector Position);
    void WalkDodge(float Seconds,FVector Direction);
};

UCLASS()
class ANIMEMMORPG_API AU01Character : public ACharacter
{
    GENERATED_BODY()
public:
    AU01Character(const FObjectInitializer& ObjectInitializer);
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    UPROPERTY(Replicated) FGuid NetworkPawnId;
    UPROPERTY(Replicated) bool bNetSprinting=false;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U02") TObjectPtr<UU02CombatComponent> Combat;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U02") TObjectPtr<UU02VitalComponent> Vital;
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
    void SetDefaultShoulder(bool bRight,bool bImmediate=false);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U01|Camera")
    TObjectPtr<UCameraComponent> FollowCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U01|Blockout")
    TObjectPtr<USceneComponent> SwordRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U01|Blockout")
    TObjectPtr<UStaticMeshComponent> SwordBlade;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U01|Blockout")
    TObjectPtr<UStaticMeshComponent> SwordGuard;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="U01|Blockout")
    TObjectPtr<UStaticMeshComponent> SwordGrip;

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
