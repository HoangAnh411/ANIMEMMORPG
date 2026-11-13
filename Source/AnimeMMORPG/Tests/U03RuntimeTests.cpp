#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Algo/Reverse.h"
#include "Tests/AutomationCommon.h"
#include "U01/U01Character.h"
#include "U01/U01Settings.h"
#include "U01/U01AnimInstance.h"
#include "U02/U02Presentation.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Resources,"AnimeMMORPG.U03.A1.ResourceSnapshotAndCooldownDispatcher",U03A1Flags)
bool FU03A1Resources::RunTest(const FString&)
{
    FU03A1World W;
    TestTrue(TEXT("native resource fixture spendsQ without skill action"),W.Collision->FixtureSpend(W.Player->Combat,AnimeMMORPG::U03::EAction::Q));
    TestEqual(TEXT("energy replicated snapshot80"),W.Player->Combat->GetCombatSnapshot().Energy,80.);
    TestFalse(TEXT("CD rejects fixture without charging"),W.Collision->FixtureSpend(W.Player->Combat,AnimeMMORPG::U03::EAction::Q));
    TestEqual(TEXT("no skill gameplay action from fixture"),W.Player->Combat->GetCombatSnapshot().ActionSequence,uint64(0));
    W.Player->Combat->SubmitCombatIntent(AnimeMMORPG::U03::ECommand::Q,1,0,0);W.Collision->DrainAt(W.Now());
    TestEqual(TEXT("Q dispatcher honors existing cooldown"),W.Player->Combat->GetAdmission().Admission,uint8(AnimeMMORPG::U03::EAdmission::Cooldown));
    W.Player->Combat->SubmitAttackIntent(1,0,0);W.Collision->DrainAt(W.Now());
    TestEqual(TEXT("unsupported sequence cannot replay as attack"),W.Player->Combat->GetAdmission().Admission,uint8(AnimeMMORPG::U03::EAdmission::Stale));
    W.Collision->DrainAt(W.Now()+1.5);TestEqual(TEXT("resource integral is85 after1.5"),W.Player->Combat->GetCombatSnapshot().Energy,85.);
    W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Incoming,"AnimeMMORPG.U03.A1.GeometryIncomingInterruptAndDeathDuringSuccessor",U03A1Flags)
