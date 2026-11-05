#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U02/U02CombatComponent.h"
#include "U01/U01Character.h"
#include "AIController.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"

using namespace AnimeMMORPG::U02;
static constexpr auto U02BFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FU02CombatTestAccess
{
    static void Attack(UU02CombatComponent* C,uint64 Seq,double Yaw,double Now) { C->HandleAttack(Seq,Now,Yaw,Now); }
    static bool Advance(UU02CombatComponent* C,double Now) { return C->AdvanceAuthority(Now); }
    static bool Cancel(UU02CombatComponent* C,ECancel Reason,double Now) { return C->CancelAt(Reason,Now); }
};
namespace
{
struct FU02BWorld : FTestWorldWrapper
{
    AU01Character* C=nullptr;
    AAIController* Controller=nullptr;
    FAutomationTestBase& Test;
    explicit FU02BWorld(FAutomationTestBase& InTest):Test(InTest)
    {
        if(!CreateTestWorld(EWorldType::Game))return;
        GetTestWorld()->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        auto* Floor=GetTestWorld()->SpawnActor<AActor>();
        auto* Shape=NewObject<UBoxComponent>(Floor);Floor->SetRootComponent(Shape);
        Shape->SetBoxExtent(FVector(10000,10000,50));Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Shape->SetCollisionResponseToAllChannels(ECR_Block);Floor->SetActorLocation(FVector(0,0,-50));Shape->RegisterComponent();
        C=GetTestWorld()->SpawnActor<AU01Character>(FVector(0,0,110),FRotator::ZeroRotator);
        Controller=GetTestWorld()->SpawnActor<AAIController>();Controller->bSetControlRotationFromPawnOrientation=false;Controller->Possess(C);
        BeginPlayInTestWorld();
        for(int32 I=0;I<30;++I)TickTestWorld(1.f/60);
    }
    ~FU02BWorld(){ForwardErrorMessages(&Test);}
    double Now() const { return GetTestWorld()->GetTimeSeconds(); }
    void Step(float Dt=1.f/120,FVector Input=FVector::ZeroVector)
    { C->AddMovementInput(Input);TickTestWorld(Dt); }
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02AdapterDrain,"AnimeMMORPG.U02.B.AdapterDrainBeforeMutation",U02BFlags)
bool FU02AdapterDrain::RunTest(const FString&)
{
    FU02BWorld W(*this);if(!W.C)return false;
    auto* B=W.C->Combat.Get();const double Start=W.Now();
    FU02CombatTestAccess::Attack(B,1,0,Start);
    TestEqual(TEXT("Initial accepted"),B->AcceptedCount,uint64(1));
    int32 Delivered=0;
    int32 Barriers=0;
    B->BeforeActionMutation.BindLambda([&](double)
    {
        ++Barriers;
        TestEqual(TEXT("World barrier runs after old interval delivery, before action mutation"),Delivered,Barriers);
        TestEqual(TEXT("World barrier observes old action identity"),B->GetCombatSnapshot().ActionSequence,uint64(Barriers));
    });
    B->OnActiveInterval.AddLambda([&](const FActionId& Id,const FActiveSlice& Slice)
    {
        ++Delivered;
        TestEqual(TEXT("Old action still owns snapshot during drain"),B->GetCombatSnapshot().ActionSequence,Id.Sequence);
        if(Delivered==1)
        {
            TestEqual(TEXT("Whole old active start"),Slice.BeginSeconds,Start+.16);
            TestEqual(TEXT("Whole old active end"),Slice.EndSeconds,Start+.22);
            TestTrue(TEXT("Active deadline exclusive"),Slice.bEndExclusive);
            TestEqual(TEXT("Replacement not yet accepted"),B->AcceptedCount,uint64(1));
        }
        else
        {
            TestEqual(TEXT("Second old interval before lost-ground cancel"),Id.Sequence,uint64(2));
            TestTrue(TEXT("Cancel cutoff exclusive"),Slice.bEndExclusive);
            TestTrue(TEXT("Cancel not applied before drain"),B->GetCombatSnapshot().bLocked);
        }
    });
    FU02CombatTestAccess::Attack(B,2,30,Start+.5);
    TestEqual(TEXT("Replacement accepted after full drain"),B->AcceptedCount,uint64(2));
    TestTrue(TEXT("Forced invalidation accepted"),FU02CombatTestAccess::Cancel(B,ECancel::LostGround,Start+.68));
    TestEqual(TEXT("Both old intervals delivered"),Delivered,2);
    TestEqual(TEXT("Both mutations passed world barrier"),Barriers,2);
    TestFalse(TEXT("Cancel released combat lock"),W.C->GetU01Movement()->IsMotorLocked());
    B->OnActiveInterval.Clear();
    B->BeforeActionMutation.Unbind();
    AddInfo(TEXT("U02B_ASSERT adapter old interval delivered before replacement/cancel; full skipped active preserved; cancel endpoint excluded"));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02ReplayAuthority,"AnimeMMORPG.U02.B.AuthorityLockSavedMoveReplay",U02BFlags)
bool FU02ReplayAuthority::RunTest(const FString&)
{
    FU02BWorld W(*this);if(!W.C)return false;
    auto* M=W.C->GetU01Movement();auto* B=W.C->Combat.Get();
    auto* Data=static_cast<FNetworkPredictionData_Client_Character*>(M->GetPredictionData_Client());
    M->PressJump(M->GetMotorTimeSeconds());M->SetSprintRequested(true);
    auto Unlocked=Data->AllocateNewMove();Unlocked->Clear();Unlocked->SetMoveFor(W.C,.016f,FVector::ForwardVector,*Data);
    B->SubmitAttackIntent(1,W.Now(),0);
    auto Active=Data->AllocateNewMove();Active->Clear();Active->SetMoveFor(W.C,.016f,FVector::ZeroVector,*Data);
    TestFalse(TEXT("Cannot combine across action acceptance"),Unlocked->CanCombineWith(Active,W.C,.125f));
    const double Deadline=B->GetCombatSnapshot().StartSeconds+.4;
    Unlocked->PrepMoveFor(W.C);
    M->UpdateFromCompressedFlags(FSavedMove_Character::FLAG_Custom_0|FSavedMove_Character::FLAG_Custom_1);
    TestTrue(TEXT("Unlocked saved move/flags cannot clear combat authority"),(M->GetLockMask()&uint8(EU01MotorLock::Combat))!=0);
    TestEqual(TEXT("No speed under replay"),M->GetMaxSpeed(),0.f);
    TestFalse(TEXT("Replayed jump buffer discarded under combat"),M->HasBufferedJump(M->GetMotorTimeSeconds()));
    TestFalse(TEXT("Replayed sprint discarded"),M->IsSprinting());
    const FVector Before=W.C->GetActorLocation();
    for(int32 I=0;I<8;++I)W.Step(1.f/120,FVector::ForwardVector);
    TestTrue(TEXT("Replay cannot move XY"),FVector::Dist2D(Before,W.C->GetActorLocation())<.01);
    TestEqual(TEXT("Replay cannot change action deadline"),B->GetCombatSnapshot().StartSeconds+.4,Deadline);
    for(int32 I=0;I<60;++I)W.Step();
    TestFalse(TEXT("Authority finish releases combat"),M->IsMotorLocked());
    Active->PrepMoveFor(W.C);
    TestFalse(TEXT("Old combat move cannot resurrect finished authority action"),M->IsMotorLocked());
    M->SetMotorLock(EU01MotorLock::Defeated,true);Unlocked->PrepMoveFor(W.C);
    TestTrue(TEXT("Replay also preserves live Defeated"),(M->GetLockMask()&uint8(EU01MotorLock::Defeated))!=0);
    AddInfo(TEXT("U02B_ASSERT real FSavedMove_U01 replay preserves combat/Defeated, cannot restore stale combat, cannot extend action clock"));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02MotorRuntime,"AnimeMMORPG.U02.B.MotorGravityAndHeldIntent",U02BFlags)
bool FU02MotorRuntime::RunTest(const FString&)
{
    FU02BWorld W(*this);if(!W.C)return false;
    auto* M=W.C->GetU01Movement();auto* B=W.C->Combat.Get();
    for(int32 I=0;I<100;++I){M->SetSprintRequested(true);W.Step(1.f/120,FVector::ForwardVector);}
    TestTrue(TEXT("Real motor sprint before attack"),M->Velocity.Size2D()>699);
    B->SubmitAttackIntent(1,W.Now(),0);
    TestEqual(TEXT("Acceptance immediately stops XY"),M->Velocity.SizeSquared2D(),0.);
    const FVector AtAttack=W.C->GetActorLocation();
    for(int32 I=0;I<40;++I){M->SetSprintRequested(true);W.C->Jump();W.Step(1.f/120,FVector::ForwardVector);}
    TestTrue(TEXT("No horizontal displacement during attack"),FVector::Dist2D(AtAttack,W.C->GetActorLocation())<.01);
    TestEqual(TEXT("No buffered jump survives combat"),W.C->JumpCurrentCount,0);
    for(int32 I=0;I<70;++I)W.Step(1.f/120,FVector::ForwardVector);
    TestTrue(TEXT("Continuous held movement intent resumes without release"),W.C->GetActorLocation().X>AtAttack.X+100);
    B->SubmitAttackIntent(2,W.Now(),0);
    const double Z=W.C->GetActorLocation().Z;
    W.C->SetActorLocation(W.C->GetActorLocation()+FVector(0,0,500));M->SetMovementMode(MOVE_Falling);
    TestTrue(TEXT("Lost ground cancels action"),B->GetCombatSnapshot().Phase==uint8(EPhase::Cancelled));
    for(int32 I=0;I<20;++I)W.Step();
    TestTrue(TEXT("Gravity continues after losing ground"),M->Velocity.Z<0 && W.C->GetActorLocation().Z<Z+500);
    M->SetMotorLock(EU01MotorLock::Control,true);const double MenuZ=W.C->GetActorLocation().Z;
    for(int32 I=0;I<10;++I)W.Step();
    TestTrue(TEXT("Control/menu lock keeps gravity"),W.C->GetActorLocation().Z<MenuZ && M->Velocity.Size2D()<.01);
    AddInfo(TEXT("U02B_ASSERT actual Game physics: sprint stop, move/jump lock, continuous movement resumes, lost-ground cancellation and gravity"));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02AdapterRights,"AnimeMMORPG.U02.B.AdmissionCancelAndYaw",U02BFlags)
bool FU02AdapterRights::RunTest(const FString&)
{
    FU02BWorld W(*this);if(!W.C)return false;
    auto* B=W.C->Combat.Get();auto* M=W.C->GetU01Movement();const double Start=W.Now();
    FU02CombatTestAccess::Attack(B,1,20,Start);
    FU02CombatTestAccess::Attack(B,2,30,Start+.05);
    TestEqual(TEXT("Busy edge rejected without follow-up"),B->RejectedCount,uint64(1));
    TestTrue(TEXT("Startup dodge via real adapter"),FU02CombatTestAccess::Cancel(B,ECancel::Dodge,Start+.1));
    FU02CombatTestAccess::Attack(B,3,40,Start+.11);
    TestFalse(TEXT("Active guard rejected"),FU02CombatTestAccess::Cancel(B,ECancel::Guard,Start+.27));
    TestFalse(TEXT("Menu cannot cancel accepted action"),FU02CombatTestAccess::Cancel(B,ECancel::Menu,Start+.28));
    FU02CombatTestAccess::Advance(B,Start+.6);
    TestEqual(TEXT("Busy did not buffer another action"),B->AcceptedCount,uint64(2));
    TestFalse(TEXT("End returns motor"),M->IsMotorLocked());
    FU02BWorld Aim(*this);auto* AB=Aim.C->Combat.Get();auto* AM=Aim.C->GetU01Movement();
    AB->SubmitAttackIntent(1,Aim.Now(),10);Aim.Controller->SetControlRotation(FRotator(0,75,0));
    for(int32 I=0;I<12;++I)Aim.Step();
    TestTrue(TEXT("Startup follows newest aim"),FMath::Abs(FRotator::NormalizeAxis(Aim.C->GetActorRotation().Yaw-75))<.01);
    for(int32 I=0;I<10;++I)Aim.Step();
    Aim.Controller->SetControlRotation(FRotator(0,-110,0));
    for(int32 I=0;I<20;++I)Aim.Step();
    TestTrue(TEXT("Active/recovery yaw immune to new aim"),FMath::Abs(FRotator::NormalizeAxis(Aim.C->GetActorRotation().Yaw-75))<.01);
    TestEqual(TEXT("Aim/controller remains free"),Aim.Controller->GetControlRotation().Yaw,-110.);
    AM->SetMotorLock(EU01MotorLock::Interacting,true);
    TestFalse(TEXT("Cannot enter Interacting inside action"),(AM->GetLockMask()&uint8(EU01MotorLock::Interacting))!=0);
    return true;
}
#endif
