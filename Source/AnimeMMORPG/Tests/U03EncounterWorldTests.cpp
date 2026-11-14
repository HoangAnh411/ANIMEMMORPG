#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Algo/Reverse.h"
#include "U03/U03Encounter.h"
#include "U03/U03TargetModel.h"
#include "U01/U01PlayerController.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02VitalComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
using namespace AnimeMMORPG;
using namespace AnimeMMORPG::U03;
struct FU03C2Access
{
    static void HP(AU01Character* C,int32 HP){C->Vital->State.HP=HP;C->Vital->Publish(C->GetWorld()->GetTimeSeconds());}
    static void Reverse(UU02CollisionWorld* C){Algo::Reverse(C->Sources);Algo::Reverse(C->Hurts);}
    static bool Stale(UU02CollisionWorld* C,U02::FHitCandidate H){return C->ResolveHit(H);}
    static FTimelineModel* Model(AU01Character* C){return C->Combat->Model.Get();}
    static uint64 Watermark(AU01Character* C){return C->Combat->AdmissionWatermark;}
};
namespace {
constexpr auto C2WorldFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FC2World:FTestWorldWrapper
{
    AU01PlayerController* PC;AU01Character* Player;AU03Encounter* Encounter;UU02CollisionWorld* Collision;
    FC2World(FVector PlayerPosition=FVector(150,0,98.15),FVector MonsterPosition=FVector(0,0,98.15))
    {
        CreateTestWorld(EWorldType::Game);auto* W=GetTestWorld();W->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        auto* Floor=W->SpawnActor<AActor>();auto* Shape=NewObject<UBoxComponent>(Floor);Floor->SetRootComponent(Shape);Shape->SetBoxExtent(FVector(20000,20000,50));Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Shape->SetCollisionResponseToAllChannels(ECR_Block);Shape->RegisterComponent();Floor->SetActorLocation(FVector(0,0,-50));
        Player=W->SpawnActor<AU01Character>(PlayerPosition,FRotator(0,180,0));PC=W->SpawnActor<AU01PlayerController>();PC->Possess(Player);
        BeginPlayInTestWorld();for(int I=0;I<10;++I)TickTestWorld(1.f/60);
        Collision=W->GetSubsystem<UU02CollisionWorld>();Collision->FixtureCritRoll=.5;
        Encounter=W->SpawnActor<AU03Encounter>();Encounter->Initialize(PC,Player,FTransform(FRotator(0,180,0),PlayerPosition),FTransform(FRotator::ZeroRotator,MonsterPosition));
        Monster()->GetU01Movement()->SetMovementMode(MOVE_Walking);Collision->DrainAt(W->GetTimeSeconds());
    }
    AU01Character* Monster(){return Encounter->GetSnapshot().Monster;}
    void Run(double Seconds,double Step=1./60.){for(double T=0;T<Seconds;){const double Dt=FMath::Min(Step,Seconds-T);TickTestWorld(float(Dt));T+=Dt;}}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldMonster,"AnimeMMORPG.U03.C2.WorldMonsterDamageDefenseAndNoFixtureFlag",C2WorldFlags)
bool FC2WorldMonster::RunTest(const FString&)
{
    for(int Defense=0;Defense<3;++Defense)
    {
        FC2World W;TestFalse(TEXT("production never enables fixture targeting"),W.Collision->bCharacterFixtureTargets);
        TestTrue(TEXT("owned pair allowed"),AU03Encounter::CanDamage(W.Player,W.Monster()));
        if(Defense==1)W.Player->Combat->SubmitCombatIntent(ECommand::Guard,1,0,180);
        W.Run(.51);
        if(Defense==2)W.Player->Combat->SubmitCombatIntent(ECommand::Guard,1,0,180);
        W.Run(.25);
        TestEqual(TEXT("Monster600HP"),W.Monster()->Vital->GetSnapshot().MaxHP,600);
        TestEqual(TEXT("normal100 / block30 / parry0"),W.Player->Vital->GetSnapshot().HP,Defense==0?900:Defense==1?970:1000);
        TestEqual(TEXT("no automatic hardCC"),W.Player->Combat->GetCombatSnapshot().HardCC,uint8(0));
        TestEqual(TEXT("no automatic Interrupt"),W.Player->Combat->GetCombatSnapshot().InterruptSequence,uint64(0));
        TestEqual(TEXT("Monster definition captured"),W.Monster()->Combat->GetCombatSnapshot().DefinitionId,uint8(EAction::Monster));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldRetry,"AnimeMMORPG.U03.C2.WorldRetryTransactionStaleLifeAndOwnership",C2WorldFlags)
bool FC2WorldRetry::RunTest(const FString&)
{
    for(bool Win:{true,false})
    {
        FC2World W;const auto Old=W.Encounter->GetSnapshot();const auto Life=W.Monster()->Vital->GetLife();
        FU03C2Access::HP(Win?W.Monster():W.Player,1);
        if(Win)W.Player->Combat->SubmitCombatIntent(ECommand::Attack,7,0,180);
        W.Run(.8);
        TestEqual(TEXT("server terminal"),W.Encounter->GetSnapshot().Result,uint8(Win?EEncounterResult::Won:EEncounterResult::Lost));
        auto* Unowned=W.GetTestWorld()->SpawnActor<AU01PlayerController>();
        TestFalse(TEXT("unowned"),W.Encounter->Retry(Unowned,Old.Id,1,1));
        TestFalse(TEXT("wrong ID"),W.Encounter->Retry(W.PC,FGuid::NewGuid(),1,1));
        TestFalse(TEXT("stale revision"),W.Encounter->Retry(W.PC,Old.Id,0,1));
        const uint64 Watermark=FU03C2Access::Watermark(W.Player);
        TestTrue(TEXT("owned Retry"),W.Encounter->Retry(W.PC,Old.Id,1,2));
        TestEqual(TEXT("new revision"),W.Encounter->GetSnapshot().Revision,uint64(2));
        TestEqual(TEXT("Running published last"),W.Encounter->GetSnapshot().Result,uint8(EEncounterResult::Running));
        TestEqual(TEXT("playerHP"),W.Player->Vital->GetSnapshot().HP,1000);TestEqual(TEXT("monsterHP"),W.Monster()->Vital->GetSnapshot().HP,600);
        TestEqual(TEXT("new monster life"),W.Monster()->Vital->GetLife().Generation,Life.Generation+1);
        TestEqual(TEXT("watermark preserved"),FU03C2Access::Watermark(W.Player),Watermark);
        TestEqual(TEXT("energy"),W.Player->Combat->GetCombatSnapshot().Energy,100.);TestEqual(TEXT("charges"),W.Player->Combat->GetCombatSnapshot().DodgeCharges,2);
        TestEqual(TEXT("cooldown"),W.Player->Combat->GetCombatSnapshot().EReadyAt,0.);TestEqual(TEXT("posture"),W.Player->Combat->GetCombatSnapshot().Posture,100.);
        TestFalse(TEXT("no old pending"),FU03C2Access::Model(W.Player)->GetPending().IsSet());
        U02::FHitCandidate Stale;Stale.Id.Action={Life,1};Stale.Id.Target=W.Player->Vital->GetLife();Stale.TimestampSeconds=W.GetTestWorld()->GetTimeSeconds();Stale.RawDamage=100;
        TestFalse(TEXT("old source cannot damage new life"),FU03C2Access::Stale(W.Collision,Stale));
        TestFalse(TEXT("duplicate Retry"),W.Encounter->Retry(W.PC,Old.Id,2,2));
        TestFalse(TEXT("Running Retry"),W.Encounter->Retry(W.PC,Old.Id,2,3));
        W.Encounter->Close(W.GetTestWorld()->GetTimeSeconds());TestFalse(TEXT("closed Retry"),W.Encounter->Retry(W.PC,Old.Id,2,4));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2TargetModel,"AnimeMMORPG.U03.C2.TargetRankingRetentionAndVisibilityTimer",C2WorldFlags)
bool FC2TargetModel::RunTest(const FString&)
{
    FTargetRank A{1,100,TEXT("b")},B{2,1,TEXT("a")};TestTrue(TEXT("screen first"),A<B);B.ScreenDistance=1;TestTrue(TEXT("3D second"),B<A);B.WorldDistance=100;TestTrue(TEXT("stable subject third"),B<A);
    for(double Delta:{-.000001,0.,.000001})
    {FTargetRetention R;TestEqual(TEXT("retention30m inclusive"),R.Update(0,3000+Delta,true,true,true),Delta<=0);R={};R.Update(4,100,true,true,false);TestEqual(TEXT("continuous1s half-open"),R.Update(5+Delta,100,true,true,false),Delta<0);}
    FTargetRetention R;R.Update(0,100,true,true,false);R.Update(.9,100,true,true,true);TestTrue(TEXT("visible resets occlusion"),R.Update(1.1,100,true,true,false));
    TestFalse(TEXT("death"),R.Update(1.2,100,false,true,true));TestFalse(TEXT("new life"),R.Update(1.2,100,true,false,true));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldIsolation,"AnimeMMORPG.U03.C2.WorldPairIsolationAndRetryNeighbor",C2WorldFlags)
bool FC2WorldIsolation::RunTest(const FString&)
{
    FC2World W;
    auto* P2=W.GetTestWorld()->SpawnActor<AU01Character>(FVector(150,95,98.15),FRotator(0,180,0));auto* PC2=W.GetTestWorld()->SpawnActor<AU01PlayerController>();PC2->Possess(P2);
    auto* E2=W.GetTestWorld()->SpawnActor<AU03Encounter>();E2->Initialize(PC2,P2,FTransform(FRotator(0,180,0),FVector(150,95,98.15)),FTransform(FRotator::ZeroRotator,FVector(0,95,98.15)));
    E2->GetSnapshot().Monster->GetU01Movement()->SetMovementMode(MOVE_Walking);
    TestFalse(TEXT("cross-player damage forbidden"),AU03Encounter::CanDamage(W.Player,P2));
    TestFalse(TEXT("other station monster forbidden"),AU03Encounter::CanDamage(W.Player,E2->GetSnapshot().Monster));
    TestFalse(TEXT("monster cannot switch owner"),AU03Encounter::CanDamage(W.Monster(),P2));
    FU03C2Access::HP(W.Monster(),1);W.Player->Combat->SubmitCombatIntent(ECommand::Attack,1,0,180);W.Run(.3);
    TestEqual(TEXT("A wins"),W.Encounter->GetSnapshot().Result,uint8(EEncounterResult::Won));
    const auto Before=E2->GetSnapshot();const auto Vital=P2->Vital->GetSnapshot();const auto Combat=P2->Combat->GetCombatSnapshot();
    TestTrue(TEXT("RetryA"),W.Encounter->Retry(W.PC,W.Encounter->GetSnapshot().Id,1,1));
    TestEqual(TEXT("B revision unchanged"),E2->GetSnapshot().Revision,Before.Revision);TestEqual(TEXT("B result unchanged"),E2->GetSnapshot().Result,Before.Result);
    TestEqual(TEXT("B HP unchanged"),P2->Vital->GetSnapshot().HP,Vital.HP);TestEqual(TEXT("B life unchanged"),P2->Vital->GetSnapshot().Generation,Vital.Generation);
    TestEqual(TEXT("B action unchanged"),P2->Combat->GetCombatSnapshot().ActionSequence,Combat.ActionSequence);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldInterrupt,"AnimeMMORPG.U03.C2.WorldEInterruptQAndFreshAdmission",C2WorldFlags)
bool FC2WorldInterrupt::RunTest(const FString&)
{
    for(auto Command:{ECommand::E,ECommand::Q})for(bool Reverse:{false,true})
    {
        FC2World W;if(Reverse)FU03C2Access::Reverse(W.Collision);
        W.Player->Combat->SubmitCombatIntent(Command,1,0,180);W.Run(.4);
        const auto S=W.Monster()->Combat->GetCombatSnapshot();
        TestEqual(TEXT("E only Interrupts"),S.InterruptSequence,uint64(Command==ECommand::E?1:0));
        TestEqual(TEXT("no stun penalty"),S.HardCC,uint8(0));
        TestTrue(TEXT("monster keeps proper definition"),S.DefinitionId==uint8(EAction::Monster));
        if(Command==ECommand::E)TestTrue(TEXT("fresh action admission after interruption"),S.ActionSequence>1);
    }
    return true;
}
#endif
