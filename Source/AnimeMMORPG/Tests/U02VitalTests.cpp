#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include <limits>
#include "Tests/AutomationCommon.h"
#include "U02/U02VitalModel.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02LabDummy.h"
#include "U02/U02HurtboxComponent.h"
#include "U01/U01Character.h"
#include "Components/BoxComponent.h"
#include "AIController.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "Kismet/GameplayStatics.h"
using namespace AnimeMMORPG::U02;
static constexpr auto U02EFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FU02VitalTestAccess
{
    static void HP(UU02VitalComponent* V,int32 HP){V->State.HP=HP;V->State.bDead=HP==0;V->Publish(V->GetWorld()->GetTimeSeconds());}
};
struct FU02EVitalWorldAccess
{
    static void ReverseSources(UU02CollisionWorld* W){if(W->Sources.Num()==2)W->Sources.Swap(0,1);}
    static bool Replay(UU02CollisionWorld* W){return W->ResolveHit(W->Confirmed[0]);}
};
namespace
{
struct FEWorld : FTestWorldWrapper
{
    FAutomationTestBase& Test;AU01Character* A=nullptr;UU02CollisionWorld* Resolver=nullptr;
    explicit FEWorld(FAutomationTestBase& T):Test(T)
    {
        CreateTestWorld(EWorldType::Game);GetTestWorld()->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        auto* Floor=GetTestWorld()->SpawnActor<AActor>();auto* Box=NewObject<UBoxComponent>(Floor);Floor->SetRootComponent(Box);Box->SetBoxExtent(FVector(10000,10000,50));Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Box->SetCollisionResponseToAllChannels(ECR_Block);Floor->SetActorLocation(FVector(0,0,-50));Box->RegisterComponent();
        A=Pawn(FVector(0,0,98),1);BeginPlayInTestWorld();for(int I=0;I<30;++I)TickTestWorld(1.f/60);
        Resolver=GetTestWorld()->GetSubsystem<UU02CollisionWorld>();Resolver->FixtureCritRoll=.5;Resolver->DrainAt(Now());
    }
    ~FEWorld(){ForwardErrorMessages(&Test);}
    double Now() const {return GetTestWorld()->GetTimeSeconds();}
    AU01Character* Pawn(FVector Position,int Id)
    {
        FTransform X(Position);auto* C=GetTestWorld()->SpawnActorDeferred<AU01Character>(AU01Character::StaticClass(),X,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);C->NetworkPawnId=FGuid(Id,0,0,1);UGameplayStatics::FinishSpawningActor(C,X);
        auto* PC=GetTestWorld()->SpawnActor<AAIController>();PC->bSetControlRotationFromPawnOrientation=false;PC->Possess(C);return C;
    }
    AU02LabDummy* Dummy(FVector P=FVector(150,0,0),int Id=10)
    {
        FTransform X(P);auto* D=GetTestWorld()->SpawnActorDeferred<AU02LabDummy>(AU02LabDummy::StaticClass(),X);D->NetworkPawnId=FGuid(Id,0,0,1);UGameplayStatics::FinishSpawningActor(D,X);return D;
    }
    void Attack(){A->Combat->SubmitAttackIntent(1,Now(),0);}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02EDamage,"AnimeMMORPG.U02.E.DamageFormulaRoundingAndCrit",U02EFlags)
bool FU02EDamage::RunTest(const FString&)
{
    TestEqual(TEXT("Default60"),FVitalModel::Calculate(60,1,0,false),60);
    TestEqual(TEXT("Crit90"),FVitalModel::Calculate(60,1,0,true),90);
    TestEqual(TEXT("Defense after attack then crit and block, round only once"),FVitalModel::Calculate(31,2,100,true,.5),23);
    TestEqual(TEXT("Half up"),FVitalModel::Calculate(1,1,100,false),1);
    TestEqual(TEXT("Final half after all factors"),FVitalModel::Calculate(31,1,100,false),16);
    TestEqual(TEXT("No negative defense"),FVitalModel::Calculate(60,1,-1,false),-1);
    FVitalModel M;auto Crit=M.Apply(60,1,.049999,0);auto Normal=M.Apply(60,1,.05,1);
    TestTrue(TEXT("5 percent strict threshold"),Crit.bCrit&&!Normal.bCrit&&Crit.Damage==90&&Normal.Damage==60);
    TestFalse(TEXT("Nonfinite roll rejected"),M.Apply(60,1,std::numeric_limits<double>::quiet_NaN(),2).bApplied);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02EShields,"AnimeMMORPG.U02.E.ShieldReplaceOrderExpiryAndOverkill",U02EFlags)
bool FU02EShields::RunTest(const FString&)
{
    FVitalModel M;M.AddShield(1,100,10,0);M.AddShield(1,20,20,0);M.AddShield(3,15,15,0);M.AddShield(2,10,15,0);
    auto R=M.Apply(60,1,.5,1);TestEqual(TEXT("Different source adds, same source replaces capacity/deadline"),R.Absorbed,45);
    TestEqual(TEXT("HP after shield"),M.HP,985);TestTrue(TEXT("Earliest deadline then source ascending"),R.ShieldOrder==TArray<uint64>{2,3,1});
    M.AddShield(1,60,5,2);R=M.Apply(60,1,.5,5);TestEqual(TEXT("Exact deadline expired, no epsilon"),R.Absorbed,0);
    M.HP=1;M.AddShield(7,10,20,6);R=M.Apply(60,1,.5,6);TestTrue(TEXT("Overkill clamps HP and emits death once"),R.bDied&&M.HP==0&&M.DeathCount==1&&R.HPDamage==1);
    TestFalse(TEXT("Dead cannot take hit again"),M.Apply(60,1,0,7).bApplied);TestEqual(TEXT("Death once"),M.DeathCount,uint32(1));
    TestFalse(TEXT("Same generation reset forbidden"),M.Reset(1,1000));TestTrue(TEXT("Lab reset increments life"),M.Reset(2,1000));TestTrue(TEXT("Reset clears shield/death"),M.HP==1000&&!M.bDead&&M.Shields.IsEmpty());return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02EWorldDamage,"AnimeMMORPG.U02.E.AuthorityDamageDedupAndOneCritRoll",U02EFlags)
bool FU02EWorldDamage::RunTest(const FString&)
{
    for(double Roll:{.5,0.})
    {
        FEWorld W(*this);auto* D=W.Dummy();W.Resolver->FixtureCritRoll=Roll;W.Attack();W.Resolver->DrainAt(W.Now()+.5);
        TestEqual(TEXT("Default player HP1000"),W.A->Vital->GetSnapshot().HP,1000);TestEqual(TEXT("Dummy600 minus one damage"),D->Vital->GetSnapshot().HP,Roll==0?510:540);
        TestEqual(TEXT("One valid target/action across two hurtboxes"),W.Resolver->DamageResults.Num(),1);TestEqual(TEXT("One roll only after valid resolve"),W.Resolver->CritRolls,uint64(1));
        TestFalse(TEXT("Duplicate confirmed ID cannot mutate damage"),FU02EVitalWorldAccess::Replay(W.Resolver));
        W.Resolver->DrainAt(W.Now()+.6);TestEqual(TEXT("No late repeated roll"),W.Resolver->CritRolls,uint64(1));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02EDeathOrder,"AnimeMMORPG.U02.E.SameTimestampLethalOrderAndDeadMotor",U02EFlags)
bool FU02EDeathOrder::RunTest(const FString&)
{
    for(bool Reverse:{false,true})
    {
    FEWorld W(*this);auto* B=W.Pawn(FVector(150,0,98),2);B->GetU01Movement()->SetMovementMode(MOVE_Walking);
    FU02VitalTestAccess::HP(W.A->Vital,60);FU02VitalTestAccess::HP(B->Vital,60);W.Resolver->bCharacterFixtureTargets=true;
    W.Attack();B->Combat->SubmitAttackIntent(1,W.Now(),180);if(Reverse)FU02EVitalWorldAccess::ReverseSources(W.Resolver);W.Resolver->DrainAt(W.Now()+.3);
    TestEqual(TEXT("Lower source kills first at identical time"),B->Vital->GetSnapshot().HP,0);TestEqual(TEXT("Dead source next lethal event rejected"),W.A->Vital->GetSnapshot().HP,60);
    TestEqual(TEXT("One damage and one RNG roll"),W.Resolver->DamageResults.Num(),1);TestEqual(TEXT("One roll"),W.Resolver->CritRolls,uint64(1));
    TestEqual(TEXT("One actual death"),B->Vital->GetSnapshot().DeathCount,uint32(1));TestTrue(TEXT("Real Defeated motor lock"),(B->GetU01Movement()->GetLockMask()&uint8(EU01MotorLock::Defeated))!=0);
    TestEqual(TEXT("Death cancels pending action presentation"),B->Combat->GetCombatSnapshot().Phase,uint8(EPhase::Cancelled));
    B->GetU01Movement()->SetMotorLock(EU01MotorLock::Defeated,false);TestTrue(TEXT("Old U01 fixture cannot clear actual HP0 Defeated"),(B->GetU01Movement()->GetLockMask()&uint8(EU01MotorLock::Defeated))!=0);
    W.TickTestWorld(.35f);TestTrue(TEXT("Real combat lab reset restores dead pawn"),B->Combat->ResetLabCombat());
    TestTrue(TEXT("Reset full HP, new life and clears actual Defeated"),B->Vital->GetSnapshot().HP==1000&&B->Vital->GetSnapshot().Generation==2&&!B->Vital->GetSnapshot().bDead&&(B->GetU01Movement()->GetLockMask()&uint8(EU01MotorLock::Defeated))==0);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02EReset,"AnimeMMORPG.U02.E.ResetRejectsOldLifeAndClearsShield",U02EFlags)
bool FU02EReset::RunTest(const FString&)
{
    FEWorld W(*this);auto* First=W.Dummy(FVector(100,0,0),10);auto* Second=W.Dummy(FVector(150,0,0),20);
    Second->Vital->AddFixtureShield(1,50,W.Now()+10,W.Now());const FLifeId Old=Second->Body->GetSubject();
    W.Resolver->OnGeometryConfirmed.AddLambda([&](const FHitCandidate& H){if(H.Id.Target.Pawn==First->NetworkPawnId)Second->ResetLabCombat();});
    W.Attack();W.Resolver->DrainAt(W.Now()+.3);
    TestEqual(TEXT("Old queued life not damaged"),Second->Vital->GetSnapshot().HP,600);TestEqual(TEXT("Reset shield cleared"),Second->Vital->GetSnapshot().Shield,0);TestEqual(TEXT("Life incremented"),Second->Vital->GetSnapshot().Generation,uint64(2));
    FHitCandidate Stale;Stale.Id.Target=Old;Stale.TimestampSeconds=W.Now()+.2;TestFalse(TEXT("Vital revalidates stale life before mutation"),Second->Vital->ApplyResolved(Stale,1,0).bApplied);
    TestEqual(TEXT("Stale candidate no second roll"),W.Resolver->CritRolls,uint64(1));W.Resolver->OnGeometryConfirmed.Clear();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02ECancel,"AnimeMMORPG.U02.E.StartupCancelNoDamageActiveCancelRejected",U02EFlags)
bool FU02ECancel::RunTest(const FString&)
{
    FEWorld Cancel(*this);auto* D=Cancel.Dummy();Cancel.Attack();TestTrue(TEXT("Real startup cancel"),Cancel.A->Combat->CancelAction(ECancel::Dodge));Cancel.Resolver->DrainAt(Cancel.Now()+.3);
    TestEqual(TEXT("No damage / RNG after startup cancellation"),D->Vital->GetSnapshot().HP,600);TestEqual(TEXT("No roll"),Cancel.Resolver->CritRolls,uint64(0));
    FEWorld Active(*this);auto* Target=Active.Dummy();Active.Attack();for(int I=0;I<21;++I)Active.TickTestWorld(1.f/120);
    TestFalse(TEXT("Active guard cannot cancel"),Active.A->Combat->CancelAction(ECancel::Guard));Active.Resolver->DrainAt(Active.Now()+.2);TestEqual(TEXT("One damage remains"),Target->Vital->GetSnapshot().HP,540);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02EShieldClock,"AnimeMMORPG.U02.E.ShieldExpiryUsesHitTimestampBeforeFrameEnd",U02EFlags)
bool FU02EShieldClock::RunTest(const FString&)
{
    FEWorld W(*this);auto* D=W.Dummy();D->Vital->AddFixtureShield(1,60,W.Now()+.2,W.Now());W.Attack();W.Resolver->DrainAt(W.Now()+.5);
    TestEqual(TEXT("Hit at .16 absorbs shield alive then, even though endpoint .5 is after expiry"),D->Vital->GetSnapshot().HP,600);
    TestEqual(TEXT("One shield consumption"),W.Resolver->DamageResults.Num(),1);
    if(!W.Resolver->DamageResults.IsEmpty())TestEqual(TEXT("Absorbed60"),W.Resolver->DamageResults[0].Result.Absorbed,60);
    return true;
}
#endif
