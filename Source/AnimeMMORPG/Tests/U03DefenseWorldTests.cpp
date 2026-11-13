#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Algo/Reverse.h"
#include "U01/U01Character.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02VitalComponent.h"
#include "Components/BoxComponent.h"
#include "AIController.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "Kismet/GameplayStatics.h"
using namespace AnimeMMORPG;
using namespace AnimeMMORPG::U03;
struct FU03B2Access
{
    static void Reverse(UU02CollisionWorld* W){Algo::Reverse(W->Sources);}
    static void Hit(UU02CollisionWorld* W,AU01Character* Source,bool Blockable,bool Parryable,EHardCC Hard=EHardCC::None)
    {UU02CollisionWorld::FDefenseFixtureHit H;H.bBlockable=Blockable;H.bParryable=Parryable;H.Hard=Hard;H.Duration=1.25;W->DefenseFixtureHits.Add({{Source->NetworkPawnId,1},1},H);}
    static void Interrupt(UU02CollisionWorld* W,AU01Character* Source){W->FixtureInterruptActions.Add({{Source->NetworkPawnId,1},1});}
    static FTimelineModel* Model(AU01Character* C){return C->Combat->Model.Get();}
    static void HP(AU01Character* C,int32 HP){C->Vital->State.HP=HP;C->Vital->Publish(C->GetWorld()->GetTimeSeconds());}
    static void Aim(AU01Character* C,double Yaw,uint64 Guard)
    {C->Combat->ServerGuardAim_Implementation(Yaw,C->NetworkPawnId,C->Combat->GetCombatSnapshot().LifeGeneration,Guard);}
    static void Intent(AU01Character* C,ECommand Kind,uint64 Seq,uint64 Life)
    {C->Combat->ServerCombat_Implementation(uint8(Kind),Seq,0,0,C->NetworkPawnId,Life,FVector2D::ZeroVector);}
};
namespace
{
constexpr auto B2WorldFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FB2World:FTestWorldWrapper
{
    AU01Character *Source=nullptr,*Target=nullptr,*Third=nullptr;UU02CollisionWorld* Collision=nullptr;double Start=0;
    FB2World(bool Multi=false)
    {
        CreateTestWorld(EWorldType::Game);auto* W=GetTestWorld();W->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        auto* Floor=W->SpawnActor<AActor>();auto* B=NewObject<UBoxComponent>(Floor);Floor->SetRootComponent(B);B->SetBoxExtent(FVector(10000,10000,50));B->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);B->SetCollisionResponseToAllChannels(ECR_Block);B->RegisterComponent();Floor->SetActorLocation(FVector(0,0,-50));
        Source=Spawn(FVector(0,0,98),101);Target=Spawn(FVector(150,0,98),102);if(Multi)Third=Spawn(FVector(0,90,98),103);BeginPlayInTestWorld();for(int I=0;I<30;++I)TickTestWorld(1.f/60);
        Collision=W->GetSubsystem<UU02CollisionWorld>();Collision->FixtureCritRoll=.5;Collision->bCharacterFixtureTargets=true;Start=W->GetTimeSeconds();
    }
    AU01Character* Spawn(FVector P,uint32 Id)
    {
        FTransform X(P);auto* C=GetTestWorld()->SpawnActorDeferred<AU01Character>(AU01Character::StaticClass(),X,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);C->NetworkPawnId=FGuid(Id,0,0,1);UGameplayStatics::FinishSpawningActor(C,X);
        auto* PC=GetTestWorld()->SpawnActor<AAIController>();PC->bSetControlRotationFromPawnOrientation=false;PC->Possess(C);return C;
    }
    void Command(AU01Character* C,ECommand Kind,uint64 Seq,double T,double Yaw)
    {C->Combat->SubmitCombatIntent(Kind,Seq,0,Yaw);Collision->DrainAt(Start+T);}
    void End(double T=.3){Collision->DrainAt(Start+T);}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2WorldDefense,"AnimeMMORPG.U03.B2.WorldParryBlockDedupCritShield",B2WorldFlags)
