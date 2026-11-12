#include "U01Character.h"
#include "U01ControlPolicy.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02HurtboxComponent.h"

void UU01CharacterMovement::BeginPlay()
{
    Super::BeginPlay();
    bServerAcceptClientAuthoritativePosition=false;
    bIgnoreClientMovementErrorChecksAndCorrection=false;
    SimulationSeconds = GetWorld()->GetTimeSeconds();
    JumpWindow.ResetSession();
}

void UU01CharacterMovement::SetControlLocked(bool bLocked)
{
    SetMotorLock(EU01MotorLock::Control, bLocked);
}

void UU01CharacterMovement::SetMotorLock(EU01MotorLock Reason, bool bEnabled)
{
    if (Reason == EU01MotorLock::Combat) return; // Owned by combat snapshot, not generic/client flags.
    auto* C = Cast<AU01Character>(CharacterOwner);
    if (!bEnabled && Reason==EU01MotorLock::Defeated && C && C->Vital && C->Vital->GetSnapshot().bDead) return;
    if (bEnabled && Reason == EU01MotorLock::Interacting && bCombatAuthorityLocked) return;
    if(bEnabled && (Reason==EU01MotorLock::Control||Reason==EU01MotorLock::Interacting) && C && C->Combat)C->Combat->DiscardPendingInputs();
    if (bEnabled && Reason == EU01MotorLock::Defeated && C && C->Combat) C->Combat->CancelAction(AnimeMMORPG::U02::ECancel::Death);
    const uint8 Bit = static_cast<uint8>(Reason);
    if (bEnabled) LockMask |= Bit;
    else LockMask &= ~Bit;
    if (IsMotorLocked())
    {
        ConsumeInputVector();
        Velocity.X = Velocity.Y = 0;
        Acceleration = FVector::ZeroVector;
        bSprintRequested = false;
        JumpWindow.ClearInput();
        if (auto* MotorPawn = Cast<AU01Character>(CharacterOwner)) MotorPawn->ClearEngineJumpInput();
    }
}

void UU01CharacterMovement::ApplyCombatAuthority(bool bLocked, bool bYawLocked, double YawDegrees)
{
    bCombatAuthorityLocked = bLocked;
    bCombatYawLocked = bYawLocked;
    CombatYawDegrees = YawDegrees;
    if (bLocked)
    {
        ConsumeInputVector(); Velocity.X = Velocity.Y = 0; Acceleration = FVector::ZeroVector;
        bSprintRequested = false; JumpWindow.ClearInput();
        if (auto* C = Cast<AU01Character>(CharacterOwner)) C->ClearEngineJumpInput();
    }
}

void UU01CharacterMovement::PhysicsRotation(float DeltaSeconds)
{
    if (bCombatAuthorityLocked)
    {
        // Authoritative/snapshot yaw also wins during movement replay.
        if (UpdatedComponent) MoveUpdatedComponent(FVector::ZeroVector,FRotator(0,CombatYawDegrees,0).Quaternion(),true);
        return;
    }
    Super::PhysicsRotation(DeltaSeconds);
}

bool UU01CharacterMovement::IsSprinting() const
{
    if(CharacterOwner&&CharacterOwner->GetLocalRole()==ROLE_SimulatedProxy)return CastChecked<AU01Character>(CharacterOwner)->bNetSprinting;
    return !IsMotorLocked() && bSprintRequested && Acceleration.SizeSquared2D() > UE_SMALL_NUMBER;
}

float UU01CharacterMovement::GetMaxSpeed() const
{
#if !UE_BUILD_SHIPPING
    if(CharacterOwner&&CharacterOwner->GetLocalRole()==ROLE_AutonomousProxy&&ProbeSpeed>0)return ProbeSpeed;
#endif
    return IsMotorLocked() ? 0.f : (IsSprinting() ? 700.f : 500.f);
}

