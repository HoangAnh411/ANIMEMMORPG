#include "U01Character.h"
#include "U01ControlPolicy.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"

void UU01CharacterMovement::SetControlLocked(bool bLocked)
{
    bControlLocked = bLocked;
    if (bLocked)
    {
        ConsumeInputVector();
        Velocity.X = Velocity.Y = 0;
        Acceleration = FVector::ZeroVector;
    }
}

void UU01CharacterMovement::PerformMovement(float DeltaSeconds)
{
    if (bControlLocked)
    {
        Acceleration = FVector::ZeroVector;
        Velocity.X = Velocity.Y = 0;
    }
    Super::PerformMovement(DeltaSeconds); // Keep vertical movement and world simulation alive.
}

AU01Character::AU01Character(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer.SetDefaultSubobjectClass<UU01CharacterMovement>(ACharacter::CharacterMovementComponentName))
{
    GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);
    bUseControllerRotationPitch = bUseControllerRotationYaw = bUseControllerRotationRoll = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 500, 0);
    GetCharacterMovement()->MaxWalkSpeed = 500.f;
    GetCharacterMovement()->JumpZVelocity = 500.f; // C will calibrate the 120 cm apex.
    GetCharacterMovement()->AirControl = .35f;
    JumpMaxCount = 1;
    JumpMaxHoldTime = 0;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("U01Camera"));
    FollowCamera->SetupAttachment(RootComponent);
    FollowCamera->bUsePawnControlRotation = false;
    FollowCamera->FieldOfView = 90;
}

void AU01Character::SetControlLocked(bool bLocked)
{
    CastChecked<UU01CharacterMovement>(GetCharacterMovement())->SetControlLocked(bLocked);
    if (bLocked) { StopJumping(); ConsumeMovementInputVector(); }
}

void AU01Character::ToggleShoulder()
{
    ShoulderStart = ShoulderOffset;
    ShoulderTarget = -ShoulderTarget;
    ShoulderElapsed = 0;
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
