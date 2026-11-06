#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U02/U02CollisionGeometry.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02HurtboxComponent.h"
#include "U02/U02LabDummy.h"
#include "U01/U01Character.h"
#include "AIController.h"
#include "Components/BoxComponent.h"
#include "Components/ArrowComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "Engine/CollisionProfile.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "Kismet/GameplayStatics.h"
using namespace AnimeMMORPG::U02;
static constexpr auto U02DFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FU02CollisionTestAccess
{
    static void ReverseSources(UU02CollisionWorld* W) { if(W->Sources.Num()==2)W->Sources.Swap(0,1); }
};
namespace
{
struct FDWorld : FTestWorldWrapper
{
    AU01Character* Source=nullptr;UU02CollisionWorld* Resolver=nullptr;FAutomationTestBase& Test;
    UBoxComponent* Wall(FVector P,FVector Half,FRotator R=FRotator::ZeroRotator)
    {
        auto* A=GetTestWorld()->SpawnActor<AActor>();auto* B=NewObject<UBoxComponent>(A);A->SetRootComponent(B);
        B->SetBoxExtent(Half);B->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);B->SetCollisionResponseToAllChannels(ECR_Block);
        A->SetActorLocation(P);A->SetActorRotation(R);B->RegisterComponent();return B;
    }
    explicit FDWorld(FAutomationTestBase& T):Test(T)
    {
        CreateTestWorld(EWorldType::Game);GetTestWorld()->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        Wall(FVector(0,0,-50),FVector(10000,10000,50));
        auto* DebugActor=GetTestWorld()->SpawnActor<AActor>();auto* Debug=NewObject<UArrowComponent>(DebugActor);DebugActor->SetRootComponent(Debug);
        Debug->SetCollisionEnabled(ECollisionEnabled::QueryOnly);Debug->SetCollisionResponseToAllChannels(ECR_Block);Debug->RegisterComponent();
        Source=GetTestWorld()->SpawnActor<AU01Character>(FVector(0,0,98),FRotator::ZeroRotator);Source->NetworkPawnId=FGuid(1,0,0,1);
        auto* PC=GetTestWorld()->SpawnActor<AAIController>();PC->bSetControlRotationFromPawnOrientation=false;PC->Possess(Source);
        BeginPlayInTestWorld();for(int I=0;I<30;++I)TickTestWorld(1.f/60);
        Resolver=GetTestWorld()->GetSubsystem<UU02CollisionWorld>();Resolver->DrainAt(Now());
    }
    ~FDWorld(){ForwardErrorMessages(&Test);}
    double Now() const {return GetTestWorld()->GetTimeSeconds();}
    AU02LabDummy* Dummy(FVector P,int32 Id=10)
    {
        FTransform X(P);auto* D=GetTestWorld()->SpawnActorDeferred<AU02LabDummy>(AU02LabDummy::StaticClass(),X);
        D->NetworkPawnId=FGuid(Id,0,0,1);UGameplayStatics::FinishSpawningActor(D,X);return D;
    }
    void Attack(double Yaw=0){Source->Combat->SubmitAttackIntent(1,Now(),Yaw);}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DGeometry,"AnimeMMORPG.U02.D.FeetBoxBoundaryAndRelativeSweep",U02DFlags)
