#include "U02CollisionWorld.h"
#include "U02CombatComponent.h"
#include "U02VitalComponent.h"
#include "U02LabDummy.h"
#include "EngineUtils.h"
#include "U02HurtboxComponent.h"
#include "U01/U01Character.h"
#include "Components/CapsuleComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Brush.h"
#include "PhysicsEngine/BodySetup.h"
#include "PhysicsEngine/BodyInstance.h"
#include "Interfaces/Interface_CollisionDataProvider.h"
#include "Engine/World.h"
#include "GameFramework/PhysicsVolume.h"
#include "Engine/Engine.h"
#include "UObject/UObjectIterator.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "DrawDebugHelpers.h"
#include "HAL/IConsoleManager.h"
#include "GameFramework/PlayerController.h"

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
    if(W==GetWorld()&&W->GetNetMode()!=NM_Client&&Type!=LEVELTICK_ViewportsOnly){DrainAt(W->GetTimeSeconds());DrawSelectedAction();}
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
    for(const auto& R:Hurts)if(auto* H=R.Component.Get())if(auto* V=H->GetOwner()->FindComponentByClass<UU02VitalComponent>())V->Refresh(Now);
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
        if(P->GetOwner()==GetWorld()->GetDefaultBrush()||P->GetOwner()->IsEditorOnly()||Cast<APawn>(P->GetOwner())||Cast<APhysicsVolume>(P->GetOwner())||Cast<UU02HurtboxComponent>(P)||P->GetCollisionResponseToChannel(ECC_Pawn)!=ECR_Block)
        {IgnoredObstructionComponents.Add(P);continue;}
        if(P->GetCollisionResponseToChannel(ECC_GameTraceChannel2)!=ECR_Block)continue;
        auto* PhysicsBody=P->GetBodyInstance();
        if(!PhysicsBody||!PhysicsBody->IsValidBodyInstance())
        {IgnoredObstructionComponents.Add(P);continue;} // render/debug components have bounds but no query shape
        FEnvironment E;E.Component=P;E.Bounds=P->Bounds.GetBox();int Before=Triangles.Num();
        if(auto* Box=Cast<UBoxComponent>(P))AddBoxTriangles(Box->GetComponentTransform(),Box->GetUnscaledBoxExtent(),Triangles);
        else
        {
            auto* Mesh=Cast<UStaticMeshComponent>(P);
            if(auto* Body=P->GetBodySetup())
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
                if(Triangles.Num()==Before&&Mesh&&Mesh->GetStaticMesh())
                {
                    FTriMeshCollisionData Data;
                    if(Mesh->GetStaticMesh()->GetPhysicsTriMeshData(&Data,true))for(const auto& T:Data.Indices)
                        Triangles.Add({P->GetComponentTransform().TransformPosition(FVector(Data.Vertices[T.v0])),P->GetComponentTransform().TransformPosition(FVector(Data.Vertices[T.v1])),P->GetComponentTransform().TransformPosition(FVector(Data.Vertices[T.v2]))});
                }
            }
        }
        E.FirstTriangle=Before;E.TriangleCount=Triangles.Num()-Before;
        E.bSupported&=E.TriangleCount>0;Environment.Add(E);if(!E.bSupported)
        {
            ++UnsupportedObstructions;
            if(FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))UE_LOG(LogU02Collision,Display,TEXT("U02D_UNSUPPORTED component=%s class=%s ownerClass=%s bounds=%s"),*P->GetPathName(),*P->GetClass()->GetName(),*P->GetOwner()->GetClass()->GetName(),*E.Bounds.ToString());
        }
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
        // Complex triangle collision may not expose signed containment via Chaos.
        if(E.Bounds.IsInsideOrOn(O)&&InsideClosedPolyhedron(O,MakeArrayView(Triangles.GetData()+E.FirstTriangle,E.TriangleCount)))return false;
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
        auto* Shape=H.Component.Get();if(!Shape||!Shape->IsQueryCollisionEnabled()||Shape->GetOwner()->IsActorBeingDestroyed()||H.Current.Life.Pawn==P.Action.Source.Pawn)continue;
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
        auto Range=SphereAttackContact(F0,F1,P.Yaw,C0,C1,H.Current.Radius,A,B);
        if(!Range.bHit){RecordSelected(P,H.Current.Life,Shape->StableHurtboxId,FMath::Lerp(F0,F1,A),FMath::Lerp(C0,C1,A),H.Current.Radius,P.Slice.BeginSeconds,TEXT("OUTSIDE"));continue;}++Queries;
        const FVector Up(0,0,90);
        auto Valid=[&](double T){return Unobstructed(FMath::Lerp(F0,F1,T)+Up,FMath::Lerp(C0,C1,T),H.Current.Radius);};
        auto Hit=FirstVisible(F0+Up,F1+Up,C0,C1,H.Current.Radius,Range,Triangles,Valid);
        if(FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))UE_LOG(LogU02Collision,Display,
            TEXT("U02D_QUERY world=%s source=%s:%llu action=%llu target=%s:%llu hurtbox=%u prev=%.17g now=%.17g activeBegin=%.17g activeEnd=%.17g alphaBegin=%.17g alphaEnd=%.17g feet0=(%s) feet1=(%s) yaw=%.17g half=100/60/90 originUp=90 target0=(%s) target1=(%s) radius=%.17g visible=%d unsupportedShapes=%u"),
            *GetWorld()->GetPathName(),*P.Action.Source.Pawn.ToString(),P.Action.Source.Generation,P.Action.Sequence,*H.Current.Life.Pawn.ToString(),H.Current.Life.Generation,Shape->StableHurtboxId,
            PreviousTime,CurrentTime,P.Slice.BeginSeconds,P.Slice.EndSeconds,Range.Begin,Range.End,*F0.ToString(),*F1.ToString(),P.Yaw,*C0.ToString(),*C1.ToString(),H.Current.Radius,Hit.IsSet(),UnsupportedObstructions);
        if(!Hit.IsSet())
        {
            ++Blocked;
            RecordSelected(P,H.Current.Life,Shape->StableHurtboxId,FMath::Lerp(F0,F1,Range.Begin),FMath::Lerp(C0,C1,Range.Begin),H.Current.Radius,P.Slice.BeginSeconds,TEXT("BLOCKED"));
            if(!bSelectedDebug&&FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))
            {
                const FVector Foot=FMath::Lerp(F0,F1,Range.Begin),Origin=Foot+Up;
                DrawDebugBox(GetWorld(),AttackCenter(Foot,P.Yaw),FVector(100,60,90),FRotator(0,P.Yaw,0).Quaternion(),FColor::Red,false,.5f);
                DrawDebugLine(GetWorld(),Origin,SphereNearest(Origin,FMath::Lerp(C0,C1,Range.Begin),H.Current.Radius),FColor::Red,false,.5f);
            }
            continue;
        }
        const double T=Hit.GetValue();
        const double Timestamp=T==P.Slice.BeginAlpha?P.Slice.BeginSeconds:T==P.Slice.EndAlpha?P.Slice.EndSeconds:FMath::Lerp(PreviousTime,CurrentTime,T);
        if(Timestamp<P.Slice.BeginSeconds||Timestamp>P.Slice.EndSeconds||(P.Slice.bEndExclusive&&Timestamp>=P.Slice.EndSeconds))continue;
        Out.Add({{P.Action,H.Current.Life},Timestamp,Shape->StableHurtboxId,true,true});
        RecordSelected(P,H.Current.Life,Shape->StableHurtboxId,FMath::Lerp(F0,F1,T),FMath::Lerp(C0,C1,T),H.Current.Radius,Timestamp,TEXT("VALID"));
        if(!bSelectedDebug&&FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))
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
    UU02VitalComponent* TargetVital=nullptr;UU02VitalComponent* SourceVital=nullptr;
    for(const auto& H:Hurts)if(auto* P=H.Component.Get())if(P->GetSubject()==C.Id.Target)TargetVital=P->GetOwner()->FindComponentByClass<UU02VitalComponent>();
    for(const auto& S:Sources)if(auto* B=S.Component.Get())
    {
        const auto Snap=B->GetCombatSnapshot();if(FLifeId{Snap.PawnId,Snap.LifeGeneration}==C.Id.Action.Source)SourceVital=B->GetOwner()->FindComponentByClass<UU02VitalComponent>();
    }
    if(!TargetCurrent||!TargetVital||!SourceVital||!TargetVital->IsAlive(C.Id.Target)||!SourceVital->IsAlive(C.Id.Action.Source)
        ||!FMath::IsFinite(SourceVital->GetAttackFactor())||SourceVital->GetAttackFactor()<0||!Ledger.ResolveHit(C))return false;
    const double Roll=FixtureCritRoll>=0?FixtureCritRoll:FMath::Min(double(FMath::FRand()),1.-DBL_EPSILON);++CritRolls;
    const auto Result=TargetVital->ApplyResolved(C,SourceVital->GetAttackFactor(),Roll);
    if(!Result.bApplied)return false;
    DamageResults.Add({C,Result,Roll});
    if(const auto* Pawn=Cast<APawn>(SourceVital->GetOwner()))if(Pawn->IsLocallyControlled())HUDTarget=TargetVital->GetOwner();
    Confirmed.Add(C);
    for(auto& D:DebugHurts)if(D.Hit==C.Id&&D.Hurtbox==C.HurtboxId)D.Result=TEXT("CONFIRMED");
    FString SHA;FParse::Value(FCommandLine::Get(),TEXT("U02SourceSHA="),SHA);
    UE_LOG(LogU02Collision,Display,TEXT("U02D_CONFIRMED sourceSHA=%s world=%s time=%.17g source=%s:%llu action=%llu target=%s:%llu hurtbox=%u damage=%d crit=%d roll=%.17g absorbed=%d hpBefore=%d hpAfter=%d death=%d"),
        *SHA,*GetWorld()->GetPathName(),C.TimestampSeconds,*C.Id.Action.Source.Pawn.ToString(),C.Id.Action.Source.Generation,C.Id.Action.Sequence,*C.Id.Target.Pawn.ToString(),C.Id.Target.Generation,C.HurtboxId,Result.Damage,Result.bCrit,Roll,Result.Absorbed,Result.BeforeHP,Result.AfterHP,Result.bDied);
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
    if(GEngine&&FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))GEngine->AddOnScreenDebugMessage(290001,.15f,FColor::Yellow,
        FString::Printf(TEXT("U02-E confirmed | hits %d | queries %llu | blocked %llu | crit %s"),Confirmed.Num(),Queries,Blocked,FixtureCritRoll>=0?TEXT("FIXTURE controlled"):TEXT("server 5%")));
    DrawVitalHUD();
}

