#include "U02CollisionWorld.h"
#include "U02CombatComponent.h"
#include "U02HurtboxComponent.h"
#include "U01/U01Character.h"
#include "Components/CapsuleComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "PhysicsEngine/BodySetup.h"
#include "Interfaces/Interface_CollisionDataProvider.h"
#include "Engine/World.h"
#include "UObject/UObjectIterator.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "DrawDebugHelpers.h"

DEFINE_LOG_CATEGORY_STATIC(LogU02Collision,Log,All);
using namespace AnimeMMORPG::U02;
namespace
{
FVector Feet(const AU01Character* C) {return C->GetActorLocation()-FVector(0,0,C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());}
}
bool UU02CollisionWorld::DoesSupportWorldType(EWorldType::Type Type) const {return Type==EWorldType::Game||Type==EWorldType::PIE;}
void UU02CollisionWorld::Initialize(FSubsystemCollectionBase& C)
{Super::Initialize(C);TickHandle=FWorldDelegates::OnWorldPreActorTick.AddUObject(this,&UU02CollisionWorld::PreActorTick);}
void UU02CollisionWorld::Deinitialize()
{
    FWorldDelegates::OnWorldPreActorTick.Remove(TickHandle);
    for(auto& S:Sources)if(auto* C=S.Component.Get())
    {C->OnActiveInterval.Remove(S.IntervalHandle);if(C->BeforeActionMutation.IsBoundToObject(this))C->BeforeActionMutation.Unbind();}
    Sources.Empty();Hurts.Empty();Pending.Empty();Super::Deinitialize();
}
void UU02CollisionWorld::PreActorTick(UWorld* W,ELevelTick Type,float Dt)
{
    if(W==GetWorld()&&W->GetNetMode()!=NM_Client&&Type!=LEVELTICK_ViewportsOnly)DrainAt(W->GetTimeSeconds());
}
void UU02CollisionWorld::RegisterCombat(UU02CombatComponent* C)
{
    if(!C->GetOwner()->HasAuthority()||Sources.ContainsByPredicate([&](const FSource& S){return S.Component==C;}))return;
    FSource S;S.Component=C;auto* Pawn=CastChecked<AU01Character>(C->GetOwner());
    const auto Snap=C->GetCombatSnapshot();S.Current.Position=Feet(Pawn);S.Current.Life={Snap.PawnId,Snap.LifeGeneration};TArray<UU02HurtboxComponent*> Boxes;Pawn->GetComponents(Boxes);for(auto* H:Boxes)S.Current.Epoch=FMath::Max(S.Current.Epoch,H->ContinuityEpoch);
    S.Previous=S.Current;
    S.IntervalHandle=C->OnActiveInterval.AddLambda([this,Weak=TWeakObjectPtr<UU02CombatComponent>(C)](const FActionId& Id,const FActiveSlice& Slice)
    {
        if(auto* Component=Weak.Get())Pending.Add({Weak,Id,Slice,Component->GetCombatSnapshot().AimYawDegrees});
    });
    C->BeforeActionMutation.BindUObject(this,&UU02CollisionWorld::DrainAt);Sources.Add(S);ObserveCombat(C);
}
void UU02CollisionWorld::UnregisterCombat(UU02CombatComponent* C)
{
    const auto S=C->GetCombatSnapshot();MarkDead({S.PawnId,S.LifeGeneration});
    for(auto& R:Sources)if(R.Component==C)C->OnActiveInterval.Remove(R.IntervalHandle);
    Sources.RemoveAll([&](const FSource& R){return R.Component==C;});
}
void UU02CollisionWorld::RegisterHurtbox(UU02HurtboxComponent* H)
{
    const auto Life=H->GetSubject();
    if(!Life.Pawn.IsValid()||!H->StableHurtboxId||Hurts.ContainsByPredicate([&](const FHurt& R)
        {auto* Other=R.Component.Get();return Other&&Other->GetSubject()==Life&&Other->StableHurtboxId==H->StableHurtboxId;}))
    {UE_LOG(LogU02Collision,Error,TEXT("Invalid/duplicate stable hurtbox registration %s"),*H->GetPathName());return;}
    FHurt R;R.Component=H;R.Current={H->GetComponentLocation(),Life,H->ContinuityEpoch,H->GetScaledSphereRadius()};R.Previous=R.Current;Hurts.Add(R);Ledger.RegisterLife(Life);
}
void UU02CollisionWorld::UnregisterHurtbox(UU02HurtboxComponent* H)
{
    if(H->GetOwner()->IsActorBeingDestroyed())MarkDead(H->GetSubject());
    Hurts.RemoveAll([&](const FHurt& R){return R.Component==H;});
}
void UU02CollisionWorld::MarkDead(FLifeId Life) {Ledger.MarkDead(Life);}
void UU02CollisionWorld::ObserveCombat(UU02CombatComponent* C)
{
    const auto S=C->GetCombatSnapshot();FLifeId Life{S.PawnId,S.LifeGeneration};Ledger.RegisterLife(Life);
    if(S.ActionSequence)
    {
        FActionId Id{Life,S.ActionSequence};Ledger.RegisterAction(Id,S.StartSeconds+.16,S.StartSeconds+.22);
        if(S.Phase==uint8(EPhase::Cancelled))Ledger.InvalidateAction(Id,S.ServerSeconds);
    }
}
void UU02CollisionWorld::Capture(double Now)
{
    PreviousTime=CurrentTime<0?Now:CurrentTime;CurrentTime=Now;
    for(auto& S:Sources)if(auto* C=S.Component.Get())
    {
        S.Previous=S.Current;auto* Pawn=CastChecked<AU01Character>(C->GetOwner());const auto Snap=C->GetCombatSnapshot();
        S.Current.Position=Feet(Pawn);S.Current.Life={Snap.PawnId,Snap.LifeGeneration};
        // Teleport propagation is recorded by the character's root-attached hurtboxes.
        TArray<UU02HurtboxComponent*> Boxes;Pawn->GetComponents(Boxes);uint64 Epoch=0;for(auto* H:Boxes)Epoch=FMath::Max(Epoch,H->ContinuityEpoch);S.Current.Epoch=Epoch;
        Ledger.RegisterLife(S.Current.Life);
    }
    for(auto& R:Hurts)if(auto* H=R.Component.Get())
    {R.Previous=R.Current;R.Current={H->GetComponentLocation(),H->GetSubject(),H->ContinuityEpoch,H->GetScaledSphereRadius()};Ledger.RegisterLife(R.Current.Life);}
    CaptureEnvironment();
}
void UU02CollisionWorld::CaptureEnvironment()
{
    Environment.Empty();Triangles.Empty();IgnoredObstructionComponents.Empty();UnsupportedObstructions=0;
    for(TObjectIterator<UPrimitiveComponent> It;It;++It)
    {
        auto* P=*It;if(P->GetWorld()!=GetWorld()||!P->IsRegistered()||!P->IsQueryCollisionEnabled()||!P->GetOwner())continue;
        // Trigger/physics volumes and pawn bodies are not solid environment. New trace
        // channels can inherit Block even where their existing Pawn response is overlap.
        if(Cast<APawn>(P->GetOwner())||Cast<UU02HurtboxComponent>(P)||P->GetCollisionResponseToChannel(ECC_Pawn)!=ECR_Block)
        {IgnoredObstructionComponents.Add(P);continue;}
        if(P->GetCollisionResponseToChannel(ECC_GameTraceChannel2)!=ECR_Block)continue;
        FEnvironment E;E.Component=P;E.Bounds=P->Bounds.GetBox();int Before=Triangles.Num();
        if(auto* Box=Cast<UBoxComponent>(P))AddBoxTriangles(Box->GetComponentTransform(),Box->GetUnscaledBoxExtent(),Triangles);
        else if(auto* Mesh=Cast<UStaticMeshComponent>(P))
        {
            if(auto* Body=Mesh->GetBodySetup())
            {
                if(Body->CollisionTraceFlag!=CTF_UseComplexAsSimple)
                {
                    for(const auto& B:Body->AggGeom.BoxElems)AddBoxTriangles(B.GetTransform()*P->GetComponentTransform(),FVector(B.X,B.Y,B.Z)*.5,Triangles);
                    for(const auto& C:Body->AggGeom.ConvexElems)for(int I=0;I+2<C.IndexData.Num();I+=3)
                    {
                        const FTransform X=C.GetTransform()*P->GetComponentTransform();
                        Triangles.Add({X.TransformPosition(C.VertexData[C.IndexData[I]]),X.TransformPosition(C.VertexData[C.IndexData[I+1]]),X.TransformPosition(C.VertexData[C.IndexData[I+2]])});
                    }
                    E.bSupported=Body->AggGeom.SphereElems.IsEmpty()&&Body->AggGeom.SphylElems.IsEmpty()&&Body->AggGeom.TaperedCapsuleElems.IsEmpty();
                }
                if(Triangles.Num()==Before&&Mesh->GetStaticMesh())
                {
                    FTriMeshCollisionData Data;
                    if(Mesh->GetStaticMesh()->GetPhysicsTriMeshData(&Data,true))for(const auto& T:Data.Indices)
                        Triangles.Add({P->GetComponentTransform().TransformPosition(FVector(Data.Vertices[T.v0])),P->GetComponentTransform().TransformPosition(FVector(Data.Vertices[T.v1])),P->GetComponentTransform().TransformPosition(FVector(Data.Vertices[T.v2]))});
                }
            }
        }
        E.bSupported&=Triangles.Num()>Before;Environment.Add(E);if(!E.bSupported)++UnsupportedObstructions;
    }
}
bool UU02CollisionWorld::Unobstructed(FVector O,FVector C,double R) const
{
    const FVector End=SphereNearest(O,C,R);FBox Segment(ForceInit);Segment+=O;Segment+=End;
    for(const auto& E:Environment)
    {
        if(!E.Bounds.Intersect(Segment))continue;
        if(!E.bSupported)return false; // authoring diagnostic, never silently allow an unknown solid
        if(auto* P=E.Component.Get()) { FVector Closest;const float D=P->GetClosestPointOnCollision(O,Closest);if(D==0)return false; }
    }
    for(const auto& T:Triangles)if(SegmentTriangleClosed(O,End,T))return false;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(U02Wall),false);
    for(const auto& Weak:IgnoredObstructionComponents)if(auto* Cmp=Weak.Get())Params.AddIgnoredComponent(Cmp);
    return !GetWorld()->LineTraceTestByChannel(O,End,ECC_GameTraceChannel2,Params);
}
void UU02CollisionWorld::CollectHitCandidates(const FPending& P,TArray<FHitCandidate>& Out)
{
    const auto* Source=Sources.FindByPredicate([&](const FSource& S){return S.Component==P.Component;});if(!Source)return;
    for(const auto& H:Hurts)
    {
        auto* Shape=H.Component.Get();if(!Shape||Shape->GetOwner()->IsActorBeingDestroyed()||H.Current.Life.Pawn==P.Action.Source.Pawn)continue;
        if(Cast<AU01Character>(Shape->GetOwner())&&!bCharacterFixtureTargets)continue;
        const bool Continuous=Source->Previous.Life==Source->Current.Life&&Source->Previous.Epoch==Source->Current.Epoch
            &&H.Previous.Life==H.Current.Life&&H.Previous.Epoch==H.Current.Epoch&&H.Previous.Radius==H.Current.Radius;
        if(FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))UE_LOG(LogU02Collision,Display,TEXT("U02D_SPAN source=%s target=%s hurtbox=%u continuous=%d epochs=%llu/%llu targetEpochs=%llu/%llu radius=%.17g/%.17g feet=%s target=%s"),*P.Action.Source.Pawn.ToString(),*H.Current.Life.Pawn.ToString(),Shape->StableHurtboxId,Continuous,Source->Previous.Epoch,Source->Current.Epoch,H.Previous.Epoch,H.Current.Epoch,H.Previous.Radius,H.Current.Radius,*Source->Current.Position.ToString(),*H.Current.Position.ToString());
        double A=P.Slice.BeginAlpha,B=P.Slice.EndAlpha;
        FVector F0=Source->Previous.Position,F1=Source->Current.Position,C0=H.Previous.Position,C1=H.Current.Position;
        if(!Continuous)
        {
            ++Discontinuities;
            // Never reinterpret an old active range as a sweep through a teleport.
            if(CurrentTime<P.Slice.BeginSeconds||CurrentTime>P.Slice.EndSeconds||P.Slice.bEndExclusive)continue;
            A=B=1;F0=F1;C0=C1;
        }
        auto Range=SphereAttackContact(F0,F1,P.Yaw,C0,C1,H.Current.Radius,A,B);if(!Range.bHit)continue;++Queries;
        const FVector Up(0,0,90);
        auto Valid=[&](double T){return Unobstructed(FMath::Lerp(F0,F1,T)+Up,FMath::Lerp(C0,C1,T),H.Current.Radius);};
        auto Hit=FirstVisible(F0+Up,F1+Up,C0,C1,H.Current.Radius,Range,Triangles,Valid);
        if(FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))UE_LOG(LogU02Collision,Display,
            TEXT("U02D_QUERY world=%s source=%s:%llu action=%llu target=%s:%llu hurtbox=%u prev=%.17g now=%.17g activeBegin=%.17g activeEnd=%.17g alphaBegin=%.17g alphaEnd=%.17g feet0=(%s) feet1=(%s) yaw=%.17g half=100/60/90 originUp=90 target0=(%s) target1=(%s) radius=%.17g visible=%d unsupportedShapes=%u"),
            *GetWorld()->GetPathName(),*P.Action.Source.Pawn.ToString(),P.Action.Source.Generation,P.Action.Sequence,*H.Current.Life.Pawn.ToString(),H.Current.Life.Generation,Shape->StableHurtboxId,
            PreviousTime,CurrentTime,P.Slice.BeginSeconds,P.Slice.EndSeconds,Range.Begin,Range.End,*F0.ToString(),*F1.ToString(),P.Yaw,*C0.ToString(),*C1.ToString(),H.Current.Radius,Hit.IsSet(),UnsupportedObstructions);
        if(!Hit.IsSet()){++Blocked;continue;}
        const double T=Hit.GetValue();
        const double Timestamp=T==P.Slice.BeginAlpha?P.Slice.BeginSeconds:T==P.Slice.EndAlpha?P.Slice.EndSeconds:FMath::Lerp(PreviousTime,CurrentTime,T);
        if(Timestamp<P.Slice.BeginSeconds||Timestamp>P.Slice.EndSeconds||(P.Slice.bEndExclusive&&Timestamp>=P.Slice.EndSeconds))continue;
        Out.Add({{P.Action,H.Current.Life},Timestamp,Shape->StableHurtboxId,true,true});
        if(FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))
        {
            const FVector FeetNow=FMath::Lerp(F0,F1,T);
            DrawDebugBox(GetWorld(),AttackCenter(FeetNow,P.Yaw),FVector(100,60,90),FRotator(0,P.Yaw,0).Quaternion(),FColor::Cyan,false,.5f);
            DrawDebugLine(GetWorld(),FeetNow+Up,SphereNearest(FeetNow+Up,FMath::Lerp(C0,C1,T),H.Current.Radius),FColor::Green,false,.5f);
        }
    }
}
bool UU02CollisionWorld::ResolveHit(const FHitCandidate& C)
{
    bool TargetCurrent=false;
    for(const auto& H:Hurts)if(auto* P=H.Component.Get())if(P->GetSubject()==C.Id.Target&&!P->GetOwner()->IsActorBeingDestroyed())TargetCurrent=true;
    if(!TargetCurrent||!Ledger.ResolveHit(C))return false;
    Confirmed.Add(C);
    FString SHA;FParse::Value(FCommandLine::Get(),TEXT("U02SourceSHA="),SHA);
    UE_LOG(LogU02Collision,Display,TEXT("U02D_CONFIRMED sourceSHA=%s world=%s time=%.17g source=%s:%llu action=%llu target=%s:%llu hurtbox=%u damage=NOT_IMPLEMENTED"),
        *SHA,*GetWorld()->GetPathName(),C.TimestampSeconds,*C.Id.Action.Source.Pawn.ToString(),C.Id.Action.Source.Generation,C.Id.Action.Sequence,*C.Id.Target.Pawn.ToString(),C.Id.Target.Generation,C.HurtboxId);
    OnGeometryConfirmed.Broadcast(C);return true;
}
void UU02CollisionWorld::DrainAt(double Now)
{
    if(bDraining||GetWorld()->GetNetMode()==NM_Client||!FMath::IsFinite(Now)||Now<CurrentTime||GetWorld()->bIsTearingDown)return;
    TGuardValue<bool> Guard(bDraining,true);
    if(Now>CurrentTime)Capture(Now);
    // Sample every collider first, advance every source next, resolve one globally sorted batch last.
    for(auto& S:Sources)if(auto* C=S.Component.Get()){ObserveCombat(C);C->AdvanceAuthority(Now);}
    TArray<FHitCandidate> Candidates;auto Batch=MoveTemp(Pending);Pending.Empty();
    for(const auto& P:Batch)CollectHitCandidates(P,Candidates);
    Candidates.Sort(CandidateLess);
    for(const auto& C:Candidates)ResolveHit(C);
}
