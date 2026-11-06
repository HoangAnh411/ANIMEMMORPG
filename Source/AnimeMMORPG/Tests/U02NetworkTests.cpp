#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U02/U02NetworkState.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02LabDummy.h"
#include "U02/U02VitalComponent.h"
#include "U01/U01Character.h"
#include "Components/BoxComponent.h"
#include "AIController.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include <limits>
struct FU02FTestAccess
{
    static void Attack(UU02CombatComponent* C,uint64 Seq,FGuid Id,uint64 Life,double Yaw=0){C->ServerAttack_Implementation(Seq,0,Yaw,Id,Life);}
};
namespace {
constexpr auto U02FFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FW:FTestWorldWrapper
{
 AU01Character* C=nullptr;
 FW(){CreateTestWorld(EWorldType::Game);auto* W=GetTestWorld();W->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();auto* F=W->SpawnActor<AActor>();auto* S=NewObject<UBoxComponent>(F);F->SetRootComponent(S);S->SetBoxExtent(FVector(10000,10000,50));S->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);S->SetCollisionResponseToAllChannels(ECR_Block);F->SetActorLocation(FVector(0,0,-50));S->RegisterComponent();C=W->SpawnActor<AU01Character>(FVector(0,0,110),FRotator::ZeroRotator);W->SpawnActor<AAIController>()->Possess(C);BeginPlayInTestWorld();for(int I=0;I<30;++I)TickTestWorld(1.f/60);}
 void Finish(){for(int I=0;I<30;++I)TickTestWorld(1.f/60);}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02FLife,"AnimeMMORPG.U02.F.CommandLifeAndDuplicateAdmission",U02FFlags)
bool FU02FLife::RunTest(const FString&)
{
 FW W;auto* C=W.C->Combat.Get();const auto Id=W.C->NetworkPawnId;FU02FTestAccess::Attack(C,1,Id,1);TestEqual(TEXT("Own life accepted"),C->AcceptedCount,uint64(1));W.Finish();FU02FTestAccess::Attack(C,1,Id,1);TestEqual(TEXT("Duplicate rejected after finish"),C->AcceptedCount,uint64(1));C->ResetLabCombat();FU02FTestAccess::Attack(C,2,Id,1);FU02FTestAccess::Attack(C,2,FGuid::NewGuid(),2);TestEqual(TEXT("Old life and wrong subject rejected"),C->AcceptedCount,uint64(1));FU02FTestAccess::Attack(C,2,Id,2,std::numeric_limits<double>::quiet_NaN());TestEqual(TEXT("Nonfinite rejected"),C->AcceptedCount,uint64(1));FU02FTestAccess::Attack(C,3,Id,2);TestEqual(TEXT("Valid new command after rejection accepted"),C->AcceptedCount,uint64(2));W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02FResult,"AnimeMMORPG.U02.F.AuthoritativeResultHistoryAndReplicationSchema",U02FFlags)
bool FU02FResult::RunTest(const FString&)
{
 FW W;auto* S=W.GetTestWorld()->SpawnActor<AU02NetworkState>();auto* D=W.GetTestWorld()->SpawnActor<AU02LabDummy>(FVector(500,0,0),FRotator::ZeroRotator);TestTrue(TEXT("Dummy replicates with server identity"),D->GetIsReplicated()&&D->NetworkPawnId.IsValid());TestTrue(TEXT("Vital replicated component"),D->Vital->GetIsReplicated());UU02CollisionWorld::FConfirmedDamage R;R.Hit.Id.Action={{W.C->NetworkPawnId,1},1};R.Hit.Id.Target={D->NetworkPawnId,1};R.Result.Damage=60;R.Result.AfterHP=540;
 for(int I=0;I<70;++I){R.Hit.Id.Action.Sequence=I+1;S->Confirm(R);}TestEqual(TEXT("Bounded result history"),S->Results.Num(),64);TestEqual(TEXT("Stable server serial"),S->Results.Last().Serial,uint64(70));TestEqual(TEXT("Event publication never applies damage"),D->Vital->GetSnapshot().HP,600);
 const auto* F=UU02CombatComponent::StaticClass()->FindFunctionByName(TEXT("ServerAttack"));TestNotNull(TEXT("RPC exists"),F);if(F){TestTrue(TEXT("Server reliable RPC"),F->HasAllFunctionFlags(FUNC_NetServer|FUNC_NetReliable));TestNull(TEXT("Client cannot declare damage"),F->FindPropertyByName(TEXT("Damage")));TestNull(TEXT("Client cannot declare HP"),F->FindPropertyByName(TEXT("HP")));TestNotNull(TEXT("Expected life on wire"),F->FindPropertyByName(TEXT("Life")));}W.ForwardErrorMessages(this);return true;
}
#endif
