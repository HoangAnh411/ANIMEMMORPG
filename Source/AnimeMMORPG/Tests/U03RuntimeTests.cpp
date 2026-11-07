#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U01/U01Character.h"
#include "U01/U01Settings.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02LabDummy.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02NetworkState.h"
#include "Components/BoxComponent.h"
#include "AIController.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "Kismet/GameplayStatics.h"
struct FU03RuntimeAccess
{
    static void HP(UU02VitalComponent* V,int32 Value){V->State.HP=Value;V->State.bDead=false;V->Publish(V->GetWorld()->GetTimeSeconds());}
    static void Reverse(UU02CollisionWorld* W){Algo::Reverse(W->Sources);}
    static void Interrupt(UU02CollisionWorld* W,UU02CombatComponent* C){W->FixtureInterruptActions.Add({{C->GetCombatSnapshot().PawnId,C->GetCombatSnapshot().LifeGeneration},1});}
    static void Command(UU02CombatComponent* C,uint64 Seq,uint64 Life,FGuid Pawn){C->ServerAttack_Implementation(Seq,0,0,Pawn,Life);}
};
namespace
{
constexpr auto U03A1Flags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FU03A1World:FTestWorldWrapper
{
    AU01Character* Player=nullptr;AU02LabDummy* Dummy=nullptr;UU02CollisionWorld* Collision=nullptr;AU02NetworkState* Network=nullptr;
    FU03A1World()
    {
        CreateTestWorld(EWorldType::Game);auto* W=GetTestWorld();W->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        auto* Floor=W->SpawnActor<AActor>();auto* B=NewObject<UBoxComponent>(Floor);Floor->SetRootComponent(B);B->SetBoxExtent(FVector(10000,10000,50));B->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);B->SetCollisionResponseToAllChannels(ECR_Block);B->RegisterComponent();Floor->SetActorLocation(FVector(0,0,-50));
        Player=SpawnPlayer(FVector(0,0,98),1);
        Dummy=W->SpawnActor<AU02LabDummy>(FVector(150,0,0),FRotator::ZeroRotator);
        Network=W->SpawnActor<AU02NetworkState>();
        BeginPlayInTestWorld();for(int32 I=0;I<30;++I)TickTestWorld(1.f/60);
        Collision=W->GetSubsystem<UU02CollisionWorld>();Collision->FixtureCritRoll=.5;
    }
    AU01Character* SpawnPlayer(FVector P,uint32 Id)
    {
        FTransform X(P);auto* C=GetTestWorld()->SpawnActorDeferred<AU01Character>(AU01Character::StaticClass(),X,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);C->NetworkPawnId=FGuid(Id,0,0,1);UGameplayStatics::FinishSpawningActor(C,X);
        auto* PC=GetTestWorld()->SpawnActor<AAIController>();PC->bSetControlRotationFromPawnOrientation=false;PC->Possess(C);return C;
    }
    double Now()const{return GetTestWorld()->GetTimeSeconds();}
    void Press(uint64 Seq,double At,double Yaw=0){Player->Combat->SubmitAttackIntent(Seq,Now(),Yaw);Collision->DrainAt(At);}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Combo,"AnimeMMORPG.U03.A1.WorldComboAndNineHitDeath",U03A1Flags)
