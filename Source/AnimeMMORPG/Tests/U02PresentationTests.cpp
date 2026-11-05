#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U02/U02Presentation.h"
#include "U01/U01AnimInstance.h"
#include "U01/U01Character.h"
#include "Tests/AutomationCommon.h"
#include "AIController.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02PresentationClock,"AnimeMMORPG.U02.C.SnapshotClock",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU02PresentationClock::RunTest(const FString&)
{
    FU02RepCombatSnapshot S;S.PawnId=FGuid(1,0,0,1);S.LifeGeneration=1;S.ActionSequence=1;S.StartSeconds=10;S.Phase=2;S.bLocked=true;
    for(double Elapsed:{0.,.159,.16,.219,.22,.399})
    {
        auto P=AnimeMMORPG::U02::SamplePresentation(S,10+Elapsed);
        TestTrue(TEXT("Valid current snapshot plays"),P.bPlay);
        TestTrue(TEXT("Late seek authority timeline"),FMath::Abs(P.PositionSeconds-Elapsed)<1.e-12);
    }
    TestFalse(TEXT("Exact finish no replay"),AnimeMMORPG::U02::SamplePresentation(S,10.4).bPlay);
    S.Phase=uint8(AnimeMMORPG::U02::EPhase::Cancelled);S.bLocked=false;
    TestFalse(TEXT("Cancellation stops presentation"),AnimeMMORPG::U02::SamplePresentation(S,10.18).bPlay);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02MontageAssets,"AnimeMMORPG.U02.C.MontageAssets",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU02MontageAssets::RunTest(const FString&)
{
    auto* M=LoadObject<UAnimMontage>(nullptr,TEXT("/Game/AnimeMMORPG/U02/Animation/AM_U02_Attack1"));
    auto* A=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AnimeMMORPG/U02/Animation/A_U02_Attack1"));
    if(!TestNotNull(TEXT("Authored montage"),M)||!TestNotNull(TEXT("Authored sequence"),A))return false;
    TestTrue(TEXT("Both 0.40s"),FMath::Abs(M->GetPlayLength()-.4)<1.e-6&&FMath::Abs(A->GetPlayLength()-.4)<1.e-6);
    TestEqual(TEXT("Three sections"),M->GetNumSections(),3);
    TestTrue(TEXT("Same technical skeleton"),M->GetSkeleton()==A->GetSkeleton());
    TestFalse(TEXT("Authored root motion disabled"),A->bEnableRootMotion);
    TestEqual(TEXT("No gameplay notify dependencies"),A->Notifies.Num()+M->Notifies.Num(),0);
    TestTrue(TEXT("Zero root displacement"),A->ExtractRootMotionFromRange(0,.4,FAnimExtractContext()).GetTranslation().IsNearlyZero(.001));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02MontageRuntime,"AnimeMMORPG.U02.C.RuntimeIdentityAndReturn",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU02MontageRuntime::RunTest(const FString&)
{
    FTestWorldWrapper W;if(!W.CreateTestWorld(EWorldType::Game))return false;
    W.GetTestWorld()->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
    auto* Class=LoadClass<AU01Character>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Character.BP_U01Character_C"));
    auto* C=W.GetTestWorld()->SpawnActor<AU01Character>(Class);auto* Controller=W.GetTestWorld()->SpawnActor<AAIController>();Controller->Possess(C);
    W.BeginPlayInTestWorld();auto* Anim=Cast<UU01AnimInstance>(C->GetMesh()->GetAnimInstance());
    if(!TestNotNull(TEXT("U01 actual anim instance"),Anim)||!TestNotNull(TEXT("Montage serialized dependency"),Anim->AttackMontage.Get()))return false;
    FU02RepCombatSnapshot S;S.PawnId=C->NetworkPawnId;S.LifeGeneration=1;S.ActionSequence=2;S.StartSeconds=5;S.Phase=2;S.bLocked=true;
    const FVector Location=C->GetActorLocation();Anim->PresentCombat(S,5.18);
    TestTrue(TEXT("Late client snapshot presents current action"),Anim->bAttackPresented&&Anim->PresentedAction==2);
    TestTrue(TEXT("Seeks active time"),FMath::Abs(Anim->Montage_GetPosition(Anim->AttackMontage)-.18)<.001);
    auto Old=S;Old.ActionSequence=1;Old.bLocked=false;Old.Phase=5;Anim->PresentCombat(Old,5.19);
    TestTrue(TEXT("Stale cancellation cannot stop newer action"),Anim->bAttackPresented&&Anim->PresentedAction==2);
    S.bLocked=false;S.Phase=5;Anim->PresentCombat(S,5.2);TestFalse(TEXT("Matching cancellation stops"),Anim->bAttackPresented);
    S.LifeGeneration=2;S.ActionSequence=0;S.Phase=0;Anim->PresentCombat(S,5.21);
    TestTrue(TEXT("Reset life applied with no action"),Anim->PresentedLife==2&&!Anim->bAttackPresented);
    S.ActionSequence=1;S.Phase=1;S.bLocked=true;S.StartSeconds=6;Anim->PresentCombat(S,6.1);Anim->PresentCombat(S,6.4);
    TestFalse(TEXT("Finish returns locomotion, no replay"),Anim->bAttackPresented);
    TestTrue(TEXT("Presentation never displaces capsule"),C->GetActorLocation().Equals(Location));
    W.ForwardErrorMessages(this);return true;
}
#endif