void UU01CharacterMovement::PerformMovement(float DeltaSeconds)
{
    // Inputs use the last completed movement time. Substep contacts are timestamped
    // within this interval, rather than at the frame-end world time twice.
    FrameStartSeconds = SimulationSeconds;
    FrameDeltaSeconds = DeltaSeconds;
    if (IsMotorLocked())
    {
        Acceleration = FVector::ZeroVector;
        Velocity.X = Velocity.Y = 0;
    }
    const auto* Combat=Cast<AU01Character>(CharacterOwner)?CastChecked<AU01Character>(CharacterOwner)->Combat.Get():nullptr;
    const bool WorldOwnsDodge=CharacterOwner&&CharacterOwner->HasAuthority()&&HasDodgePlan()&&IsMovingOnGround()&&Combat
        &&Combat->GetCombatSnapshot().ServerSeconds<Combat->GetCombatSnapshot().DodgeMotionEnd;
    // During a retained walking path, another CMC solve would move the actor
    // away from the resolver's trajectory. Falling still uses native gravity.
    if(!WorldOwnsDodge)Super::PerformMovement(DeltaSeconds);
    if (bCombatAuthorityLocked) PhysicsRotation(DeltaSeconds);
    SimulationSeconds = FrameStartSeconds + DeltaSeconds;
    if(CharacterOwner&&CharacterOwner->HasAuthority())CastChecked<AU01Character>(CharacterOwner)->bNetSprinting=IsSprinting();
}

void UU01CharacterMovement::StartFalling(int32 Iterations, float RemainingTime, float TimeTick, const FVector& Delta, const FVector& SubLocation)
{
    const double DesiredDistance = Delta.Size();
    const double ActualDistance = ProjectToGravityFloor(UpdatedComponent->GetComponentLocation() - SubLocation).Size();
    const double UsedFraction = DesiredDistance > UE_KINDA_SMALL_NUMBER ? FMath::Min(1., ActualDistance / DesiredDistance) : 0.;
    const double UsedSeconds = FMath::Clamp(double(FrameDeltaSeconds - RemainingTime - TimeTick) + TimeTick * UsedFraction, 0., double(FrameDeltaSeconds));
    TGuardValue<TOptional<double>> EventScope(EventSeconds, FrameStartSeconds + UsedSeconds);
    Super::StartFalling(Iterations, RemainingTime, TimeTick, Delta, SubLocation);
}

void UU01CharacterMovement::ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations)
{
    TGuardValue<TOptional<double>> EventScope(EventSeconds, FrameStartSeconds + FMath::Clamp(double(FrameDeltaSeconds - RemainingTime), 0., double(FrameDeltaSeconds)));
    Super::ProcessLanded(Hit, RemainingTime, Iterations);
}

void UU01CharacterMovement::SetPostLandedPhysics(const FHitResult& Hit)
{
    Super::SetPostLandedPhysics(Hit);
    // Consume in the landing substep, before the remaining part of this frame is simulated.
    if (IsMovingOnGround()) TryJump(EventSeconds.Get(SimulationSeconds), FrameDeltaSeconds);
}

void UU01CharacterMovement::ObserveMovementMode(EMovementMode PreviousMode)
{
    if (IsMovingOnGround()) { JumpWindow.Land(); if(auto* C=Cast<AU01Character>(CharacterOwner); C&&C->Combat)C->Combat->Landed(); }
    else if ((PreviousMode == MOVE_Walking || PreviousMode == MOVE_NavWalking) && IsFalling())
    {
        JumpWindow.LeaveGround(EventSeconds.Get(SimulationSeconds), bAttemptingJump);
        if (auto* C=Cast<AU01Character>(CharacterOwner); C && C->Combat) C->Combat->LostGround();
    }
}

bool UU01CharacterMovement::TryJump(double Now, float DeltaSeconds)
{
    const bool bGrounded = IsMovingOnGround();
    if (IsMotorLocked() || !JumpWindow.CanConsume(Now, bGrounded)) return false;
    auto* MotorPawn = Cast<AU01Character>(CharacterOwner);
    if (!MotorPawn) return false;
    const float GravityMagnitude = FMath::Abs(GetGravityZ());
    if (GravityMagnitude <= UE_SMALL_NUMBER) return false;
    JumpZVelocity = FMath::Sqrt(2.f * GravityMagnitude * 120.f);
    TGuardValue<bool> JumpScope(bAttemptingJump, true);
    if (!MotorPawn->ExecuteMotorJump(DeltaSeconds)) return false;
    JumpWindow.Consume(Now, bGrounded);
    return true;
}

