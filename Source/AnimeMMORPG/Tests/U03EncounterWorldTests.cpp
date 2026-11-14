#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Algo/Reverse.h"
#include "U03/U03Encounter.h"
#include "U03/U03MonsterStateComponent.h"
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
    static void Capture(UU02CollisionWorld* C,double At){C->Capture(At);}
    static void Control(AU01Character* C,bool Playing,U02::FLifeId Life){C->Combat->ServerControlPlaying_Implementation(Playing,Life.Pawn,Life.Generation);}
    static void Identity( AU01Character* C,FGuid Id)
    {
        // Deterministic native fixture setup before the simultaneous-contact probe, never a product identity API.
        auto* W=C->GetWorld()->GetSubsystem<UU02CollisionWorld>();W->MarkDead(C->Vital->GetLife());C->NetworkPawnId=Id;
        auto* B=C->Combat.Get();B->Model=MakeUnique<FTimelineModel>(U02::FLifeId{Id,1},C->GetWorld()->GetTimeSeconds());B->Snapshot=FU02RepCombatSnapshot();B->QueuedIntents.Empty();B->QueuedAim.Empty();B->AdmissionWatermark=B->LastCommand=0;B->Publish(B->Model->Time(),true);W->RebaseResetSubject(C);
    }
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
        TestTrue(TEXT("populate real resource/CD state"),W.Collision->FixtureSpend(W.Player->Combat,EAction::E));
        W.Player->Vital->AddFixtureShield(77,50,W.GetTestWorld()->GetTimeSeconds()+20,W.GetTestWorld()->GetTimeSeconds());
        FU03C2Access::HP(Win?W.Monster():W.Player,1);
        if(Win)W.Player->Combat->SubmitCombatIntent(ECommand::Attack,7,0,180);
        W.Run(.8);
        TestEqual(TEXT("server terminal"),W.Encounter->GetSnapshot().Result,uint8(Win?EEncounterResult::Won:EEncounterResult::Lost));
        auto* Unowned=W.GetTestWorld()->SpawnActor<AU01PlayerController>();
        TestFalse(TEXT("unowned"),W.Encounter->Retry(Unowned,Old.Id,1,1));
        TestFalse(TEXT("wrong ID"),W.Encounter->Retry(W.PC,FGuid::NewGuid(),1,1));
        TestFalse(TEXT("stale revision"),W.Encounter->Retry(W.PC,Old.Id,0,1));
        const uint64 Watermark=FU03C2Access::Watermark(W.Player);const auto OldPlayerLife=W.Player->Vital->GetLife();
        TestTrue(TEXT("cooldown existed before Retry"),W.Player->Combat->GetCombatSnapshot().EReadyAt>W.GetTestWorld()->GetTimeSeconds());
        TestTrue(TEXT("owned Retry"),W.Encounter->Retry(W.PC,Old.Id,1,2));
        TestEqual(TEXT("new revision"),W.Encounter->GetSnapshot().Revision,uint64(2));
        TestEqual(TEXT("Running published last"),W.Encounter->GetSnapshot().Result,uint8(EEncounterResult::Running));
        TestEqual(TEXT("server FSM component reset in the same transaction"),CastChecked<AU03Monster>(W.Monster())->State->GetServerState(),EMonsterState::Idle);
        TestEqual(TEXT("playerHP"),W.Player->Vital->GetSnapshot().HP,1000);TestEqual(TEXT("monsterHP"),W.Monster()->Vital->GetSnapshot().HP,600);
        TestEqual(TEXT("shield cleared"),W.Player->Vital->GetSnapshot().Shield,0);
        TestTrue(TEXT("Retry preserves server AwaitingResume gate"),W.Player->GetU01Movement()->IsMotorLocked());
        FU03C2Access::Control(W.Player,true,OldPlayerLife);W.Player->GetU01Movement()->UpdateFromCompressedFlags(0);
        TestTrue(TEXT("old control packet and move flags cannot reopen new life"),W.Player->GetU01Movement()->IsMotorLocked());
        FU03C2Access::Control(W.Player,true,W.Player->Vital->GetLife());TestFalse(TEXT("explicit new-life Resume unlocks"),W.Player->GetU01Movement()->IsMotorLocked());
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
    {TestEqual(TEXT("selection20m inclusive"),WithinTargetSelectionRange(FMath::Square(2000+Delta)),Delta<=0);FTargetRetention R;TestEqual(TEXT("retention30m inclusive"),R.Update(0,3000+Delta,true,true,true),Delta<=0);R={};R.Update(4,100,true,true,false);TestEqual(TEXT("continuous1s half-open"),R.Update(5+Delta,100,true,true,false),Delta<0);}
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldScheduledBoundary,"AnimeMMORPG.U03.C2.WorldScheduledDistanceAndReturnLatch",C2WorldFlags)
bool FC2WorldScheduledBoundary::RunTest(const FString&)
{
    FC2World W;
    TFunction<FVector(AActor*,double)> Path=[&](AActor* A,double T){return FVector(2000*T+(A==W.Player?150:0),0,2.15);};
    TArray<U02::FTriangle> Environment;
    const double Boundary=W.Encounter->NextBoundary(.6,1.,Path,Environment);
    TestEqual(TEXT("exact leash trajectory root"),Boundary,.75);
    const double After=W.Encounter->NextBoundary(.75,1.,Path,Environment);TestTrue(TEXT("strict exit is separately scheduled"),After>.75&&After<.750001);
    // Observation-only callback test: no model mutation outside a real world barrier is counted.
    auto O=FMonsterObservation{};O.SpawnDistance=1500;O.TargetDistance=150;O.bAction=true;
    TestEqual(TEXT("15m inclusive"),DecideMonster(EMonsterState::Action,O).State,EMonsterState::Action);
    O.SpawnDistance=1500.000001;
    TestEqual(TEXT("exit chooses Return"),DecideMonster(EMonsterState::Action,O).State,EMonsterState::Return);
    O.SpawnDistance=100;O.TargetDistance=100;TestEqual(TEXT("Return latches despite target"),DecideMonster(EMonsterState::Return,O).State,EMonsterState::Return);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldReturn,"AnimeMMORPG.U03.C2.WorldReturnPhaseCutoffLatchAndOneReset",C2WorldFlags)