bool FU02DGeometry::RunTest(const FString&)
{
    TestEqual(TEXT("Candidate channel name"),UCollisionProfile::Get()->ReturnChannelNameFromContainerIndex(ECC_GameTraceChannel1),FName(TEXT("U02CombatCandidate")));
    TestEqual(TEXT("Obstruction channel name"),UCollisionProfile::Get()->ReturnChannelNameFromContainerIndex(ECC_GameTraceChannel2),FName(TEXT("U02CombatObstruction")));
    const FVector Feet(10,20,30);TestTrue(TEXT("Feet based rotated center"),AttackCenter(Feet,90).Equals(FVector(10,120,120),1.e-8));
    for(double Yaw:{0.,45.,90.,-179.})
    {
        const FQuat Q=FRotator(0,Yaw,0).Quaternion().GetNormalized();auto Point=[&](FVector P){return Feet+Q.RotateVector(P);};
        for(FVector P:{FVector(0,0,0),FVector(200,60,180),FVector(100,-60,90)})
            TestTrue(TEXT("Closed spatial boundaries"),SphereAttackContact(Feet,Feet,Yaw,Point(P),Point(P),0,0,1).bHit);
        for(FVector P:{FVector(-1,0,90),FVector(201,0,90),FVector(100,61,90),FVector(100,0,181)})
            TestFalse(TEXT("Outside box"),SphereAttackContact(Feet,Feet,Yaw,Point(P),Point(P),0,0,1).bHit);
    }
    auto C=SphereAttackContact(FVector::ZeroVector,FVector::ZeroVector,0,FVector(100,-500,90),FVector(100,500,90),10,.32,.44);
    TestTrue(TEXT("Crossing target, neither frame endpoint overlaps"),C.bHit);
    TestTrue(TEXT("Exact relative entry"),FMath::Abs(C.Begin-.43)<1.e-9);
    auto Same=SphereAttackContact(FVector(0,-500,0),FVector(0,500,0),0,FVector(100,0,90),FVector(100,0,90),10,.32,.44);
    TestTrue(TEXT("Moving attack / stationary target same relative entry"),Same.bHit&&FMath::Abs(Same.Begin-C.Begin)<1.e-10);
    TestFalse(TEXT("Never sweep startup/recovery outside clipped active"),SphereAttackContact(FVector::ZeroVector,FVector::ZeroVector,0,FVector(100,-500,90),FVector(100,500,90),10,0,.2).bHit);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DVisibility,"AnimeMMORPG.U02.D.VisibilityChangesInsideContactInterval",U02DFlags)
bool FU02DVisibility::RunTest(const FString&)
{
    TArray<FTriangle> Triangles;AddBoxTriangles(FTransform(FVector(75,-35,90)),FVector(5,35,90),Triangles);
    FVector O(0,0,90),A(150,-60,90),B(150,60,90);FContactRange Contact{true,0,1};
    auto Visible=[&](double T){FVector End=SphereNearest(O,FMath::Lerp(A,B,T),10);for(auto& Tri:Triangles)if(SegmentTriangleClosed(O,End,Tri))return false;return true;};
    TestFalse(TEXT("First contact is blocked"),Visible(0));TestTrue(TEXT("Later contact emerges"),Visible(1));
    auto First=FirstVisible(O,O,A,B,10,Contact,Triangles,Visible);
    TestTrue(TEXT("Blocked-first interval can emerge"),First.IsSet()&&First.GetValue()>.49&&First.GetValue()<.51&&Visible(First.GetValue()));
    TArray<FTriangle> Slit;AddBoxTriangles(FTransform(FVector(75,-40.8767,90)),FVector(5,50,90),Slit);
    AddBoxTriangles(FTransform(FVector(75,59.1235,90)),FVector(5,50,90),Slit);
    FVector SlitOrigin(0,9.1234,90);
    auto SlitVisible=[&](double T){auto End=SphereNearest(SlitOrigin,FMath::Lerp(A,B,T),1);for(auto& Tri:Slit)if(SegmentTriangleClosed(SlitOrigin,End,Tri))return false;return true;};
    auto Hit=FirstVisible(SlitOrigin,SlitOrigin,A,B,1,Contact,Slit,SlitVisible);
    TestTrue(TEXT("Sub-sample slit is found analytically"),Hit.IsSet()&&SlitVisible(Hit.GetValue()));return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DWorldSweep,"AnimeMMORPG.U02.D.WorldWholeActiveCrossingAndDedup",U02DFlags)