void UU01CharacterMovement::ResetFixtureState()
{
    if (auto* C=Cast<AU01Character>(CharacterOwner); C && C->Combat) C->Combat->ResetLabCombat();
    LockMask &= static_cast<uint8>(EU01MotorLock::Control);
    // A failed/non-authority lab reset cannot bypass actual vital death.
    if(const auto* C=Cast<AU01Character>(CharacterOwner);C&&C->Vital&&C->Vital->GetSnapshot().bDead)
        LockMask |= static_cast<uint8>(EU01MotorLock::Defeated);
    bSprintRequested = false;
    JumpWindow.ResetSession();
    StopMovementImmediately();
    ConsumeInputVector();
    EventSeconds.Reset();
}

AU01Character::AU01Character(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer.SetDefaultSubobjectClass<UU01CharacterMovement>(ACharacter::CharacterMovementComponentName))
{
    GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);
    bUseControllerRotationPitch = bUseControllerRotationYaw = bUseControllerRotationRoll = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 500, 0);
    GetCharacterMovement()->MaxWalkSpeed = 500.f;
    GetCharacterMovement()->JumpZVelocity = FMath::Sqrt(2.f * 980.f * 120.f); // Recomputed from actual gravity at takeoff.
    GetCharacterMovement()->SetWalkableFloorAngle(45.f);
    GetCharacterMovement()->MaxStepHeight = 45.f;
    GetCharacterMovement()->AirControl = .35f;
    JumpMaxCount = 1;
    JumpMaxHoldTime = 0;
    Vital = CreateDefaultSubobject<UU02VitalComponent>(TEXT("U02Vital"));
    Combat = CreateDefaultSubobject<UU02CombatComponent>(TEXT("U02Combat"));
    auto* BodyHurt=CreateDefaultSubobject<UU02HurtboxComponent>(TEXT("U02BodyHurtbox"));
    BodyHurt->SetupAttachment(RootComponent);BodyHurt->SetRelativeLocation(FVector(0,0,-26));BodyHurt->InitSphereRadius(35);BodyHurt->StableHurtboxId=1;
    auto* HeadHurt=CreateDefaultSubobject<UU02HurtboxComponent>(TEXT("U02HeadHurtbox"));
    HeadHurt->SetupAttachment(RootComponent);HeadHurt->SetRelativeLocation(FVector(0,0,49));HeadHurt->InitSphereRadius(20);HeadHurt->StableHurtboxId=2;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("U01Camera"));
    FollowCamera->SetupAttachment(RootComponent);
    FollowCamera->bUsePawnControlRotation = false;
    FollowCamera->FieldOfView = 90;
    SwordRoot = CreateDefaultSubobject<USceneComponent>(TEXT("U01SwordRoot"));
    SwordRoot->SetupAttachment(GetMesh(), TEXT("U01_Sword_R"));
    SwordBlade = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("U01SwordBlade"));
    SwordGuard = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("U01SwordGuard"));
    SwordGrip = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("U01SwordGrip"));
    for (auto* Part : {SwordBlade.Get(), SwordGuard.Get(), SwordGrip.Get()})
    {
        Part->SetupAttachment(SwordRoot);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetCanEverAffectNavigation(false);
        Part->SetCastShadow(true);
    }
    SwordGrip->SetRelativeScale3D(FVector(.18,.03,.03));
    SwordGuard->SetRelativeLocation(FVector(10,0,0));
    SwordGuard->SetRelativeScale3D(FVector(.04,.18,.04));
    SwordBlade->SetRelativeLocation(FVector(56,0,0));
    SwordBlade->SetRelativeScale3D(FVector(.88,.06,.025));
}

void AU01Character::SetControlLocked(bool bLocked)
{
    GetU01Movement()->SetControlLocked(bLocked);
    if (bLocked) ConsumeMovementInputVector();
}