bool UU02CollisionWorld::SelectDebugAction(uint64 Sequence)
{
#if !UE_BUILD_SHIPPING
    if(!GetWorld()->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))&&!GetWorld()->GetMapName().EndsWith(TEXT("L_NetworkLab")))return false;
    auto* PC=GetWorld()->GetFirstPlayerController();auto* C=PC?Cast<AU01Character>(PC->GetPawn()):nullptr;if(!C||!C->HasAuthority())return false;
    auto S=C->Combat->GetCombatSnapshot();DebugAction={{S.PawnId,S.LifeGeneration},Sequence?Sequence:S.ActionSequence+1};
    DebugHurts.Empty();bSelectedDebug=true;FlushPersistentDebugLines(GetWorld());
    return true;
#else
    return false;
#endif
}
void UU02CollisionWorld::RecordSelected(const FPending& P,FLifeId Target,uint32 Hurtbox,FVector Feet,FVector Center,double Radius,double Time,const FString& Result)
{
    if(!bSelectedDebug||!(P.Action==DebugAction)||(Center-Feet).Size()>400)return;
    FHitId Id{P.Action,Target};
    auto* Existing=DebugHurts.FindByPredicate([&](const FDebugHurt& D){return D.Hit==Id&&D.Hurtbox==Hurtbox;});
    if(Existing&&(Existing->Result==TEXT("CONFIRMED")||Existing->Result==TEXT("VALID")||Result!=TEXT("VALID")))return;
    FDebugHurt D;D.Hit=Id;D.Hurtbox=Hurtbox;D.Feet=Feet;D.Center=Center;D.Yaw=P.Yaw;D.Radius=Radius;D.Time=Time;D.Origin=Feet+FVector(0,0,90);D.Nearest=SphereNearest(D.Origin,Center,Radius);D.Result=Result;
    if(Result==TEXT("BLOCKED"))
    {
        FHitResult Hit;FCollisionQueryParams Params(SCENE_QUERY_STAT(U02SelectedWall),false);
        for(auto Weak:IgnoredObstructionComponents)if(auto* Comp=Weak.Get())Params.AddIgnoredComponent(Comp);
        if(GetWorld()->LineTraceSingleByChannel(Hit,D.Origin,D.Nearest,ECC_GameTraceChannel2,Params))
        {D.bHasBlock=true;D.BlockPoint=Hit.ImpactPoint;D.Wall=GetPathNameSafe(Hit.GetComponent());}
        else for(const auto& E:Environment)if(E.bSupported)
        {
            for(int I=E.FirstTriangle;I<E.FirstTriangle+E.TriangleCount;++I)if(SegmentTriangleClosed(D.Origin,D.Nearest,Triangles[I]))
            {
                const auto& T=Triangles[I];FVector N=FVector::CrossProduct(T.B-T.A,T.C-T.A);double Den=FVector::DotProduct(N,D.Nearest-D.Origin);
                D.bHasBlock=true;D.BlockPoint=Den!=0?D.Origin+(D.Nearest-D.Origin)*(FVector::DotProduct(N,T.A-D.Origin)/Den):D.Origin;D.Wall=GetPathNameSafe(E.Component.Get());break;
            }
            if(D.bHasBlock)break;
        }
    }
    if(Existing)*Existing=D;else DebugHurts.Add(D);
    UE_LOG(LogU02Collision,Display,TEXT("U02D_SELECTED action=%s:%llu:%llu target=%s:%llu hurtbox=%u time=%.17g result=%s origin=(%s) center=(%s) nearest=(%s) radius=%.17g block=(%s) wall=%s"),
        *P.Action.Source.Pawn.ToString(),P.Action.Source.Generation,P.Action.Sequence,*Target.Pawn.ToString(),Target.Generation,Hurtbox,Time,*D.Result,*D.Origin.ToString(),*D.Center.ToString(),*D.Nearest.ToString(),Radius,*D.BlockPoint.ToString(),*D.Wall);
}
void UU02CollisionWorld::DrawSelectedAction()
{
    if(!bSelectedDebug)return;
    int Count=0;for(const auto& C:Confirmed)if(C.Id.Action==DebugAction)++Count;
    if(GEngine)GEngine->AddOnScreenDebugMessage(290002,.1f,FColor::White,FString::Printf(TEXT("SELECTED %s:%llu:%llu | action hits %d | frozen query only"),*DebugAction.Source.Pawn.ToString(),DebugAction.Source.Generation,DebugAction.Sequence,Count));
    for(const auto& D:DebugHurts)
    {
        FColor Color=D.Result==TEXT("CONFIRMED")?FColor::Green:D.Result==TEXT("BLOCKED")?FColor::Red:D.Result==TEXT("OUTSIDE")?FColor::Silver:FColor::Yellow;
        DrawDebugBox(GetWorld(),AttackCenter(D.Feet,D.Yaw),FVector(100,60,90),FRotator(0,D.Yaw,0).Quaternion(),FColor::Cyan,false,0,1,1);
        DrawDebugSphere(GetWorld(),D.Center,D.Radius,24,Color,false,0,1,1.5f);
        DrawDebugSphere(GetWorld(),D.Origin,3,8,FColor::Magenta,false,0,1);DrawDebugSphere(GetWorld(),D.Nearest,3,8,FColor::Yellow,false,0,1);
        DrawDebugLine(GetWorld(),D.Origin,D.Nearest,Color,false,0,1,3);
        DrawDebugString(GetWorld(),D.Center+FVector(0,0,D.Radius+10),FString::Printf(TEXT("%s:%llu HB%u %s"),*D.Hit.Target.Pawn.ToString().Left(8),D.Hit.Target.Generation,D.Hurtbox,*D.Result),nullptr,Color,0,true);
        if(D.bHasBlock){DrawDebugPoint(GetWorld(),D.BlockPoint,15,FColor::Red,false,0,1);DrawDebugString(GetWorld(),D.BlockPoint+FVector(0,0,10),FString::Printf(TEXT("WALL BLOCK %s"),*FPaths::GetCleanFilename(D.Wall)),nullptr,FColor::Red,0);}
    }
}
namespace
{
FAutoConsoleCommandWithWorldAndArgs SelectU02Action(TEXT("U02DebugAction"),TEXT("Lab only: 0 freezes next local action; explicit sequence selects that action going forward"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* W){if(W)if(auto* S=W->GetSubsystem<UU02CollisionWorld>())S->SelectDebugAction(Args.Num()?FCString::Strtoui64(*Args[0],nullptr,10):0);}));
FAutoConsoleCommandWithWorldAndArgs CornerU02Fixture(TEXT("U02CornerCase"),TEXT("Lab-only action66 reconstruction: open or blocked"),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* W)
    {
#if !UE_BUILD_SHIPPING
        if(!W||!W->GetMapName().EndsWith(TEXT("L_CharacterCombatLab")))return;
        auto* PC=W->GetFirstPlayerController();auto* C=PC?Cast<AU01Character>(PC->GetPawn()):nullptr;if(!C||!C->HasAuthority()||C->Combat->GetCombatSnapshot().bLocked)return;
        C->GetU01Movement()->ResetFixtureState();
        FVector Feet(162.889,-9181.335,2.15);double Yaw=90.720003351569176;
        if(Args.Num()&&Args[0].Equals(TEXT("blocked"),ESearchCase::IgnoreCase)){Feet.X=120;Yaw=80.6;}
        if(Args.Num()&&Args[0].Equals(TEXT("outside"),ESearchCase::IgnoreCase)){Feet.X=400;Yaw=90;}
        C->SetActorLocation(Feet+FVector(0,0,C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),false,nullptr,ETeleportType::TeleportPhysics);
        C->SetActorRotation(FRotator(0,Yaw,0));PC->SetControlRotation(FRotator(0,Yaw,0));C->GetU01Movement()->SetMovementMode(MOVE_Walking);
        W->GetSubsystem<UU02CollisionWorld>()->SelectDebugAction(0);
#endif
    }));
}

