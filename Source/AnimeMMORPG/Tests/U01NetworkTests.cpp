#include "Misc/AutomationTest.h"
#include "U01/U01Character.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Tests/AutomationCommon.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "AIController.h"
#include "U01/U01AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01NetworkMoves,"AnimeMMORPG.U01.F.SavedMoveReplay",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU01NetworkMoves::RunTest(const FString&)
{
    FTestWorldWrapper World;TestTrue(TEXT("Game world"),World.CreateTestWorld(EWorldType::Game));
    World.GetTestWorld()->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
    auto* C=World.GetTestWorld()->SpawnActor<AU01Character>();auto* PC=World.GetTestWorld()->SpawnActor<AAIController>();PC->Possess(C);
    World.BeginPlayInTestWorld();auto* M=C->GetU01Movement();
    auto* Data=static_cast<FNetworkPredictionData_Client_Character*>(M->GetPredictionData_Client());
    const int32 BeforeCorrection=M->CorrectionCount;Data->bUpdatePosition=true;
    M->ClientUpdatePositionAfterServerUpdate();
    TestEqual(TEXT("Adjustment counted even without pending moves to replay"),M->CorrectionCount,BeforeCorrection+1);
    M->PressJump(M->GetMotorTimeSeconds());M->SetSprintRequested(true);
    auto Move=Data->AllocateNewMove();Move->Clear();Move->SetMoveFor(C,.016f,FVector(1,0,0),*Data);
    TestTrue(TEXT("Sprint compressed"),(Move->GetCompressedFlags()&FSavedMove_Character::FLAG_Custom_0)!=0);
    TestTrue(TEXT("Held jump compressed"),(Move->GetCompressedFlags()&FSavedMove_Character::FLAG_Custom_1)!=0);
    TestFalse(TEXT("Engine jump is not alternate permission"),(Move->GetCompressedFlags()&FSavedMove_Character::FLAG_JumpPressed)!=0);
    M->SetControlLocked(true);auto Locked=Data->AllocateNewMove();Locked->Clear();Locked->SetMoveFor(C,.016f,FVector::ZeroVector,*Data);
    TestFalse(TEXT("No combination across intent edge"),Move->CanCombineWith(Locked,C,.125f));
    TestTrue(TEXT("Control lock compressed"),(Locked->GetCompressedFlags()&FSavedMove_Character::FLAG_Custom_2)!=0);
    Move->PrepMoveFor(C);TestFalse(TEXT("Replay restores lock snapshot"),M->IsMotorLocked());
    TestTrue(TEXT("Replay restores buffered edge"),M->HasBufferedJump(M->GetMotorTimeSeconds()));
    TestFalse(TEXT("Replay does not extend half-open deadline"),M->HasBufferedJump(M->GetMotorTimeSeconds()+.1));
    M->ResetFixtureState();M->UpdateFromCompressedFlags(FSavedMove_Character::FLAG_Custom_1);
    TestTrue(TEXT("Authority reconstructs new jump edge on its clock"),M->HasBufferedJump(M->GetMotorTimeSeconds()));
    M->UpdateFromCompressedFlags(FSavedMove_Character::FLAG_Custom_1|FSavedMove_Character::FLAG_Custom_2);
    TestTrue(TEXT("Server control lock applies"),M->IsMotorLocked());TestFalse(TEXT("Lock flushes network buffer"),M->HasBufferedJump(M->GetMotorTimeSeconds()));
    M->UpdateFromCompressedFlags(0);M->SetMotorLock(EU01MotorLock::Defeated,true);M->UpdateFromCompressedFlags(FSavedMove_Character::FLAG_Custom_0);
    TestTrue(TEXT("Client cannot clear authority Defeated bit"),M->IsMotorLocked());
    M->SetMotorLock(EU01MotorLock::Defeated,false);M->MaxWalkSpeed=2000;TestEqual(TEXT("Authority ignores arbitrary max walk speed"),M->GetMaxSpeed(),500.f);
    World.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01ProxyAnimation,"AnimeMMORPG.U01.F.ProxyAnimation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU01ProxyAnimation::RunTest(const FString&)
{
    FTestWorldWrapper World;if(!World.CreateTestWorld(EWorldType::Game))return false;
    World.GetTestWorld()->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
    auto* Class=LoadClass<AU01Character>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Character.BP_U01Character_C"));
    auto* C=World.GetTestWorld()->SpawnActor<AU01Character>(Class);if(!C){AddError(TEXT("Real U01 Blueprint spawn failed"));return false;}
    World.BeginPlayInTestWorld();auto* Anim=Cast<UU01AnimInstance>(C->GetMesh()->GetAnimInstance());if(!Anim){AddError(TEXT("Real U01 AnimBP missing"));return false;}
    C->SetRole(ROLE_SimulatedProxy);auto* Motor=C->GetU01Movement();Motor->SetMovementMode(MOVE_Falling);
    Motor->Velocity=FVector(700,0,-400);C->GetReplicatedMovement_Mutable().LinearVelocity=FVector(700,0,300);
    const FVector Before=C->GetActorLocation();Anim->NativeUpdateAnimation(.033f);
    TestEqual(TEXT("Proxy uses authoritative ascent, not extrapolated descent"),Anim->PoseIndex,2);
    TestEqual(TEXT("Proxy presentation speed from packet"),Anim->GroundSpeed,700.f);
    C->GetReplicatedMovement_Mutable().LinearVelocity.Z=-100;Anim->NativeUpdateAnimation(.033f);
    TestEqual(TEXT("Proxy authoritative fall"),Anim->PoseIndex,3);
    Motor->SetMovementMode(MOVE_Walking);Motor->Velocity=FVector::ZeroVector;C->GetReplicatedMovement_Mutable().LinearVelocity=FVector::ZeroVector;
    Anim->NativeUpdateAnimation(.033f);TestEqual(TEXT("Proxy landing"),Anim->PoseIndex,4);
    Anim->NativeUpdateAnimation(.3f);TestEqual(TEXT("Proxy idle, not stuck falling"),Anim->PoseIndex,0);
    TestTrue(TEXT("Animation never moves capsule"),C->GetActorLocation().Equals(Before));
    C->SetRole(ROLE_Authority);Motor->Velocity=FVector(500,0,0);Anim->NativeUpdateAnimation(.033f);
    TestEqual(TEXT("Authority still reads actual velocity"),Anim->GroundSpeed,500.f);
    World.ForwardErrorMessages(this);return true;
}
#endif