bool FB2WorldDefense::RunTest(const FString&)
{
    for(bool Parry:{true,false})
    {
        FB2World W;W.Collision->FixtureCritRoll=0;W.Target->Vital->AddFixtureShield(1,100,W.Start+5,W.Start);
        W.Command(W.Source,ECommand::Attack,1,0,0);W.Command(W.Target,ECommand::Guard,1,Parry?.10:0,180);W.End(1);
        TestEqual(TEXT("one dedup contact"),W.Collision->DamageResults.Num(),1);if(W.Collision->DamageResults.IsEmpty())return false;
        const auto& R=W.Collision->DamageResults[0];TestEqual(TEXT("defense"),R.Result.Defense,uint8(Parry?EDefense::Parry:EDefense::Block));
        TestEqual(TEXT("parry no crit roll, block once"),W.Collision->CritRolls,uint64(Parry?0:1));TestEqual(TEXT("posture"),W.Target->Combat->GetCombatSnapshot().Posture,Parry?100.:75.);
        TestEqual(TEXT("shield before HP"),W.Target->Vital->GetSnapshot().HP,1000);TestEqual(TEXT("final rounding after crit/block"),R.Result.Damage,Parry?0:27);
        TestEqual(TEXT("shield only spends rounded damage"),W.Target->Vital->GetSnapshot().Shield,Parry?100:73);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2WorldEffects,"AnimeMMORPG.U03.B2.WorldFlagsInterruptAndLethalEffects",B2WorldFlags)
bool FB2WorldEffects::RunTest(const FString&)
{
    for(int Mode=0;Mode<4;++Mode)
    {
        FB2World W;FU03B2Access::Hit(W.Collision,W.Source,Mode==0,false,EHardCC::Grab);FU03B2Access::Interrupt(W.Collision,W.Source);
        if(Mode==2)W.Target->Vital->AddFixtureShield(1,100,W.Start+5,W.Start);
        if(Mode==3)FU03B2Access::HP(W.Target,1);
        W.Command(W.Source,ECommand::Attack,1,0,0);W.Command(W.Target,ECommand::Guard,1,.10,180);W.End();
        const auto& R=W.Collision->DamageResults.Last();
        TestEqual(TEXT("independent unparryable/bypass"),R.Result.Defense,uint8(Mode==0?EDefense::Block:EDefense::Hit));
        TestEqual(TEXT("blocked effects, shield not immune, lethal no effects"),W.Target->Combat->GetCombatSnapshot().HardCC,uint8(Mode==1||Mode==2?EHardCC::Grab:EHardCC::None));
        TestEqual(TEXT("death before effects"),W.Target->Vital->GetSnapshot().bDead,Mode==3);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2WorldCausality,"AnimeMMORPG.U03.B2.WorldLateInputAndStableSimultaneousHits",B2WorldFlags)
bool FB2WorldCausality::RunTest(const FString&)
{
    for(bool Reverse:{false,true})for(bool Short:{false,true})
    {
        FB2World W(true);auto* Other=W.Third;
        W.Source->Combat->SubmitAttackIntent(1,0,0);Other->Combat->SubmitAttackIntent(1,0,(W.Target->GetActorLocation()-Other->GetActorLocation()).Rotation().Yaw);W.Collision->DrainAt(W.Start);
        TestTrue(TEXT("both attackers admitted before comparison"),W.Source->Combat->GetCombatSnapshot().bLocked&&Other->Combat->GetCombatSnapshot().bLocked);
        if(Reverse)FU03B2Access::Reverse(W.Collision);
        W.Command(W.Target,ECommand::Guard,1,.10,180);
        if(Short)for(int I=11;I<30;++I)W.End(I*.01);W.End();
        int Parry=0,Block=0;for(const auto& R:W.Collision->DamageResults)if(R.Hit.Id.Target.Pawn==W.Target->NetworkPawnId){Parry+=R.Result.Defense==uint8(EDefense::Parry);Block+=R.Result.Defense==uint8(EDefense::Block);}
        TestEqual(TEXT("simultaneous first parry only"),Parry,1);TestEqual(TEXT("second block"),Block,1);TestEqual(TEXT("stable target HP"),W.Target->Vital->GetSnapshot().HP,982);
    }
    FB2World W;W.Command(W.Source,ECommand::Attack,1,0,0);W.End(.17);const int Before=W.Target->Vital->GetSnapshot().HP;
    W.Command(W.Target,ECommand::Guard,1,.18,180);W.Command(W.Target,ECommand::GuardRelease,2,.19,0);W.End();
    TestEqual(TEXT("late guard/release cannot rewrite HP"),W.Target->Vital->GetSnapshot().HP,Before);TestEqual(TEXT("past hit unguarded"),Before,940);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2WorldAngle,"AnimeMMORPG.U03.B2.WorldGuardAnglesAndHitTimeAim",B2WorldFlags)
bool FB2WorldAngle::RunTest(const FString&)
{
    for(double Angle:{-180.,-60.00001,-60.,0.,60.,60.00001,180.})
    {
        FB2World W;W.Command(W.Target,ECommand::Guard,1,0,180+Angle);W.Command(W.Source,ECommand::Attack,1,0,0);W.End();
        TestEqual(TEXT("world inclusive yaw boundary"),W.Collision->DamageResults.Last().Result.Defense,uint8(FMath::Abs(Angle)<=60?EDefense::Block:EDefense::Hit));
    }
    FB2World W;W.Source->SetActorLocation(W.Target->GetActorLocation(),false,nullptr,ETeleportType::TeleportPhysics);W.Collision->RebaseResetSubject(W.Source);
    W.Command(W.Target,ECommand::Guard,1,0,180);W.Command(W.Source,ECommand::Attack,1,0,0);W.End();
    TestEqual(TEXT("coincident actual world uses reverse attack"),W.Collision->DamageResults.Last().Result.Defense,uint8(EDefense::Block));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2WorldIdentity,"AnimeMMORPG.U03.B2.WorldAimCausalityOwnershipLifeAndMotor",B2WorldFlags)
bool FB2WorldIdentity::RunTest(const FString&)
{
    for(bool Early:{false,true})
    {
        FB2World W;W.Command(W.Target,ECommand::Guard,1,0,0);W.Command(W.Source,ECommand::Attack,1,0,0);
        W.End(Early?.15:.17);FU03B2Access::Aim(W.Target,180,W.Target->Combat->GetCombatSnapshot().GuardSequence);W.End(Early?.15:.18);W.End();
        TestEqual(TEXT("aim only affects future hits"),W.Target->Vital->GetSnapshot().HP,Early?982:940);
        TestEqual(TEXT("guard speed200"),W.Target->GetU01Movement()->GetMaxSpeed(),200.f);
        W.Target->GetU01Movement()->SetSprintRequested(true);TestFalse(TEXT("guard cannot sprint"),W.Target->GetU01Movement()->IsSprinting());
        W.Target->GetU01Movement()->PressJump(W.Start+.3);TestFalse(TEXT("guard cannot buffer jump"),W.Target->GetU01Movement()->HasBufferedJump(W.Start+.3));
        const auto Old=W.Target->Combat->GetCombatSnapshot();W.Command(W.Target,ECommand::GuardRelease,2,.31,0);W.Command(W.Target,ECommand::Guard,3,.60,180);
        FU03B2Access::Aim(W.Target,0,Old.GuardSequence);W.End(.61);TestEqual(TEXT("old guard aim identity rejected"),W.Target->Combat->GetCombatSnapshot().GuardYaw,180.);
        FU03B2Access::Intent(W.Target,ECommand::Guard,3,Old.LifeGeneration);W.End(.62);TestEqual(TEXT("duplicate cannot reopen window"),W.Target->Combat->GetCombatSnapshot().ParryStart,W.Start+.60);
        W.Target->Combat->ResetLabCombat();FU03B2Access::Intent(W.Target,ECommand::GuardRelease,100,Old.LifeGeneration);W.End(.63);
        const auto New=W.Target->Combat->GetCombatSnapshot();TestEqual(TEXT("new life posture"),New.Posture,100.);TestEqual(TEXT("new life X"),New.XReadyAt,0.);TestFalse(TEXT("new life no replay guard"),New.bGuard);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1WorldInterrupt,"AnimeMMORPG.U03.C1.WorldSkillInterruptShieldDefenseDeath",B2WorldFlags)
bool FC1WorldInterrupt::RunTest(const FString&)
{
    for(auto Victim:{ECommand::Attack,ECommand::Q,ECommand::E})for(int Mode=0;Mode<6;++Mode)for(bool Reverse:{false,true})
    {
        FB2World W;
        if(Mode==1)W.Target->Vital->AddFixtureShield(1,500,W.Start+5,W.Start);
        if(Mode==4)FU03B2Access::HP(W.Target,1);
        const bool IsQ=Mode==5;const double Hit=IsQ?.30:.25;
        W.Command(W.Source,IsQ?ECommand::Q:ECommand::E,1,0,0);
        if(Mode==2||Mode==3)W.Command(W.Target,ECommand::Guard,1,Mode==2?0:.20,180);
        else W.Command(W.Target,Victim,1,.20,180);
        if(Reverse)FU03B2Access::Reverse(W.Collision);
        W.End(1.5);
        const auto* R=W.Collision->DamageResults.FindByPredicate([&](const auto& D){return D.Hit.Id.Action.Source.Pawn==W.Source->NetworkPawnId&&D.Hit.Id.Target.Pawn==W.Target->NetworkPawnId;});
        TestNotNull(TEXT("real geometry contact"),R);if(!R)return false;
        TestEqual(TEXT("one skill hit on target"),W.Collision->DamageResults.FilterByPredicate([&](const auto& D){return D.Hit.Id.Action.Source.Pawn==W.Source->NetworkPawnId&&D.Hit.Id.Target.Pawn==W.Target->NetworkPawnId;}).Num(),1);
        TestEqual(TEXT("captured raw"),R->Hit.RawDamage,IsQ?100:80);
        TestEqual(TEXT("E effect survives shield, blocked/parried/lethal/Q suppress"),R->bInterrupted,Mode<2);
        TestEqual(TEXT("identity feedback"),W.Target->Combat->GetCombatSnapshot().InterruptSequence,Mode<2?uint64(1):uint64(0));
        TestEqual(TEXT("Interrupt is not stun"),W.Target->Combat->GetCombatSnapshot().HardCC,uint8(0));
        if(Mode==1)TestEqual(TEXT("full shield no HP loss"),W.Target->Vital->GetSnapshot().HP,1000);
        if(Mode==2||Mode==3)TestEqual(TEXT("actual defense"),R->Result.Defense,uint8(Mode==2?EDefense::Block:EDefense::Parry));
        TestEqual(TEXT("source cooldown"),W.Source->Combat->GetCombatSnapshot().EReadyAt,IsQ?0.:W.Start+6);
        AddInfo(FString::Printf(TEXT("C1_WORLD victim=%u mode=%d reverse=%d hit=%.17g expected=%.17g interrupted=%d action=%llu hp=%d"),uint8(Victim),Mode,Reverse,R->Hit.TimestampSeconds,W.Start+Hit,R->bInterrupted,R->InterruptedAction,W.Target->Vital->GetSnapshot().HP));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1WorldFeint,"AnimeMMORPG.U03.C1.WorldFeintCutoffAndMotor",B2WorldFlags)
bool FC1WorldFeint::RunTest(const FString&)
{
    for(bool Feint:{false,true})
    {
        FB2World W;W.Command(W.Source,ECommand::Q,1,0,0);
        if(Feint)W.Command(W.Source,ECommand::Q,2,.10,0);
        TestEqual(TEXT("Feint releases horizontal skill lock"),W.Source->Combat->GetCombatSnapshot().bLocked,!Feint);
        W.Source->GetU01Movement()->SetSprintRequested(true);
        W.Source->GetU01Movement()->PressJump(W.Start+.10);
        W.End(1.5);
        TestEqual(TEXT("cutoff prevents all unfired skill contacts"),W.Collision->DamageResults.Num(),Feint?0:1);
        TestEqual(TEXT("no resource refund, original regen delay"),W.Source->Combat->GetCombatSnapshot().Energy,85.);
        TestEqual(TEXT("original Q cooldown"),W.Source->Combat->GetCombatSnapshot().QReadyAt,W.Start+4);
        TestEqual(TEXT("Feint feedback identity"),W.Source->Combat->GetCombatSnapshot().FeintSequence,Feint?uint64(1):uint64(0));
        TestEqual(TEXT("Feint action identity"),W.Source->Combat->GetCombatSnapshot().FeintAction,Feint?uint64(1):uint64(0));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1Successor,"AnimeMMORPG.U03.C1.WorldIncomingEInSuccessorLongShort",B2WorldFlags)
bool FC1Successor::RunTest(const FString&)
{
    for(bool Reverse:{false,true})for(double Step:{.01,1.})
    {
        FB2World W;W.Command(W.Source,ECommand::Attack,1,0,0);W.Command(W.Target,ECommand::E,1,.29,180);W.Command(W.Source,ECommand::Attack,2,.30,0);
        if(Reverse)FU03B2Access::Reverse(W.Collision);
        for(double T=.30+Step;T<1.3;T+=Step)W.End(T);W.End(1.3);
        TestEqual(TEXT("successor started"),W.Source->Combat->GetCombatSnapshot().ActionSequence,uint64(2));
        // Incoming E starts .29, hits .54 inside successor [.40,.56) startup.
        TestEqual(TEXT("real E cut successor startup"),W.Source->Combat->GetCombatSnapshot().InterruptedAction,uint64(2));
        TestEqual(TEXT("old confirmed attack retained"),W.Target->Vital->GetSnapshot().HP,940);
        TestEqual(TEXT("no successor hit after cutoff"),W.Collision->DamageResults.FilterByPredicate([&](const auto& D){return D.Hit.Id.Action.Source.Pawn==W.Source->NetworkPawnId;}).Num(),1);
        TestEqual(TEXT("E raw80"),W.Source->Vital->GetSnapshot().HP,920);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1MultiTarget,"AnimeMMORPG.U03.C1.WorldEPerTargetDedup",B2WorldFlags)
bool FC1MultiTarget::RunTest(const FString&)
{
    FB2World W(true);W.Command(W.Source,ECommand::E,1,0,0);W.Command(W.Target,ECommand::Q,1,.20,180);W.Command(W.Third,ECommand::Q,1,.20,180);W.End(1.5);
    const auto Hits=W.Collision->DamageResults.FilterByPredicate([&](const auto& D){return D.Hit.Id.Action.Source.Pawn==W.Source->NetworkPawnId;});
    TestEqual(TEXT("one contact on each distinct target"),Hits.Num(),2);
    for(const auto& D:Hits){TestTrue(TEXT("each target interrupted independently"),D.bInterrupted);TestEqual(TEXT("each target80"),D.Result.Damage,80);}
    return true;
}
#endif