UU01CharacterMovement* AU01Character::GetU01Movement() const { return CastChecked<UU01CharacterMovement>(GetCharacterMovement()); }
void AU01Character::Jump() { GetU01Movement()->PressJump(GetU01Movement()->GetMotorTimeSeconds()); }
void AU01Character::StopJumping() { GetU01Movement()->ReleaseJump(); Super::StopJumping(); }
void AU01Character::CheckJumpInput(float DeltaTime) { GetU01Movement()->TryJump(GetU01Movement()->GetMotorTimeSeconds(), DeltaTime); }
bool AU01Character::CanJumpWhileFalling() const { return GetU01Movement()->CanUseCoyote(GetU01Movement()->GetMotorTimeSeconds()); }
void AU01Character::OnMovementModeChanged(EMovementMode PreviousMode, uint8 PreviousCustomMode)
{
    Super::OnMovementModeChanged(PreviousMode, PreviousCustomMode);
    GetU01Movement()->ObserveMovementMode(PreviousMode);
}
bool AU01Character::ExecuteMotorJump(float DeltaSeconds)
{
    const int32 PreviousCount = JumpCurrentCount;
    bPressedJump = true;
    Super::CheckJumpInput(DeltaSeconds);
    bPressedJump = false;
    return JumpCurrentCount > PreviousCount && GetCharacterMovement()->IsFalling();
}

void AU01Character::ToggleShoulder()
{
    ShoulderStart = ShoulderOffset;
    ShoulderTarget = -ShoulderTarget;
    ShoulderElapsed = 0;
}

void AU01Character::SetDefaultShoulder(bool bRight,bool bImmediate)
{
    ShoulderStart=ShoulderOffset;ShoulderTarget=bRight?45.f:-45.f;ShoulderElapsed=0;
    if(bImmediate){ShoulderStart=ShoulderOffset=ShoulderTarget;ShoulderElapsed=.15f;}
}

void AU01Character::CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult)
{
    if (!IsLocallyControlled()) { Super::CalcCamera(DeltaTime, OutResult); return; }
    const FRotator Aim = GetControlRotation();
    CameraPivot = GetActorLocation() + FVector(0, 0, 70);
    ShoulderElapsed = FMath::Min(ShoulderElapsed + DeltaTime, .15f);
    ShoulderOffset = FMath::Lerp(ShoulderStart, ShoulderTarget, ShoulderElapsed / .15f);
    DesiredCamera = CameraPivot - Aim.Vector() * 350.f + FRotationMatrix(Aim).GetUnitAxis(EAxis::Y) * ShoulderOffset;
    const FVector Arm = DesiredCamera - CameraPivot;
    const FVector Direction = Arm.GetSafeNormal();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(U01Camera), false, this);
    FHitResult Hit;
    bCameraHit = GetWorld()->SweepSingleByChannel(Hit, CameraPivot, DesiredCamera, FQuat::Identity,
        ECC_Camera, FCollisionShape::MakeSphere(12), Params);
    const float SafeDistance = bCameraHit ? (Hit.bStartPenetrating ? 0.f : FMath::Max(0.f, Hit.Distance - .5f)) : Arm.Size();
    CameraDistance = bCameraInitialized ? AnimeMMORPG::U01::ResolveDistance(CameraDistance, SafeDistance, DeltaTime) : SafeDistance;
    bCameraInitialized = true;
    FVector Resolved = CameraPivot + Direction * CameraDistance;
    // Re-sweep after the direction/shoulder changes; never smooth through a wall.
    FHitResult FinalHit;
    if (GetWorld()->SweepSingleByChannel(FinalHit, CameraPivot, Resolved, FQuat::Identity,
        ECC_Camera, FCollisionShape::MakeSphere(12), Params))
    {
        CameraDistance = FinalHit.bStartPenetrating ? 0.f : FMath::Max(0.f, FinalHit.Distance - .5f);
        Resolved = CameraPivot + Direction * CameraDistance;
        bCameraHit = true;
    }
    if (CameraDistance < 80) bOwnerMeshHidden = true;
    else if (CameraDistance > 100) bOwnerMeshHidden = false;
    GetMesh()->SetOwnerNoSee(bOwnerMeshHidden);
    TArray<USceneComponent*> MeshChildren;
    GetMesh()->GetChildrenComponents(true, MeshChildren);
    for (USceneComponent* Child : MeshChildren)
        if (UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Child)) Primitive->SetOwnerNoSee(bOwnerMeshHidden);
    FollowCamera->SetWorldLocationAndRotation(Resolved, Aim);
    FollowCamera->GetCameraView(DeltaTime, OutResult);
}