bool FU02DWorldSweep::RunTest(const FString&)
{
    FDWorld W(*this);auto* D=W.Dummy(FVector(150,-500,0));W.Attack();D->SetActorLocation(FVector(150,500,0));W.Resolver->DrainAt(W.Now()+.5);
    TestEqual(TEXT("Whole active crossing, one hit across two hurtboxes"),W.Resolver->Confirmed.Num(),1);
    if(!W.Resolver->Confirmed.IsEmpty()){auto Hit=W.Resolver->Confirmed[0];TestEqual(TEXT("Earlier larger body chosen"),Hit.HurtboxId,uint32(1));TestTrue(TEXT("Timestamp inside active"),Hit.TimestampSeconds>=W.Now()+.16&&Hit.TimestampSeconds<W.Now()+.22);}
    W.Resolver->DrainAt(W.Now()+.6);TestEqual(TEXT("No repeat"),W.Resolver->Confirmed.Num(),1);
    TestEqual(TEXT("Query only"),D->Body->GetCollisionEnabled(),ECollisionEnabled::QueryOnly);
    TestEqual(TEXT("Ignores pawn movement"),D->Body->GetCollisionResponseToChannel(ECC_Pawn),ECR_Ignore);
    TestEqual(TEXT("Capsule ignores obstruction"),W.Source->GetCapsuleComponent()->GetCollisionResponseToChannel(ECC_GameTraceChannel2),ECR_Ignore);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DWalls,"AnimeMMORPG.U02.D.WorldWallPartialHurtboxAndOrigin",U02DFlags)