bool FU03A1Incoming::RunTest(const FString&)
{
    for(bool Death:{false,true})for(bool Reverse:{false,true})
    {
        FU03A1World W;const double S=W.Now();W.Collision->bCharacterFixtureTargets=true;
        auto* Enemy=W.SpawnPlayer(FVector(-150,0,98),2);
        if(Death)FU03RuntimeAccess::HP(W.Player->Vital,60);
        W.Press(1,S);
        Enemy->Combat->SubmitAttackIntent(1,S,0);W.Collision->DrainAt(S+.29);
        if(!Death)FU03RuntimeAccess::Interrupt(W.Collision,Enemy->Combat);
        W.Press(2,S+.30);
        if(Reverse)FU03RuntimeAccess::Reverse(W.Collision);
        W.Collision->DrainAt(S+1.);
        TestEqual(TEXT("real incoming hit during successor startup"),W.Player->Vital->GetSnapshot().HP,Death?0:940);
        TestEqual(TEXT("successor actually started before incoming collision"),W.Player->Combat->GetCombatSnapshot().ActionSequence,uint64(2));
        TestEqual(TEXT("incoming effect cutoff cancelled successor"),W.Player->Combat->GetCombatSnapshot().Phase,uint8(AnimeMMORPG::U02::EPhase::Cancelled));
        TestEqual(TEXT("old confirmed60 retained, no successor damage"),W.Dummy->Vital->GetSnapshot().HP,540);
        const auto& Events=W.Collision->DamageResults;
        TestFalse(TEXT("no geometry damage from cancelled successor"),Events.ContainsByPredicate([&](const auto& R){return R.Hit.Id.Action.Source.Pawn==W.Player->NetworkPawnId&&R.Hit.Id.Action.Sequence==2;}));
        AddInfo(FString::Printf(TEXT("U03A1_WORLD_CUTOFF death=%d reverse=%d incoming=%.17g action=%llu phase=%u hp=%d dummyHP=%d"),Death,Reverse,S+.45,W.Player->Combat->GetCombatSnapshot().ActionSequence,W.Player->Combat->GetCombatSnapshot().Phase,W.Player->Vital->GetSnapshot().HP,W.Dummy->Vital->GetSnapshot().HP));
        W.ForwardErrorMessages(this);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Group,"AnimeMMORPG.U03.A1.WorldTimestampGroupBeforeSuccessor",U03A1Flags)
bool FU03A1Group::RunTest(const FString&)
{
    for(bool Reverse:{false,true})
    {
        FU03A1World W;const double S=W.Now();W.Collision->bCharacterFixtureTargets=true;
        auto* A=W.SpawnPlayer(FVector(-150,-25,98),2);auto* B=W.SpawnPlayer(FVector(-140,25,98),3);
        FU03RuntimeAccess::HP(W.Player->Vital,100);W.Press(1,S);
        A->Combat->SubmitAttackIntent(1,S,0);B->Combat->SubmitAttackIntent(1,S,0);W.Collision->DrainAt(S+.24);
        W.Press(2,S+.30);if(Reverse)FU03RuntimeAccess::Reverse(W.Collision);
        W.Collision->DrainAt(S+.40);
        TestEqual(TEXT("second same-time source lethal"),W.Player->Vital->GetSnapshot().HP,0);
        TestEqual(TEXT("pending successor never starts between same-time hits"),W.Player->Combat->GetCombatSnapshot().ActionSequence,uint64(1));
        TestEqual(TEXT("one death from group"),W.Player->Vital->GetSnapshot().DeathCount,uint32(1));
        TArray<uint32> Order;for(const auto& R:W.Collision->DamageResults)if(R.Hit.Id.Target.Pawn==W.Player->NetworkPawnId)Order.Add(R.Hit.Id.Action.Source.Pawn.A);
        TestTrue(TEXT("global stable source order2 then3"),Order==TArray<uint32>{2,3});
        W.ForwardErrorMessages(this);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Life,"AnimeMMORPG.U03.A1.LostGroundLandingResetAndStaleLife",U03A1Flags)
bool FU03A1Life::RunTest(const FString&)
{
    FU03A1World W;const double S=W.Now();W.Press(1,S);W.Press(2,S+.30);
    TestTrue(TEXT("world floor-loss exactly action-end accepted"),W.Collision->ApplyLifecycle(W.Player->Combat,S+.40,AnimeMMORPG::U03::ECutoff::LostGround,false));
    TestEqual(TEXT("floor-loss clears pending before successor"),W.Player->Combat->GetCombatSnapshot().ActionSequence,uint64(1));
    W.Press(3,S+.41);TestEqual(TEXT("model floor-loss latch blocks stale grounded motor context"),W.Player->Combat->GetAdmission().Admission,uint8(AnimeMMORPG::U03::EAdmission::Locked));
    TestTrue(TEXT("authority landing permits fresh command"),W.Collision->ApplyLifecycle(W.Player->Combat,S+.42,AnimeMMORPG::U03::ECutoff::LostGround,true));
    W.Press(4,S+.42);TestEqual(TEXT("landing starts first definition"),W.Player->Combat->GetCombatSnapshot().DefinitionId,uint8(0));
    const auto Before=W.Player->Combat->GetCombatSnapshot();TestTrue(TEXT("real combat reset succeeds"),W.Player->Combat->ResetLabCombat());
    FU03RuntimeAccess::Command(W.Player->Combat,5,Before.LifeGeneration,Before.PawnId);W.Collision->DrainAt(S+.42);
    TestEqual(TEXT("old life rejected at authority dispatcher"),W.Player->Combat->GetAdmission().Admission,uint8(AnimeMMORPG::U03::EAdmission::Invalid));
    TestEqual(TEXT("new life action not resurrected"),W.Player->Combat->GetCombatSnapshot().ActionSequence,uint64(0));
    W.ForwardErrorMessages(this);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Presentation,"AnimeMMORPG.U03.A1.AuthoredThreeClipsAndDefinitionClock",U03A1Flags)
bool FU03A1Presentation::RunTest(const FString&)
{
    auto* Class=LoadClass<UU01AnimInstance>(nullptr,TEXT("/Game/AnimeMMORPG/U03/Animation/ABP_U03.ABP_U03_C"));
    TestNotNull(TEXT("A1 class loads"),Class);if(!Class)return false;
    auto* Default=CastChecked<UU01AnimInstance>(Class->GetDefaultObject());
    const UAnimMontage* Montages[]={Default->AttackMontage,Default->Attack2Montage,Default->Attack3Montage};
    for(uint8 I=0;I<3;++I)
    {
        const auto& D=AnimeMMORPG::U03::Definition(static_cast<AnimeMMORPG::U03::EAction>(I));
        TestNotNull(TEXT("each definition has authored montage"),Montages[I]);if(!Montages[I])return false;
        TestTrue(TEXT("duration follows immutable action definition"),FMath::Abs(Montages[I]->GetPlayLength()-D.Duration)<1.e-6);
        if(I)TestTrue(TEXT("clips distinguish each action"),Montages[I]!=Montages[I-1]);
        FU02RepCombatSnapshot S;S.ActionSequence=1;S.bLocked=true;S.Phase=1;S.DefinitionId=I;S.Duration=D.Duration;
        TestTrue(TEXT("presentation runs inside each duration"),AnimeMMORPG::U02::SamplePresentation(S,D.Duration-.001).bPlay);
        TestFalse(TEXT("presentation exact own end excluded"),AnimeMMORPG::U02::SamplePresentation(S,D.Duration).bPlay);
    }
    TestTrue(TEXT("animation ignores root motion"),Default->RootMotionMode==ERootMotionMode::IgnoreRootMotion);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03A1Bindings,"AnimeMMORPG.U03.A1.BindingFoundationAndV1Migration",U03A1Flags)
bool FU03A1Bindings::RunTest(const FString&)
{
    namespace C=AnimeMMORPG::U01;
    C::FPreferences Defaults,Out;
    TestEqual(TEXT("Attack uses physical LMB by default"),Defaults.Keys[C::Attack],EKeys::LeftMouseButton);
    TestEqual(TEXT("Dodge binding is Shift but runtime remains unsupported"),Defaults.Keys[C::Dodge],EKeys::LeftShift);
    TSharedPtr<FJsonObject> Json;FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(C::EncodePreferences(Defaults)),Json);
    Json->SetNumberField(TEXT("version"),1);auto B=Json->GetObjectField(TEXT("bindings"));
    for(const TCHAR* Name:{TEXT("Attack"),TEXT("Guard"),TEXT("Dodge"),TEXT("EscapeCC"),TEXT("Q"),TEXT("E"),TEXT("Target")})B->RemoveField(Name);
    B->SetStringField(TEXT("Jump"),TEXT("H"));FString V1;FJsonSerializer::Serialize(Json.ToSharedRef(),TJsonWriterFactory<>::Create(&V1));
    TestTrue(TEXT("v1 loads without treating missing combat bindings as damage"),C::DecodePreferences(V1,Out).IsEmpty());
    TestEqual(TEXT("valid legacy jump retained"),Out.Keys[C::Jump],EKeys::H);TestEqual(TEXT("new Attack gets default"),Out.Keys[C::Attack],EKeys::LeftMouseButton);
    FString Why;TestTrue(TEXT("mouse buttons now legal bindings"),C::AllowedBinding(EKeys::RightMouseButton,Why));
    TestTrue(TEXT("unused keyboard Attack rebind valid"),C::BindingError(Defaults,C::Attack,EKeys::H).IsEmpty());
    TestFalse(TEXT("shared conflict namespace rejects duplicate movement binding"),C::BindingError(Defaults,C::Attack,EKeys::W).IsEmpty());
    TestFalse(TEXT("reserved future skill R remains reserved"),C::AllowedBinding(EKeys::R,Why));
    TestFalse(TEXT("wheel not a single button"),C::AllowedBinding(EKeys::MouseScrollUp,Why));
    TestEqual(TEXT("Shift family canonical"),C::CanonicalKey(EKeys::RightShift),EKeys::LeftShift);
    return true;
}

#endif
