#include "U02CollisionWorld.h"
#include "U02NetworkState.h"
#include "U02CombatComponent.h"
#include "U02VitalComponent.h"
#include "U02LabDummy.h"
#include "EngineUtils.h"
#include "U02HurtboxComponent.h"
#include "U01/U01Character.h"
#include "U03/U03DodgeCollision.h"
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
#include "AIController.h"

DEFINE_LOG_CATEGORY_STATIC(LogU02Collision,Log,All);
using namespace AnimeMMORPG::U02;
namespace
{
FVector Feet(const AU01Character* C) {return C->GetActorLocation()-FVector(0,0,C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());}
}
bool UU02CollisionWorld::DoesSupportWorldType(EWorldType::Type Type) const {return Type==EWorldType::Game||Type==EWorldType::PIE;}
void UU02CollisionWorld::StartDefenseFixture(const FString& Label)
{
#if !UE_BUILD_SHIPPING
    if(GetWorld()->GetNetMode()==NM_Client)return;
    const TArray<FString> Labels={TEXT("off"),TEXT("block"),TEXT("unparryable"),TEXT("bypass"),TEXT("slow"),TEXT("stun"),TEXT("knockdown"),TEXT("launch"),TEXT("grab"),TEXT("multi")};
    if(!Labels.Contains(Label))return;
    DrainAt(GetWorld()->GetTimeSeconds());
    for(auto& E:DefenseEnemies)if(auto* A=E.Actor.Get()){if(auto* PC=A->GetController())PC->Destroy();A->Destroy();}
    DefenseEnemies.Empty();DefenseFixtureHits.Empty();
    if(Label==TEXT("off"))return;
    TArray<AU01Character*> Targets;for(TActorIterator<AU01Character> It(GetWorld());It;++It)if(Cast<APlayerController>(It->GetController()))Targets.Add(*It);
    for(auto* Target:Targets)for(int32 I=0;I<(Label==TEXT("multi")?2:1);++I)
    {
        const FVector P=Target->GetActorLocation()+Target->GetControlRotation().Vector().GetSafeNormal2D()*150+FVector(0,I?35:0,0);
        FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        auto* Enemy=GetWorld()->SpawnActor<AU01Character>(P,(Target->GetActorLocation()-P).Rotation(),Params);
        auto* Controller=GetWorld()->SpawnActor<AAIController>();Controller->bSetControlRotationFromPawnOrientation=false;Controller->Possess(Enemy);Controller->SetControlRotation((Target->GetActorLocation()-P).Rotation());
        Enemy->Tags.Add(FName(*(TEXT("B2_FIXTURE_")+Label)));DefenseEnemies.Add({Enemy,Target,Label,GetWorld()->GetTimeSeconds()+1.});
    }
    UE_LOG(LogU02Collision,Display,TEXT("U03B2_FIXTURE label=%s start=%.17g duration=1.25 slow=.5 launchImpulse=NONE enemyOnly=1"),*Label,GetWorld()->GetTimeSeconds());
#endif
}
void UU02CollisionWorld::TickDefenseFixture(double Now)
{
#if !UE_BUILD_SHIPPING
    for(auto& E:DefenseEnemies)
    {
        auto* A=E.Actor.Get();auto* Target=E.Target.Get();if(!A||!Target||Now<E.Next||Target->Vital->GetSnapshot().bDead)continue;
        E.Next=Now+.75;
        if(A->Combat->Model&&A->Combat->Model->Current())continue;
        FDefenseFixtureHit H;H.Duration=1.25;
        H.bParryable=E.Label!=TEXT("unparryable");H.bBlockable=E.Label!=TEXT("bypass")&&E.Label!=TEXT("grab");
        if(E.Label==TEXT("slow"))H.Slow=.5;
        using namespace AnimeMMORPG::U03;
        if(E.Label==TEXT("stun"))H.Hard=EHardCC::Stun;
        if(E.Label==TEXT("knockdown"))H.Hard=EHardCC::Knockdown;
        if(E.Label==TEXT("launch"))H.Hard=EHardCC::Launch;
        if(E.Label==TEXT("grab"))H.Hard=EHardCC::Grab;
        const double Yaw=(Target->GetActorLocation()-A->GetActorLocation()).Rotation().Yaw;
        A->Combat->SubmitAttackIntent(A->Combat->GetLastCommand()+1,Now,Yaw);
        DrainAt(Now);
        if(const auto* Action=A->Combat->Model->Current())DefenseFixtureHits.Add(Action->Identity,H);
    }
#endif
}
static FAutoConsoleCommandWithWorldAndArgs B2FixtureCommand(TEXT("U03B2Fixture"),TEXT("Labelled enemy fixture: off/block/unparryable/bypass/slow/stun/knockdown/launch/grab/multi; no player defense input."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* W){if(W&&Args.Num()==1)if(auto* C=W->GetSubsystem<UU02CollisionWorld>())C->StartDefenseFixture(Args[0]);}));
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
    if(W==GetWorld()&&W->GetNetMode()!=NM_Client&&Type!=LEVELTICK_ViewportsOnly){DrainAt(W->GetTimeSeconds());TickDefenseFixture(W->GetTimeSeconds());DrawSelectedAction();}
}
void UU02CollisionWorld::RegisterCombat(UU02CombatComponent* C)
{
    if(!C->GetOwner()->HasAuthority()||Sources.ContainsByPredicate([&](const FSource& S){return S.Component==C;}))return;
    FSource S;S.Component=C;auto* Pawn=CastChecked<AU01Character>(C->GetOwner());
    const auto Snap=C->GetCombatSnapshot();S.Current.Position=Feet(Pawn);S.Current.Life={Snap.PawnId,Snap.LifeGeneration};TArray<UU02HurtboxComponent*> Boxes;Pawn->GetComponents(Boxes);for(auto* H:Boxes)S.Current.Epoch=FMath::Max(S.Current.Epoch,H->ContinuityEpoch);
    S.Previous=S.Current;
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
    FHurt R;R.Component=H;R.Current={H->GetComponentLocation(),Life,H->ContinuityEpoch,H->GetScaledSphereRadius()};R.Previous=R.Current;R.AvailableFrom=FMath::Max(double(GetWorld()->GetTimeSeconds()),CurrentTime);Hurts.Add(R);Ledger.RegisterLife(Life);
}
void UU02CollisionWorld::UnregisterHurtbox(UU02HurtboxComponent* H)
{
    if(H->GetOwner()->IsActorBeingDestroyed())MarkDead(H->GetSubject());
    Hurts.RemoveAll([&](const FHurt& R){return R.Component==H;});
}
void UU02CollisionWorld::MarkDead(FLifeId Life) {Ledger.MarkDead(Life);}
void UU02CollisionWorld::RebaseResetSubject(AActor* Subject)
{
    if(!Subject||!Subject->HasAuthority())return;
    // Reset is a known boundary, not an unknown swept path. Establish the new
    // life baseline now so a first NEW action can span its entire active next step.
    for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->GetOwner()==Subject)
    {
        auto* Pawn=CastChecked<AU01Character>(Subject);const auto Snap=C->GetCombatSnapshot();
        S.Current.Position=Feet(Pawn);S.Current.Life={Snap.PawnId,Snap.LifeGeneration};S.Current.Epoch=0;
        TArray<UU02HurtboxComponent*> Boxes;Pawn->GetComponents(Boxes);for(auto* H:Boxes)S.Current.Epoch=FMath::Max(S.Current.Epoch,H->ContinuityEpoch);
        S.Previous=S.Current;Ledger.RegisterLife(S.Current.Life);
    }
    for(auto& H:Hurts)if(auto* C=H.Component.Get())if(C->GetOwner()==Subject)
    {
        H.Current={C->GetComponentLocation(),C->GetSubject(),C->ContinuityEpoch,C->GetScaledSphereRadius()};H.Previous=H.Current;H.AvailableFrom=FMath::Max(double(GetWorld()->GetTimeSeconds()),CurrentTime);Ledger.RegisterLife(H.Current.Life);
    }
}
void UU02CollisionWorld::ObserveCombat(UU02CombatComponent* C)
{
    const auto S=C->GetCombatSnapshot();FLifeId Life{S.PawnId,S.LifeGeneration};Ledger.RegisterLife(Life);
    if(S.ActionSequence)
    {
        FActionId Id{Life,S.ActionSequence};Ledger.RegisterAction(Id,S.StartSeconds+S.ActiveStart,S.StartSeconds+S.ActiveEnd);
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
    {R.Previous=R.Current;R.Current={H->GetComponentLocation(),H->GetSubject(),H->ContinuityEpoch,H->GetScaledSphereRadius()};if(!(R.Previous.Life==R.Current.Life))R.AvailableFrom=Now;Ledger.RegisterLife(R.Current.Life);}
    CaptureEnvironment();
}
void UU02CollisionWorld::CaptureEnvironment()
{
    const auto PreviousEnvironment=Environment;const auto PreviousTriangles=Triangles;
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
    bool Changed=PreviousEnvironment.Num()!=Environment.Num()||PreviousTriangles.Num()!=Triangles.Num();
    if(!Changed)for(int32 I=0;I<Environment.Num();++I)
        Changed|=PreviousEnvironment[I].Component!=Environment[I].Component||PreviousEnvironment[I].Bounds.Min!=Environment[I].Bounds.Min||PreviousEnvironment[I].Bounds.Max!=Environment[I].Bounds.Max;
    if(!Changed)for(int32 I=0;I<Triangles.Num();++I)Changed|=PreviousTriangles[I].A!=Triangles[I].A||PreviousTriangles[I].B!=Triangles[I].B||PreviousTriangles[I].C!=Triangles[I].C;
    if(Changed)for(auto& S:Sources)if(auto* C=S.Component.Get())C->Character()->GetU01Movement()->InvalidateDodgePath();
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
        if(Cast<AU01Character>(Shape->GetOwner())&&!bCharacterFixtureTargets && !DefenseEnemies.ContainsByPredicate([&](const FDefenseEnemy& E){return E.Actor.Get()==P.Component->GetOwner()&&E.Target.Get()==Shape->GetOwner();}))continue;
        if(H.AvailableFrom>P.Slice.EndSeconds)continue;
        const bool Continuous=Source->Previous.Life==Source->Current.Life&&Source->Previous.Epoch==Source->Current.Epoch
            &&H.Previous.Life==H.Current.Life&&H.Previous.Epoch==H.Current.Epoch&&H.Previous.Radius==H.Current.Radius;
        if(FParse::Param(FCommandLine::Get(),TEXT("U02Trace")))UE_LOG(LogU02Collision,Display,TEXT("U02D_SPAN source=%s target=%s hurtbox=%u continuous=%d epochs=%llu/%llu targetEpochs=%llu/%llu radius=%.17g/%.17g feet=%s target=%s"),*P.Action.Source.Pawn.ToString(),*H.Current.Life.Pawn.ToString(),Shape->StableHurtboxId,Continuous,Source->Previous.Epoch,Source->Current.Epoch,H.Previous.Epoch,H.Current.Epoch,H.Previous.Radius,H.Current.Radius,*Source->Current.Position.ToString(),*H.Current.Position.ToString());
        const double Begin=FMath::Max(P.Slice.BeginSeconds,H.AvailableFrom),End=P.Slice.EndSeconds;
        if(Begin>End)continue;
        double A=0,B=1;
        auto Sample=[&](FVector Previous,FVector Current,double At)
        {return FMath::Lerp(Previous,Current,CurrentTime>PreviousTime?(At-PreviousTime)/(CurrentTime-PreviousTime):1.);};
        FVector F0=Sample(Source->Previous.Position,Source->Current.Position,Begin),F1=Sample(Source->Previous.Position,Source->Current.Position,End);
        FVector C0=Sample(H.Previous.Position,H.Current.Position,Begin),C1=Sample(H.Previous.Position,H.Current.Position,End);
        auto Planned=[&](AU01Character* Pawn,FVector Relative,FVector& P0,FVector& P1)
        {
            if(!Pawn)return;auto* M=Pawn->GetU01Movement();if(!M->HasDodgePlan())return;
            P0=M->DodgePositionAt(Begin)+Relative;
            P1=M->DodgePositionAt(End)+Relative;
        };
        auto* SourcePawn=Cast<AU01Character>(P.Component->GetOwner());
        Planned(SourcePawn,FVector(0,0,-SourcePawn->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()),F0,F1);
        if(auto* TargetPawn=Cast<AU01Character>(Shape->GetOwner()))Planned(TargetPawn,Shape->GetComponentLocation()-TargetPawn->GetActorLocation(),C0,C1);
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
        const double Timestamp=T==0?Begin:T==1?End:FMath::Lerp(Begin,End,T);
        if(Timestamp<P.Slice.BeginSeconds||Timestamp>P.Slice.EndSeconds||(P.Slice.bEndExclusive&&Timestamp>=P.Slice.EndSeconds))continue;
        Out.Add({{P.Action,H.Current.Life},Timestamp,Shape->StableHurtboxId,true,true,P.DefinitionId,P.DefinitionVersion,P.RawDamage});
        auto& Candidate=Out.Last();Candidate.ToSource=FMath::Lerp(F0,F1,T)-FMath::Lerp(C0,C1,T);Candidate.ToSource.Z=0;
        Candidate.AttackDirection=FRotator(0,P.Yaw,0).Vector();
        const auto& Rules=AnimeMMORPG::U03::Definition(AnimeMMORPG::U03::EAction(P.DefinitionId));
        Candidate.bBlockable=Rules.bBlockable;Candidate.bParryable=Rules.bParryable;
        if(const auto* Fixture=DefenseFixtureHits.Find(P.Action)){Candidate.bBlockable=Fixture->bBlockable;Candidate.bParryable=Fixture->bParryable;}
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
    using namespace AnimeMMORPG::U03;
    auto* TargetCombat=TargetVital->GetOwner()->FindComponentByClass<UU02CombatComponent>();
    EDefense Defense=EDefense::Hit;
    if(TargetCombat && TargetCombat->Model)
    {
        check(TargetCombat->Model->Time()==C.TimestampSeconds);
        Defense=TargetCombat->Model->DefendAtBarrier(C.ToSource,C.AttackDirection,C.bBlockable,C.bParryable);
        if(Defense!=EDefense::Hit){++TargetCombat->Snapshot.DefenseEvent;TargetCombat->Snapshot.DefenseResult=uint8(Defense);TargetCombat->Snapshot.DefenseEventTime=C.TimestampSeconds;}
    }
    double Roll=-1;FDamageResult Result;
    if(Defense==EDefense::Parry)
    {Result.bApplied=true;Result.BeforeHP=Result.AfterHP=TargetVital->GetSnapshot().HP;}
    else
    {
        Roll=FixtureCritRoll>=0?FixtureCritRoll:FMath::Min(double(FMath::FRand()),1.-DBL_EPSILON);++CritRolls;
        Result=TargetVital->ApplyResolved(C,SourceVital->GetAttackFactor(),Roll,Defense==EDefense::Block?.30:1.);
    }
    Result.Defense=uint8(Defense);
    if(!Result.bApplied)return false;
    DamageResults.Add({C,Result,Roll});
    for(TActorIterator<AU02NetworkState> It(GetWorld());It;++It)It->Confirm(DamageResults.Last());
    if(const auto* Pawn=Cast<APawn>(SourceVital->GetOwner()))if(Pawn->IsLocallyControlled())HUDTarget=TargetVital->GetOwner();
    Confirmed.Add(C);
    for(auto& D:DebugHurts)if(D.Hit==C.Id&&D.Hurtbox==C.HurtboxId)D.Result=TEXT("CONFIRMED");
    FString SHA;FParse::Value(FCommandLine::Get(),TEXT("U02SourceSHA="),SHA);
    UE_LOG(LogU02Collision,Display,TEXT("U02D_CONFIRMED sourceSHA=%s world=%s time=%.17g source=%s:%llu action=%llu target=%s:%llu hurtbox=%u damage=%d crit=%d roll=%.17g absorbed=%d hpBefore=%d hpAfter=%d death=%d"),
        *SHA,*GetWorld()->GetPathName(),C.TimestampSeconds,*C.Id.Action.Source.Pawn.ToString(),C.Id.Action.Source.Generation,C.Id.Action.Sequence,*C.Id.Target.Pawn.ToString(),C.Id.Target.Generation,C.HurtboxId,Result.Damage,Result.bCrit,Roll,Result.Absorbed,Result.BeforeHP,Result.AfterHP,Result.bDied);
    FString Order;for(uint64 Id:Result.ShieldOrder)Order+=FString::Printf(TEXT("%llu,"),Id);
    UE_LOG(LogU02Collision,Display,TEXT("U02E_DAMAGE sourceSHA=%s timestamp=%.17g source=%s:%llu action=%llu target=%s:%llu hurtbox=%u raw=%d attack=%.17g roll=%.17g crit=%d damage=%d absorbed=%d hpBefore=%d hpAfter=%d death=%d shieldOrder=%s"),
        *SHA,C.TimestampSeconds,*C.Id.Action.Source.Pawn.ToString(),C.Id.Action.Source.Generation,C.Id.Action.Sequence,*C.Id.Target.Pawn.ToString(),C.Id.Target.Generation,C.HurtboxId,C.RawDamage,SourceVital->GetAttackFactor(),Roll,Result.bCrit,Result.Damage,Result.Absorbed,Result.BeforeHP,Result.AfterHP,Result.bDied,*Order);
    // Native labelled fixture only: effect is attached to a real geometry-confirmed direct hit.
    if(FixtureInterruptActions.Contains(C.Id.Action) && !Result.bDied && Defense==EDefense::Hit)
        if(TargetCombat)
            ApplyLifecycle(TargetCombat,C.TimestampSeconds,AnimeMMORPG::U03::ECutoff::Interrupt,false);
    if(const auto* Fixture=DefenseFixtureHits.Find(C.Id.Action))
        if(TargetCombat && TargetCombat->Model && !Result.bDied && Defense==EDefense::Hit)
        {
            if(Fixture->Slow>0)TargetCombat->Model->SlowAtBarrier(Fixture->Slow,Fixture->Duration);
            if(Fixture->Hard!=EHardCC::None && TargetCombat->Model->HardAtBarrier(Fixture->Hard,Fixture->Duration))
                ApplyLifecycle(TargetCombat,C.TimestampSeconds,ECutoff::HardCC,false);
        }
    OnGeometryConfirmed.Broadcast(C);return true;
}
namespace
{
class FU03WorldCollector final : public AnimeMMORPG::U03::ITimelineResolver
{
public:
    TFunction<void(const AnimeMMORPG::U03::FActiveInterval&)> Emit;
    TOptional<double> NextEvent(const AnimeMMORPG::U03::FTimelineModel&,double) override {return {};}
    void ResolveInterval(const AnimeMMORPG::U03::FActiveInterval& I) override {if(Emit)Emit(I);}
    void ResolveEvent(AnimeMMORPG::U03::FTimelineModel&,double) override {checkNoEntry();}
};
}
void UU02CollisionWorld::EmitInterval(UU02CombatComponent* C,const AnimeMMORPG::U03::FActiveInterval& I)
{
    FActiveSlice Slice;Slice.bEvaluate=true;Slice.BeginSeconds=I.Begin;Slice.EndSeconds=I.End;Slice.bEndExclusive=I.bEndExclusive;
    const double Span=CurrentTime-PreviousTime;
    Slice.BeginAlpha=Span>0?(I.Begin-PreviousTime)/Span:1;Slice.EndAlpha=Span>0?(I.End-PreviousTime)/Span:1;
    C->LastInterval=Slice;++C->IntervalCount;C->Publish(I.End);
    C->OnActiveInterval.Broadcast(I.Identity,Slice);
}
void UU02CollisionWorld::CollectCurrent(double Through,TArray<FHitCandidate>& Out)
{
    for(auto& Source:Sources)if(auto* C=Source.Component.Get())if(C->Model&&C->Model->Time()<=SimulationTime)
    {
        C->RememberCurrent(SimulationTime);ObserveCombat(C);
        const auto* A=C->Model->Current();if(!A)continue;const auto& D=A->GetDefinition();
        const double Begin=FMath::Max(SimulationTime,A->Start+D.ActiveStart);
        const double End=FMath::Min(Through,FMath::Min(A->Start+D.ActiveEnd,A->Cutoff));
        if(Begin>End||Begin>=A->Start+D.ActiveEnd||Begin>=A->Cutoff)continue;
        FPending P;P.Component=C;P.Action=A->Identity;P.Yaw=A->Yaw;
        P.DefinitionId=uint8(D.Id);P.DefinitionVersion=D.Version;P.RawDamage=D.RawDamage;
        P.Slice.bEvaluate=true;P.Slice.BeginSeconds=Begin;P.Slice.EndSeconds=End;
        P.Slice.bEndExclusive=End==A->Start+D.ActiveEnd||End==A->Cutoff;
        const double Span=CurrentTime-PreviousTime;
        P.Slice.BeginAlpha=Span>0?(Begin-PreviousTime)/Span:1;P.Slice.EndAlpha=Span>0?(End-PreviousTime)/Span:1;
        CollectHitCandidates(P,Out);
    }
    Out.RemoveAll([&](const FHitCandidate& Hit)
    {
        if(!Ledger.CanResolveHit(Hit))return true;
        bool SourceAlive=false,TargetAlive=false;
        for(const auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model&&C->Model->GetLife()==Hit.Id.Action.Source)
            if(auto* V=C->GetOwner()->FindComponentByClass<UU02VitalComponent>())SourceAlive=V->IsAlive(Hit.Id.Action.Source)&&FMath::IsFinite(V->GetAttackFactor())&&V->GetAttackFactor()>=0;
        for(const auto& H:Hurts)if(auto* Shape=H.Component.Get())if(Shape->GetSubject()==Hit.Id.Target)
            if(auto* V=Shape->GetOwner()->FindComponentByClass<UU02VitalComponent>())TargetAlive=V->IsAlive(Hit.Id.Target);
        return !SourceAlive||!TargetAlive;
    });
    Out.Sort(CandidateLess);
}
bool UU02CollisionWorld::ApplyLifecycle(UU02CombatComponent* C,double At,AnimeMMORPG::U03::ECutoff Reason,bool Landing)
{
    if(!C||!C->Model||!FMath::IsFinite(At)||At<C->Model->Time())return false;
    if(bDraining)
    {
        if(C->Model->Time()!=At)return false;
        const auto* A=C->Model->Current();const FActionId Id=A?A->Identity:FActionId{};
        const bool Accepted=Landing?C->Model->GroundedAtBarrier(true):C->Model->CancelAtBarrier(Reason);
        if(Accepted&&!Landing)
        {
            if(Id.Sequence)Ledger.InvalidateAction(Id,At);
            C->Snapshot.Phase=uint8(EPhase::Cancelled);
            if(Reason==AnimeMMORPG::U03::ECutoff::Death)Ledger.MarkDead(C->Model->GetLife());
        }
        return Accepted;
    }
    const uint64 Serial=++NextLifecycle;LifecycleEvents.Add({C,At,Reason,Landing,Serial});
    DrainAt(At);const bool Accepted=LifecycleResults.FindRef(Serial);LifecycleResults.Remove(Serial);return Accepted;
}
void UU02CollisionWorld::DrainAt(double Now)
{
    if(bDraining||GetWorld()->GetNetMode()==NM_Client||!FMath::IsFinite(Now)||Now<CurrentTime||GetWorld()->bIsTearingDown)return;
    TGuardValue<bool> Draining(bDraining,true);
    Sources.Sort([](const auto& A,const auto& B){const auto* CA=A.Component.Get();const auto* CB=B.Component.Get();return CA&&CB?CA->GetCombatSnapshot().PawnId.ToString()<CB->GetCombatSnapshot().PawnId.ToString():CA!=nullptr;});
    if(Now>CurrentTime)Capture(Now);
    if(SimulationTime<0)
    {SimulationTime=Now;for(const auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model)SimulationTime=FMath::Min(SimulationTime,C->Model->Time());}
    bool First=true;
    while(First||SimulationTime<Now)
    {
        First=false;double Boundary=Now;
        for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model)
        {if(C->Model->Time()>SimulationTime)Boundary=FMath::Min(Boundary,C->Model->Time());else Boundary=FMath::Min(Boundary,C->Model->NextBoundaryThrough(Now));}
        for(const auto& E:LifecycleEvents)if(E.At>=SimulationTime)Boundary=FMath::Min(Boundary,E.At);
        TArray<AActor*> BatchPawns;
        for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model&&C->Model->Dodge().Moving(SimulationTime))BatchPawns.Add(C->GetOwner());
        for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model)
        {
            const auto& D=C->Model->Dodge();
            auto* Motor=C->Character()->GetU01Movement();
            if(Motor->HasDodgePlan()&&!D.Moving(SimulationTime))
            {
                S.Previous.Position=S.Current.Position=Feet(C->Character());
                for(auto& H:Hurts)if(auto* Shape=H.Component.Get())if(Shape->GetOwner()==C->GetOwner())H.Previous.Position=H.Current.Position=Shape->GetComponentLocation();
            }
            Motor->PlanDodge(SimulationTime,D.Moving(SimulationTime)?FMath::Min(D.MotionEnd,SimulationTime+1./240.):SimulationTime,D.Direction,C->Model->GetLife().Generation,D.Sequence,BatchPawns);
            Boundary=Motor->NextDodgePathBoundary(SimulationTime,Boundary);
        }
        // Solve moving capsules simultaneously. Previews ignore the other active
        // dodgers' stale transforms; relative CCD constrains both retained paths.
        for(;;)
        {
            TOptional<double> Earliest;UU01CharacterMovement* FirstMotor=nullptr;UU01CharacterMovement* SecondMotor=nullptr;
            for(int32 I=0;I<Sources.Num();++I)for(int32 J=I+1;J<Sources.Num();++J)
            {
                auto* CA=Sources[I].Component.Get();auto* CB=Sources[J].Component.Get();if(!CA||!CB)continue;
                auto* PA=CA->Character();auto* PB=CB->Character();auto* MA=PA->GetU01Movement();auto* MB=PB->GetU01Movement();
                if(!MA->HasDodgePlan()&&!MB->HasDodgePlan())continue;
                const auto* ShapeA=PA->GetCapsuleComponent();const auto* ShapeB=PB->GetCapsuleComponent();
                if(ShapeA->GetCollisionResponseToChannel(ShapeB->GetCollisionObjectType())!=ECR_Block||ShapeB->GetCollisionResponseToChannel(ShapeA->GetCollisionObjectType())!=ECR_Block)continue;
                auto Position=[&](AU01Character* P,UU01CharacterMovement* M,double T){return M->HasDodgePlan()?M->DodgePositionAt(T):P->GetActorLocation();};
                const double Radius=ShapeA->GetScaledCapsuleRadius()+ShapeB->GetScaledCapsuleRadius()+.01;
                const double Half=ShapeA->GetScaledCapsuleHalfHeight()+ShapeB->GetScaledCapsuleHalfHeight()-Radius+.01;
                auto Contact=AnimeMMORPG::U03::CapsuleContact(Position(PA,MA,SimulationTime),Position(PA,MA,Boundary),Position(PB,MB,SimulationTime),Position(PB,MB,Boundary),Radius,Half);
                if(Contact.IsSet())
                {
                    const double At=FMath::Lerp(SimulationTime,Boundary,Contact.GetValue());
                    if((MA->CanClipDodgePath(At)||MB->CanClipDodgePath(At))&&(!Earliest.IsSet()||At<Earliest.GetValue()))
                    {Earliest=At;FirstMotor=MA;SecondMotor=MB;}
                }
            }
            if(!Earliest.IsSet())break;
            FirstMotor->ClipDodgePath(Earliest.GetValue());SecondMotor->ClipDodgePath(Earliest.GetValue());
            if(Earliest.GetValue()>SimulationTime)Boundary=FMath::Min(Boundary,Earliest.GetValue());
        }
        TArray<FHitCandidate> Candidates;CollectCurrent(Boundary,Candidates);
        const double Stop=Candidates.IsEmpty()?Boundary:FMath::Min(Boundary,Candidates[0].TimestampSeconds);
        for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model&&C->Model->Time()<=Stop)
        {
            FU03WorldCollector Collector;Collector.Emit=[this,C](const auto& I){EmitInterval(C,I);};
            check(C->Model->ArriveAtBarrier(Stop,Collector));C->Publish(Stop);
        }
        SimulationTime=Stop;
        for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model)
        {
            auto* M=C->Character()->GetU01Movement();M->CommitDodge(Stop);
            if(M->HasDodgePlan()&&M->DodgeLostGround())ApplyLifecycle(C,Stop,AnimeMMORPG::U03::ECutoff::LostGround,false);
        }
        // Lifecycle mutation has an explicit authority timestamp and precedes new endpoint contact.
        auto ApplyLifecycleGroup=[&]()
        {
            LifecycleEvents.Sort([](const auto& A,const auto& B){return A.At!=B.At?A.At<B.At:A.Serial<B.Serial;});
            for(int32 I=0;I<LifecycleEvents.Num();)
            {
                if(LifecycleEvents[I].At!=Stop){++I;continue;}
                const auto E=LifecycleEvents[I];LifecycleEvents.RemoveAt(I);
                LifecycleResults.Add(E.Serial,ApplyLifecycle(E.Combat.Get(),Stop,E.Reason,E.Landing));
            }
        };
        ApplyLifecycleGroup();
        // ALL models are at Stop and unfinalized. Each death/cutoff applies before the next
        // timestamp/source/event/hurtbox candidate. Callback-created endpoint events are re-collected.
        for(;;)
        {
            bool Resolved=false;
            for(const auto& Hit:Candidates)if(Hit.TimestampSeconds==Stop&&ResolveHit(Hit))Resolved=true;
            ApplyLifecycleGroup();
            Candidates.Empty();CollectCurrent(Stop,Candidates);
            if(Candidates.IsEmpty())break;
            if(!Resolved){for(const auto& Hit:Candidates)if(ResolveHit(Hit))Resolved=true;if(!Resolved)break;Candidates.Empty();CollectCurrent(Stop,Candidates);if(Candidates.IsEmpty())break;}
        }
        for(auto& S:Sources)if(auto* C=S.Component.Get())if(C->Model&&C->Model->Time()==Stop)
        {
            FU03WorldCollector Collector;Collector.Emit=[this,C](const auto& I){EmitInterval(C,I);};
            check(C->Model->FinishBarrier(Collector));C->Publish(Stop);ObserveCombat(C);
        }
    }
    // New input is admitted only AFTER the complete old world barrier at Now.
    for(auto& S:Sources)if(auto* C=S.Component.Get())C->ProcessQueuedIntents(Now);
    for(const auto& R:Hurts)if(auto* H=R.Component.Get())if(auto* V=H->GetOwner()->FindComponentByClass<UU02VitalComponent>())V->Refresh(Now);
    DrawVitalHUD();
}
bool UU02CollisionWorld::FixtureSpend(UU02CombatComponent* C,AnimeMMORPG::U03::EAction Skill)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if(!C||!C->Model||GetWorld()->GetNetMode()==NM_Client)return false;
    DrainAt(GetWorld()->GetTimeSeconds());
    // This fixture tests resource/snapshot integration; it never starts Q/E gameplay.
    const bool Accepted=C->Model->SpendResourceFixture(Skill);
    C->Publish(C->Model->Time(),true);return Accepted;
#endif
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
    FixtureCritRoll=Roll;UE_LOG(LogU02Collision,Display,TEXT("U02E_FIXTURE critRoll=%.17g mode=%s productionCrit=5%%"),Roll,Roll>=.05?TEXT("CRIT_OFF"):Roll>=0?TEXT("CRIT_FORCED"):TEXT("NORMAL"));return true;
#endif
}
void UU02CollisionWorld::ResetLabDummies()
{
#if !UE_BUILD_SHIPPING
    if((!GetWorld()->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"))&&!GetWorld()->GetMapName().EndsWith(TEXT("L_NetworkLab")))||GetWorld()->GetNetMode()==NM_Client)return;
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