bool UU02CollisionWorld::SetLabCritRoll(double Roll)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    const bool Lab=GetWorld()->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))||GetWorld()->GetMapName().EndsWith(TEXT("L_NetworkLab"));
    if(!Lab||GetWorld()->GetNetMode()==NM_Client||!FMath::IsFinite(Roll)||(Roll!=-1&&(Roll<0||Roll>=1)))return false;
    FixtureCritRoll=Roll;UE_LOG(LogU02Collision,Display,TEXT("U02E_FIXTURE critRoll=%.17g productionCrit=5%%"),Roll);return true;
#endif
}
void UU02CollisionWorld::ResetLabDummies()
{
#if !UE_BUILD_SHIPPING
    if(!GetWorld()->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))||GetWorld()->GetNetMode()==NM_Client)return;
    DrainAt(GetWorld()->GetTimeSeconds());
    for(TActorIterator<AU02LabDummy> It(GetWorld());It;++It)It->ResetLabCombat();
#endif
}
void UU02CollisionWorld::DrawVitalHUD()
{
    if(!GEngine)return;
    auto* PC=GetWorld()->GetFirstPlayerController();auto* Pawn=PC?Cast<AU01Character>(PC->GetPawn()):nullptr;
    if(!Pawn||!Pawn->IsLocallyControlled()||!Pawn->Vital)return;
    const auto V=Pawn->Vital->GetSnapshot();GEngine->AddOnScreenDebugMessage(290010,.15f,V.bDead?FColor::Red:FColor::White,
        FString::Printf(TEXT("HP %d/%d | shield %d | %s"),V.HP,V.MaxHP,V.Shield,V.bDead?TEXT("DEFEATED - lab reset only"):TEXT("Playing")));
    if(auto* Target=HUDTarget.Get())if(auto* Vital=Target->FindComponentByClass<UU02VitalComponent>())
    {
        bool Visible=false;for(const auto& H:Hurts)if(auto* P=H.Component.Get())if(P->GetOwner()==Target)
            Visible|=Unobstructed(Feet(Pawn)+FVector(0,0,90),P->GetComponentLocation(),P->GetScaledSphereRadius());
        if(Visible)
        {
            const auto S=Vital->GetSnapshot();GEngine->AddOnScreenDebugMessage(290011,.15f,S.bDead?FColor::Red:FColor::Green,
                FString::Printf(TEXT("Target HP %d/%d | shield %d | %s"),S.HP,S.MaxHP,S.Shield,S.bDead?TEXT("DEFEATED"):TEXT("confirmed server")));
        }
        else GEngine->RemoveOnScreenDebugMessage(290011);
    }
    for(auto& S:Sources)if(S.Component==Pawn->Combat&&Pawn->Combat->GetCombatSnapshot().Phase==uint8(EPhase::Finished))
    {
        const auto Snap=Pawn->Combat->GetCombatSnapshot();
        if(Snap.ActionSequence&&(S.FeedbackAction!=Snap.ActionSequence||S.FeedbackLife!=Snap.LifeGeneration))
        {
            S.FeedbackAction=Snap.ActionSequence;S.FeedbackLife=Snap.LifeGeneration;
            FActionId Id{{Snap.PawnId,Snap.LifeGeneration},Snap.ActionSequence};
            const auto* Hit=DamageResults.FindByPredicate([&](const FConfirmedDamage& R){return R.Hit.Id.Action==Id;});
            GEngine->AddOnScreenDebugMessage(290012,1.2f,Hit?FColor::Green:FColor::Silver,Hit?FString::Printf(TEXT("CONFIRMED %d%s"),Hit->Result.Damage,Hit->Result.bCrit?TEXT(" CRIT"):TEXT("")):TEXT("MISS"));
        }
    }
}
namespace
{
FAutoConsoleCommandWithWorldAndArgs CritU02Fixture(TEXT("U02ECrit"),TEXT("Lab only: off / force / normal"),FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A,UWorld* W)
{if(!W||A.IsEmpty())return;auto* S=W->GetSubsystem<UU02CollisionWorld>();if(S)S->SetLabCritRoll(A[0]==TEXT("off")?1.-1.e-9:A[0]==TEXT("force")?0.:-1.);}));
FAutoConsoleCommandWithWorldAndArgs ResetU02DummyFixture(TEXT("U02EResetDummies"),TEXT("Lab only reset all dummy lives"),FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&,UWorld* W)
{if(W)if(auto* S=W->GetSubsystem<UU02CollisionWorld>())S->ResetLabDummies();}));
FAutoConsoleCommandWithWorldAndArgs ShieldU02Fixture(TEXT("U02EShield"),TEXT("Lab only dummy shield source capacity duration; source>0"),FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& A,UWorld* W)
{
#if !UE_BUILD_SHIPPING
    if(!W||!W->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))||W->GetNetMode()==NM_Client||A.Num()!=3)return;
    auto* S=W->GetSubsystem<UU02CollisionWorld>();S->DrainAt(W->GetTimeSeconds());
    for(TActorIterator<AU02LabDummy> It(W);It;++It)It->Vital->AddFixtureShield(FCString::Strtoui64(*A[0],nullptr,10),FCString::Atoi(*A[1]),W->GetTimeSeconds()+FCString::Atod(*A[2]),W->GetTimeSeconds());
#endif
}));
}