bool FC2WorldReturn::RunTest(const FString&)
{
    // Fixture placement drives exact observations; authored navigation/physical return is a separate gate.
    for(double Phase:{.2,.65,.9})for(bool Reverse:{false,true})
    {
        FC2World W;if(Reverse)FU03C2Access::Reverse(W.Collision);
        W.Monster()->SetActorLocation(FVector(300,0,98.15));W.Player->SetActorLocation(FVector(450,0,98.15));
        FU03C2Access::HP(W.Monster(),400);W.Run(Phase);
        const int Hits=W.Collision->DamageResults.Num();const auto OldLife=W.Monster()->Vital->GetLife();
        W.Player->SetActorLocation(FVector(1400,0,98.15));W.Run(.02);
        TestEqual(TEXT("loss enters Return in every phase"),W.Encounter->GetSnapshot().AI,uint8(EMonsterState::Return));
        TestFalse(TEXT("Return releases action lock"),W.Monster()->Combat->GetCombatSnapshot().bLocked);
        TestEqual(TEXT("earlier confirmed hit retained, future suppressed"),W.Collision->DamageResults.Num(),Hits);
        W.Player->SetActorLocation(FVector(450,0,98.15));W.Run(.02);
        TestEqual(TEXT("no rechase before reset"),W.Encounter->GetSnapshot().AI,uint8(EMonsterState::Return));
        TestEqual(TEXT("no early heal"),W.Monster()->Vital->GetSnapshot().HP,400);
        TestEqual(TEXT("no early life"),W.Monster()->Vital->GetLife().Generation,OldLife.Generation);
        W.Monster()->SetActorLocation(FVector(49,0,98.15));W.Run(.04);
        TestEqual(TEXT("reset inside50cm"),W.Monster()->Vital->GetLife().Generation,OldLife.Generation+1);
        TestEqual(TEXT("fullHP at reset"),W.Monster()->Vital->GetSnapshot().HP,600);
        W.Run(.2);TestEqual(TEXT("reset exactly once"),W.Monster()->Vital->GetLife().Generation,OldLife.Generation+1);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldLOS,"AnimeMMORPG.U03.C2.WorldMovingLOSLongShortAndCollectionOrder",C2WorldFlags)
bool FC2WorldLOS::RunTest(const FString&)
{
    TArray<double> Cutoffs;
    for(bool Short:{false,true})for(bool Reverse:{false,true})
    {
        FC2World W;if(Reverse)FU03C2Access::Reverse(W.Collision);
        W.Monster()->SetActorLocation(FVector(300,0,98.15));W.Player->SetActorLocation(FVector(450,0,98.15));
        auto* Wall=W.GetTestWorld()->SpawnActor<AActor>();auto* Shape=NewObject<UBoxComponent>(Wall);Wall->SetRootComponent(Shape);Shape->SetBoxExtent(FVector(10,100,140));Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Shape->SetCollisionResponseToAllChannels(ECR_Block);Shape->RegisterComponent();Wall->SetActorLocation(FVector(375,200,100));
        const double Start=W.GetTestWorld()->GetTimeSeconds();FU03C2Access::Capture(W.Collision,Start);
        const auto Life=W.Monster()->Vital->GetLife();
        const int Steps=Short?20:1;
        for(int I=1;I<=Steps;++I){W.Player->SetActorLocation(FVector(450,400.*I/Steps,98.15));W.Collision->DrainAt(Start+.5*I/Steps);}
        const auto* Cut=W.Collision->LifecycleAudit.FindByPredicate([&](const auto& E){return E.Life==Life&&E.Reason==ECutoff::Return&&E.Accepted;});
        TestNotNull(TEXT("moving feet+90 LOS schedules a real Return cutoff"),Cut);if(!Cut)return false;
        AddInfo(FString::Printf(TEXT("C2_LOS short=%d reverse=%d start=%.17g cutoff=%.17g relative=%.17g"),Short,Reverse,Start,Cut->At,Cut->At-Start));
        Cutoffs.Add(Cut->At-Start);TestTrue(TEXT("cutoff occurs inside movement span"),Cut->At>Start&&Cut->At<Start+.5);
        TestEqual(TEXT("startup hit suppressed"),W.Collision->DamageResults.Num(),0);TestEqual(TEXT("Return remains latched"),W.Encounter->GetSnapshot().AI,uint8(EMonsterState::Return));
    }
    for(double T:Cutoffs)TestTrue(TEXT("same physical LOS cutoff under collection reversal and partitioning"),FMath::Abs(T-Cutoffs[0])<1.e-10);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldTracking,"AnimeMMORPG.U03.C2.WorldStartupTrackingActiveLockAndGravity",C2WorldFlags)
bool FC2WorldTracking::RunTest(const FString&)
{
    for(bool Short:{false,true})for(bool Reverse:{false,true})
    {
        FC2World W;if(Reverse)FU03C2Access::Reverse(W.Collision);
        const double Start=W.GetTestWorld()->GetTimeSeconds();const int Steps=Short?36:1;
        W.Monster()->GetU01Movement()->Velocity=FVector(100,100,-30);
        for(int I=1;I<=Steps;++I)
        {const double Alpha=double(I)/Steps;W.Player->SetActorLocation(FVector(150*(1-Alpha),150*Alpha,98.15));W.Collision->DrainAt(Start+.60*Alpha);}
        TestEqual(TEXT("final startup sample tracks target at active entry"),W.Monster()->Combat->GetCombatSnapshot().AimYawDegrees,90.);
        TestEqual(TEXT("new-yaw active entry geometry resolves once"),W.Player->Vital->GetSnapshot().HP,900);
        TestEqual(TEXT("horizontal action stop"),W.Monster()->GetU01Movement()->Velocity.SizeSquared2D(),0.);
        TestEqual(TEXT("AI stop preserves falling velocity"),W.Monster()->GetU01Movement()->Velocity.Z,-30.);
        W.Player->SetActorLocation(FVector(150,0,98.15));W.Collision->DrainAt(Start+.65);
        TestEqual(TEXT("active yaw locked"),W.Monster()->Combat->GetCombatSnapshot().AimYawDegrees,90.);
        W.Player->SetActorLocation(FVector(0,-150,98.15));W.Collision->DrainAt(Start+.9);
        TestEqual(TEXT("recovery yaw locked"),W.Monster()->Combat->GetCombatSnapshot().AimYawDegrees,90.);
        TestEqual(TEXT("dedup remains single hit"),W.Player->Vital->GetSnapshot().HP,900);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2WorldSimultaneousLethal,"AnimeMMORPG.U03.C2.WorldSameTimestampLethalUsesResolverOrder",C2WorldFlags)
bool FC2WorldSimultaneousLethal::RunTest(const FString&)
{
    for(bool PlayerFirst:{false,true})for(bool Reverse:{false,true})
    {
        FC2World W;FU03C2Access::Identity(W.Player,FGuid(PlayerFirst?1:2,0,0,1));FU03C2Access::Identity(W.Monster(),FGuid(PlayerFirst?2:1,0,0,1));
        if(Reverse)FU03C2Access::Reverse(W.Collision);
        FU03C2Access::HP(W.Player,1);FU03C2Access::HP(W.Monster(),1);
        const double Start=W.GetTestWorld()->GetTimeSeconds();W.Collision->DrainAt(Start);
        const double Contact=Start+.60,PlayerStart=Contact-.16;
        TestEqual(TEXT("exact common contact timestamp without deadline epsilon"),PlayerStart+.16,Contact);
        W.Collision->DrainAt(PlayerStart);W.Player->Combat->SubmitCombatIntent(ECommand::Attack,1,0,180);W.Collision->DrainAt(PlayerStart);W.Collision->DrainAt(Contact);
        TestEqual(TEXT("first resolver source decides Won/Lost; no draw"),W.Encounter->GetSnapshot().Result,uint8(PlayerFirst?EEncounterResult::Won:EEncounterResult::Lost));
        TestEqual(TEXT("lethal source invalidated before the next same-time event"),W.Collision->DamageResults.Num(),1);
        if(W.Collision->DamageResults.Num()!=1)return false;
        TestEqual(TEXT("actual hit timestamp"),W.Collision->DamageResults[0].Hit.TimestampSeconds,Contact);
        TestEqual(TEXT("survivor cannot receive the cancelled counter-hit"),(PlayerFirst?W.Player:W.Monster())->Vital->GetSnapshot().HP,1);
    }
    return true;
}
#endif