bool FU02DWalls::RunTest(const FString&)
{
    for(int Case=0;Case<3;++Case)
    {
        FDWorld W(*this);W.Dummy(FVector(150,0,0));
        if(Case==0)W.Wall(FVector(75,0,110),FVector(5,200,110));
        if(Case==1)W.Wall(FVector(75,0,50),FVector(5,200,50));
        if(Case==2)W.Wall(FVector(0,0,90),FVector(5,200,10));
        W.Attack();W.Resolver->DrainAt(W.Now()+.3);TestEqual(TEXT("Full/partial/origin inside"),W.Resolver->Confirmed.Num(),Case==1?1:0);
        if(Case==1&&!W.Resolver->Confirmed.IsEmpty())TestEqual(TEXT("Visible head despite blocked body"),W.Resolver->Confirmed[0].HurtboxId,uint32(2));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DOrder,"AnimeMMORPG.U02.D.WorldTargetsOrderingAndLifetime",U02DFlags)
bool FU02DOrder::RunTest(const FString&)
{
    for(bool Reverse:{false,true})
    {
        FDWorld W(*this);W.Dummy(FVector(100,0,0),Reverse?20:10);W.Dummy(FVector(150,0,0),Reverse?10:20);W.Attack();W.Resolver->DrainAt(W.Now()+.3);
        TestEqual(TEXT("Targets do not obstruct targets"),W.Resolver->Confirmed.Num(),2);
        if(W.Resolver->Confirmed.Num()==2)TestTrue(TEXT("Stable order independent registration"),PawnLess(W.Resolver->Confirmed[0].Id.Target.Pawn,W.Resolver->Confirmed[1].Id.Target.Pawn));
    }
    FDWorld W(*this);auto* D=W.Dummy(FVector(150,-500,0));W.Attack();D->SetActorLocation(FVector(150,500,0),false,nullptr,ETeleportType::TeleportPhysics);
    W.Resolver->DrainAt(W.Now()+.5);TestEqual(TEXT("No teleport sweep"),W.Resolver->Confirmed.Num(),0);TestTrue(TEXT("Continuity break recorded"),W.Resolver->Discontinuities>0);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DReset,"AnimeMMORPG.U02.D.WorldResetAndResolveRevalidation",U02DFlags)
bool FU02DReset::RunTest(const FString&)
{
    FDWorld W(*this);auto* A=W.Dummy(FVector(100,0,0),10);auto* B=W.Dummy(FVector(150,0,0),20);
    W.Resolver->OnGeometryConfirmed.AddLambda([&](const FHitCandidate& C){if(C.Id.Target.Pawn==A->NetworkPawnId)B->ResetLabCombat();});W.Attack();W.Resolver->DrainAt(W.Now()+.3);
    TestEqual(TEXT("Reset rejects queued old life"),W.Resolver->Confirmed.Num(),1);W.Resolver->OnGeometryConfirmed.Clear();
    FDWorld Death(*this);Death.Dummy(FVector(100,0,0),10);Death.Dummy(FVector(150,0,0),20);
    Death.Resolver->OnGeometryConfirmed.AddLambda([&](const FHitCandidate& C){Death.Resolver->MarkDead(C.Id.Action.Source);});Death.Attack();Death.Resolver->DrainAt(Death.Now()+.3);
    TestEqual(TEXT("Invalid source rejects next sorted event; no HP"),Death.Resolver->Confirmed.Num(),1);Death.Resolver->OnGeometryConfirmed.Clear();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DGlobal,"AnimeMMORPG.U02.D.GlobalBatchAcrossSources",U02DFlags)
bool FU02DGlobal::RunTest(const FString&)
{
    for(bool Reverse:{false,true})
    {
        FDWorld W(*this);W.Dummy(FVector(150,0,0),10);
        FTransform X(FVector(0,40,98));auto* B=W.GetTestWorld()->SpawnActorDeferred<AU01Character>(AU01Character::StaticClass(),X,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
        B->NetworkPawnId=FGuid(2,0,0,1);UGameplayStatics::FinishSpawningActor(B,X);B->GetU01Movement()->SetMovementMode(MOVE_Walking);
        W.Attack();B->Combat->SubmitAttackIntent(1,W.Now(),0);
        if(Reverse)FU02CollisionTestAccess::ReverseSources(W.Resolver);
        W.Resolver->OnGeometryConfirmed.AddLambda([&](const FHitCandidate& C)
        {
            TestEqual(TEXT("Lower source ID resolves before higher ID at equal timestamp"),C.Id.Action.Source.Pawn, W.Source->NetworkPawnId);
            W.Resolver->MarkDead({B->NetworkPawnId,1});
        });
        W.Resolver->DrainAt(W.Now()+.3);
        TestEqual(TEXT("Global batch invalidation suppresses other source regardless collection order"),W.Resolver->Confirmed.Num(),1);
        W.Resolver->OnGeometryConfirmed.Clear();
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02DShapes,"AnimeMMORPG.U02.D.ContainmentRoundedCornersAndStepRates",U02DFlags)
bool FU02DShapes::RunTest(const FString&)
{
    TArray<FTriangle> Box;AddBoxTriangles(FTransform(FVector(30,0,90)),FVector(10,20,30),Box);
    TestTrue(TEXT("Inside closed collision mesh even when segment stays internal"),InsideClosedPolyhedron(FVector(30,0,90),Box));
    TestTrue(TEXT("Surface is blocked"),InsideClosedPolyhedron(FVector(20,0,90),Box));
    TestFalse(TEXT("Outside polyhedron"),InsideClosedPolyhedron(FVector(0,0,90),Box));
    TestFalse(TEXT("Sphere cannot hit inflated-box corner without actual rounded overlap"),SphereAttackContact(FVector::ZeroVector,FVector::ZeroVector,0,FVector(210,70,90),FVector(210,70,90),10,0,1).bHit);
    for(double Dt:{1./30,1./60,1./120,.5})
    {
        double First=1,Previous=0;
        for(double Now=Dt;Previous<.4;Now+=Dt)
        {
            const double A=FMath::Max(Previous,.16),B=FMath::Min(Now,.22);
            if(A<=B)
            {
                auto Pos=[](double T){return FVector(100,(T-.2)*10000,90);};
                auto Contact=SphereAttackContact(FVector::ZeroVector,FVector::ZeroVector,0,Pos(Previous),Pos(Now),10,(A-Previous)/(Now-Previous),(B-Previous)/(Now-Previous));
                if(Contact.bHit)
                {
                    double T=FMath::Lerp(Previous,Now,Contact.Begin);
                    if(T>=.16&&T<.22)First=FMath::Min(First,T);
                }
            }
            Previous=Now;
        }
        TestTrue(TEXT("30/60/120/whole-step same relative contact deadline"),FMath::Abs(First-.193)<1.e-8);
    }
    return true;
}
#endif
