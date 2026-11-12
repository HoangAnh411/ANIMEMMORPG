#include "U01/U01Character.h"
#include "U02/U02CombatComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"

void UU01CharacterMovement::HandleImpact(const FHitResult& Hit,float Dt,const FVector& Delta)
{if(!bPreviewDodge)Super::HandleImpact(Hit,Dt,Delta);}
void UU01CharacterMovement::TrimNativeDodgePath(FVector Position)
{
    // Native StepUp rolls back failed trial branches. Retain only the survivor.
    if(NativeDodgePath.IsEmpty()){NativeDodgePath.Add(Position);return;}
    // Remove closed native search excursions as well as explicit scope reverts.
    // A failed StepUp may sweep up/down and finish at a previous path vertex.
    for(int32 I=0;I<NativeDodgePath.Num();++I)if(NativeDodgePath[I].Equals(Position,1.e-7))
    {NativeDodgePath.SetNum(I+1);return;}
    checkf(false,TEXT("Unrecorded native dodge movement rollback"));
}
bool UU01CharacterMovement::MoveUpdatedComponentImpl(const FVector& Delta,const FQuat& Rotation,bool Sweep,FHitResult* Hit,ETeleportType Teleport)
{
    if(bPreviewDodge)TrimNativeDodgePath(UpdatedComponent->GetComponentLocation());
    const bool Moved=Super::MoveUpdatedComponentImpl(Delta,Rotation,Sweep,Hit,Teleport);
    if(bPreviewDodge&&!NativeDodgePath.Last().Equals(UpdatedComponent->GetComponentLocation(),1.e-7))
    {NativeDodgePath.Add(UpdatedComponent->GetComponentLocation());TrimNativeDodgePath(UpdatedComponent->GetComponentLocation());}
    return Moved;
}
bool UU01CharacterMovement::StepUp(const FVector& Gravity,const FVector& Delta,const FHitResult& Hit,FStepDownResult* Down)
{
    if(!bPreviewDodge)return Super::StepUp(Gravity,Delta,Hit,Down);
    const auto BeforePath=NativeDodgePath;const FVector Before=UpdatedComponent->GetComponentLocation();
    const bool Result=Super::StepUp(Gravity,Delta,Hit,Down);const FVector After=UpdatedComponent->GetComponentLocation();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(U03StepSurvivor),false,CharacterOwner);
    for(auto* Actor:UpdatedPrimitive->GetMoveIgnoreActors())if(Actor)Params.AddIgnoredActor(Actor);
    const auto* Capsule=CharacterOwner->GetCapsuleComponent();
    const bool DirectClear=!GetWorld()->SweepTestByChannel(Before,After,UpdatedComponent->GetComponentQuat(),UpdatedComponent->GetCollisionObjectType(),FCollisionShape::MakeCapsule(Capsule->GetScaledCapsuleRadius(),Capsule->GetScaledCapsuleHalfHeight()),Params);
    // Native StepUp is a search scope. Discard reverted searches; also replace
    // a no-op up/down search by its directly swept survivor when that chord is
    // collision-free. Actual stair rises keep their validated up/forward/down legs.
    if(!Result||DirectClear)
    {NativeDodgePath=BeforePath;if(!NativeDodgePath.Last().Equals(After,1.e-7))NativeDodgePath.Add(After);}
    return Result;
}
void UU01CharacterMovement::WalkDodge(float Seconds,FVector Direction)
{
    if(Seconds<=0||!UpdatedComponent||!IsMovingOnGround())return;
    FindFloor(UpdatedComponent->GetComponentLocation(),CurrentFloor,false);
    if(!CurrentFloor.IsWalkableFloor()){bDodgeLostGround=true;return;}
    const FVector Feet=UpdatedComponent->GetComponentLocation()-FVector(0,0,CharacterOwner->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
    const FVector Next=Feet+Direction*(1200.*Seconds);
    FHitResult Support;FCollisionQueryParams Params(SCENE_QUERY_STAT(U03DodgeFloor),false,CharacterOwner);
    for(auto* Ignored:UpdatedPrimitive->GetMoveIgnoreActors())if(Ignored)Params.AddIgnoredActor(Ignored);
    const bool Floor=GetWorld()->LineTraceSingleByChannel(Support,Next+FVector(0,0,MaxStepHeight+MAX_FLOOR_DIST),Next-FVector(0,0,MaxStepHeight+MAX_FLOOR_DIST),UpdatedComponent->GetCollisionObjectType(),Params);
    if(!Floor||!IsWalkable(Support)){bDodgeBlocked=true;return;}
    Velocity=Direction*1200.;FStepDownResult Down;MoveAlongFloor(Velocity,Seconds,&Down);
    if(Down.bComputedFloor)CurrentFloor=Down.FloorResult;else FindFloor(UpdatedComponent->GetComponentLocation(),CurrentFloor,false);
    if(!CurrentFloor.IsWalkableFloor()){bDodgeLostGround=true;return;}
    AdjustFloorHeight();
}
void UU01CharacterMovement::PlanDodge(double Begin,double End,FVector Direction,uint64 Life,uint64 Sequence,const TArray<AActor*>& BatchPawns)
{
    bool SameBatch=PlanBatch.Num()==BatchPawns.Num();for(auto* Pawn:BatchPawns)SameBatch&=PlanBatch.Contains(Pawn);
    if(bDodgePlan&&SameBatch&&Life==PlanLife&&Sequence==PlanSequence&&Begin<PlanEnd&&End>Begin
        &&UpdatedComponent->GetComponentLocation().Equals(DodgePositionAt(Begin),1.e-6)
        &&PlanFloor.HitResult.Component.IsValid()&&PlanFloor.HitResult.Component->IsQueryCollisionEnabled())return;
    bDodgePlan=false;bDodgeLostGround=false;bDodgeBlocked=false;DodgePath.Reset();
    if(!CharacterOwner||!CharacterOwner->HasAuthority()||End<=Begin||!UpdatedComponent)return;
    PlanBegin=PlanCommitted=Begin;PlanEnd=End;PlanClip=TNumericLimits<double>::Max();PlanDirection=Direction;PlanLife=Life;PlanSequence=Sequence;PlanOrigin=UpdatedComponent->GetComponentLocation();
    PlanBatch.Reset();for(auto* Pawn:BatchPawns)PlanBatch.Add(Pawn);
    const auto Floor=CurrentFloor;const FVector OldVelocity=Velocity;const bool Teleported=bJustTeleported;
    const auto Ignored=UpdatedPrimitive->GetMoveIgnoreActors();
    for(auto* Pawn:BatchPawns)if(Pawn!=CharacterOwner)UpdatedPrimitive->IgnoreActorWhenMoving(Pawn,true);
    NativeDodgePath.Reset();NativeDodgePath.Add(PlanOrigin);
    {
        TGuardValue<bool> Preview(bPreviewDodge,true);FScopedMovementUpdate Deferred(UpdatedComponent,EScopedUpdate::DeferredUpdates);
        WalkDodge(float(End-Begin),Direction);TrimNativeDodgePath(UpdatedComponent->GetComponentLocation());
        PlanDestination=UpdatedComponent->GetComponentLocation();PlanFloor=CurrentFloor;Deferred.RevertMove();
    }
    UpdatedPrimitive->ClearMoveIgnoreActors();for(auto* Actor:Ignored)if(Actor)UpdatedPrimitive->IgnoreActorWhenMoving(Actor,true);
    CurrentFloor=Floor;Velocity=OldVelocity;bJustTeleported=Teleported;
    double Length=0;for(int32 I=1;I<NativeDodgePath.Num();++I)Length+=(NativeDodgePath[I]-NativeDodgePath[I-1]).Size();
    // A blocked flat path consumes distance/1200 seconds then holds. Ramp and
    // vertical StepUp legs share the native horizontal quantum's time budget.
    const double Speed=FMath::Max(1200.,Length/(End-Begin));double At=Begin;
    DodgePath.Add({Begin,PlanOrigin});
    for(int32 I=1;I<NativeDodgePath.Num();++I){At=FMath::Min(End,At+(NativeDodgePath[I]-NativeDodgePath[I-1]).Size()/Speed);DodgePath.Add({At,NativeDodgePath[I]});}
    if(At<End)DodgePath.Add({End,PlanDestination});else DodgePath.Last().At=End;
    bDodgePlan=true;
}
FVector UU01CharacterMovement::DodgePositionAt(double At) const
{
    if(!bDodgePlan||DodgePath.IsEmpty())return PlanOrigin;
    At=FMath::Min(At,PlanClip);
    for(int32 I=1;I<DodgePath.Num();++I)if(At<=DodgePath[I].At)
    {const auto& A=DodgePath[I-1];const auto& B=DodgePath[I];return FMath::Lerp(A.Position,B.Position,FMath::Clamp((At-A.At)/(B.At-A.At),0.,1.));}
    return DodgePath.Last().Position;
}
FVector UU01CharacterMovement::DodgeOffsetAt(double At) const{return DodgePositionAt(At)-PlanOrigin;}
double UU01CharacterMovement::NextDodgePathBoundary(double At,double Through) const
{
    if(!bDodgePlan)return Through;
    if(PlanClip>At)Through=FMath::Min(Through,PlanClip);
    for(const auto& Knot:DodgePath)if(Knot.At>At){Through=FMath::Min(Through,Knot.At);break;}
    return Through;
}
bool UU01CharacterMovement::ClipDodgePath(double At)
{if(!bDodgePlan||At>=PlanClip)return false;PlanClip=At;return true;}
void UU01CharacterMovement::CommitDodge(double At)
{
    if(!bDodgePlan||At<PlanCommitted||At>PlanEnd||!CharacterOwner||!CharacterOwner->HasAuthority())return;
    const auto& Snapshot=CastChecked<AU01Character>(CharacterOwner)->Combat->GetCombatSnapshot();
    if(Snapshot.LifeGeneration!=PlanLife||Snapshot.DodgeSequence!=PlanSequence)return;
    // Apply the retained capsule-swept path, already constrained by batch pawn
    // CCD. Never run a second walking/StepUp/slide solve at this timestamp.
    for(const auto& Knot:DodgePath)if(Knot.At>PlanCommitted&&Knot.At<At)
        MoveUpdatedComponent(DodgePositionAt(Knot.At)-UpdatedComponent->GetComponentLocation(),UpdatedComponent->GetComponentQuat(),false,nullptr,ETeleportType::None);
    MoveUpdatedComponent(DodgePositionAt(At)-UpdatedComponent->GetComponentLocation(),UpdatedComponent->GetComponentQuat(),false,nullptr,ETeleportType::None);
    if(At==PlanEnd&&PlanClip>=PlanEnd)CurrentFloor=PlanFloor;
    if(bDodgeLostGround)SetMovementMode(MOVE_Falling);
    Velocity.X=Velocity.Y=0;PlanCommitted=At;
}