bool FU03A1Combo::RunTest(const FString&)
{
    FU03A1World W;const double S=W.Now();uint64 Seq=0;
    for(int32 Cycle=0;Cycle<3;++Cycle)
    {
        const double Start=S+Cycle*(.40+.45+.60);
        W.Press(++Seq,Start);W.Press(++Seq,Start+.30);W.Press(++Seq,Start+.75);W.Collision->DrainAt(Start+.40+.45+.60);
        TestEqual(TEXT("three geometry/vital contacts per combo"),W.Collision->DamageResults.Num(),(Cycle+1)*3);
        if(Cycle==0)TestEqual(TEXT("one220raw combo leaves380HP"),W.Dummy->Vital->GetSnapshot().HP,380);
    }
    int32 Raw=0,HPDamage=0;
    for(int32 I=0;I<W.Collision->DamageResults.Num();++I)
    {
        const auto& R=W.Collision->DamageResults[I];Raw+=R.Hit.RawDamage;HPDamage+=R.Result.HPDamage;
        TestEqual(TEXT("captured definition cycles1/2/3"),R.Hit.DefinitionId,uint8(I%3));
        TestEqual(TEXT("captured raw per action"),R.Hit.RawDamage,I%3==0?60:I%3==1?70:90);
        AddInfo(FString::Printf(TEXT("U03A1_HIT action=%llu definition=%u raw=%d time=%.17g hpBefore=%d hpAfter=%d death=%d"),R.Hit.Id.Action.Sequence,R.Hit.DefinitionId,R.Hit.RawDamage,R.Hit.TimestampSeconds,R.Result.BeforeHP,R.Result.AfterHP,R.Result.bDied));
    }
    TestEqual(TEXT("raw660 is distinct from HP lost600"),Raw,660);TestEqual(TEXT("actual HP loss600"),HPDamage,600);
    TestEqual(TEXT("dummy dies at hit9"),W.Dummy->Vital->GetSnapshot().HP,0);TestEqual(TEXT("one death"),W.Dummy->Vital->GetSnapshot().DeathCount,uint32(1));
    TestEqual(TEXT("replicated result history includes all9"),W.Network->Results.Num(),9);
    TestEqual(TEXT("last snapshot definition3"),W.Player->Combat->GetCombatSnapshot().DefinitionId,uint8(2));
    W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Buffer,"AnimeMMORPG.U03.A1.RuntimeBufferExpiryReplacementAndControl",U03A1Flags)
bool FU03A1Buffer::RunTest(const FString&)
{
    for(int32 Case=0;Case<3;++Case)
    {
        FU03A1World W;const double S=W.Now();W.Press(1,S);W.Press(2,S+(Case==0?.25:.30),10);
        if(Case==1)W.Press(3,S+.35,30);
        if(Case==2)W.Player->Combat->SetControlPlaying(false);
        W.Collision->DrainAt(S+1.);
        TestEqual(TEXT("expiry/control-clear prevent successor; replacement starts one"),W.Player->Combat->GetCombatSnapshot().ActionSequence,Case==1?uint64(2):uint64(1));
        if(Case==1)TestEqual(TEXT("replaced queued aim captured"),W.Player->Combat->GetCombatSnapshot().AimYawDegrees,30.);
        TestEqual(TEXT("owner acknowledgement clears expired pending"),W.Player->Combat->GetAdmission().PendingCommand,uint64(0));
        W.ForwardErrorMessages(this);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Resources,"AnimeMMORPG.U03.A1.ResourceSnapshotAndUnsupportedDispatcher",U03A1Flags)
bool FU03A1Resources::RunTest(const FString&)
{
    FU03A1World W;
    TestTrue(TEXT("native resource fixture spendsQ without skill action"),W.Collision->FixtureSpend(W.Player->Combat,AnimeMMORPG::U03::EAction::Q));
    TestEqual(TEXT("energy replicated snapshot80"),W.Player->Combat->GetCombatSnapshot().Energy,80.);
    TestFalse(TEXT("CD rejects fixture without charging"),W.Collision->FixtureSpend(W.Player->Combat,AnimeMMORPG::U03::EAction::Q));
    TestEqual(TEXT("no skill gameplay action from fixture"),W.Player->Combat->GetCombatSnapshot().ActionSequence,uint64(0));
    W.Player->Combat->SubmitCombatIntent(AnimeMMORPG::U03::ECommand::Q,1,0,0);W.Collision->DrainAt(W.Now());
    TestEqual(TEXT("Q physical dispatcher explicit unsupported"),W.Player->Combat->GetAdmission().Admission,uint8(AnimeMMORPG::U03::EAdmission::Unsupported));
    W.Player->Combat->SubmitAttackIntent(1,0,0);W.Collision->DrainAt(W.Now());
    TestEqual(TEXT("unsupported sequence cannot replay as attack"),W.Player->Combat->GetAdmission().Admission,uint8(AnimeMMORPG::U03::EAdmission::Stale));
    W.Collision->DrainAt(W.Now()+1.5);TestEqual(TEXT("resource integral is85 after1.5"),W.Player->Combat->GetCombatSnapshot().Energy,85.);
    W.ForwardErrorMessages(this);return true;
}
#endif
