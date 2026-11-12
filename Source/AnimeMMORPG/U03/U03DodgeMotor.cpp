#include "U01/U01Character.h"
#include "U02/U02CombatComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

void UU01CharacterMovement::HandleImpact(const FHitResult& Hit,float Dt,const FVector& Delta)
{
    if(!bPreviewDodge)Super::HandleImpact(Hit,Dt,Delta);
}
void UU01CharacterMovement::WalkDodge(float Seconds,FVector Direction)
{
    if(Seconds<=0 || !UpdatedComponent || !IsMovingOnGround())return;
    FindFloor(UpdatedComponent->GetComponentLocation(),CurrentFloor,false);
    if(!CurrentFloor.IsWalkableFloor()){bDodgeLostGround=true;return;}
    // Require support below the destination's centre, not just a trailing edge of
    // the capsule. Each planned horizontal slice is <=5cm, so no gap is skipped.
    const FVector Feet=UpdatedComponent->GetComponentLocation()-FVector(0,0,CharacterOwner->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
    const FVector Next=Feet+Direction*(1200.*Seconds);
    FHitResult Support;FCollisionQueryParams Params(SCENE_QUERY_STAT(U03DodgeFloor),false,CharacterOwner);
    const bool Floor=GetWorld()->LineTraceSingleByChannel(Support,Next+FVector(0,0,MaxStepHeight+MAX_FLOOR_DIST),Next-FVector(0,0,MaxStepHeight+MAX_FLOOR_DIST),UpdatedComponent->GetCollisionObjectType(),Params);
    if(!Floor||!IsWalkable(Support)){bDodgeBlocked=true;return;}
    Velocity=Direction*1200.;
    FStepDownResult Down;MoveAlongFloor(Velocity,Seconds,&Down);
    if(Down.bComputedFloor)CurrentFloor=Down.FloorResult;else FindFloor(UpdatedComponent->GetComponentLocation(),CurrentFloor,false);
    if(!CurrentFloor.IsWalkableFloor()){bDodgeLostGround=true;return;}
    AdjustFloorHeight();
    // Sweep/StepUp/slide all belong to the existing CharacterMovement walking path.
}
void UU01CharacterMovement::PlanDodge(double Begin,double End,FVector Direction,uint64 Life,uint64 Sequence)
{
    bDodgePlan=false;bDodgeLostGround=false;bDodgeBlocked=false;
    if(!CharacterOwner||!CharacterOwner->HasAuthority()||End<=Begin||!UpdatedComponent)return;
    PlanBegin=PlanCommitted=Begin;PlanEnd=End;PlanDirection=Direction;PlanLife=Life;PlanSequence=Sequence;PlanOrigin=UpdatedComponent->GetComponentLocation();
    const auto Floor=CurrentFloor;const FVector OldVelocity=Velocity;const bool Teleported=bJustTeleported;
    {
        TGuardValue<bool> Preview(bPreviewDodge,true);
        FScopedMovementUpdate Deferred(UpdatedComponent,EScopedUpdate::DeferredUpdates);
        WalkDodge(float(End-Begin),Direction);
        PlanDestination=UpdatedComponent->GetComponentLocation();
        Deferred.RevertMove();
    }
    CurrentFloor=Floor;Velocity=OldVelocity;bJustTeleported=Teleported;bDodgePlan=true;
}
FVector UU01CharacterMovement::DodgeOffsetAt(double At) const
{return bDodgePlan?(PlanDestination-PlanOrigin)*((At-PlanBegin)/(PlanEnd-PlanBegin)):FVector::ZeroVector;}
void UU01CharacterMovement::CommitDodge(double At)
{
    if(!bDodgePlan||At<PlanCommitted||At>PlanEnd||!CharacterOwner||!CharacterOwner->HasAuthority())return;
    const auto* Combat=CastChecked<AU01Character>(CharacterOwner)->Combat.Get();
    const auto& Snapshot=Combat->GetCombatSnapshot();
    if(Snapshot.LifeGeneration!=PlanLife)return;
    // No saved move can set PlanLife/Sequence, restore a charge, or replay this clock.
    const bool WasLost=bDodgeLostGround;
    if(!WasLost)WalkDodge(float(At-PlanCommitted),PlanDirection);
    if(bDodgeLostGround)SetMovementMode(MOVE_Falling);
    Velocity.X=Velocity.Y=0;
    PlanCommitted=At; // a repeated commit at the same time never translates again
}
