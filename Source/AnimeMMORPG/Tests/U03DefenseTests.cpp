#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U03/U03ActionModel.h"
#include "U02/U02VitalModel.h"
using namespace AnimeMMORPG::U03;
namespace { constexpr auto B2Flags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter; }

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2Parry,"AnimeMMORPG.U03.B2.ParryHalfOpenEdges",B2Flags)
bool FB2Parry::RunTest(const FString&)
{
    for(double T:{0.,.12-1e-9,.12,.12+1e-9})
    {
        FDefenseState D;D.PressGuard(0,0,true);D.Advance(T);
        TestTrue(TEXT("half-open .12"),D.Defend(T,FVector::ForwardVector,FVector::BackwardVector,true,true)==(T<.12?EDefense::Parry:EDefense::Block));
        TestTrue(TEXT("only one parry"),D.Defend(T,FVector::ForwardVector,FVector::BackwardVector,true,true)==EDefense::Block);
    }
    for(double T:{.60-1e-9,.60,.60+1e-9})
    {
        FDefenseState D;D.PressGuard(0,0,true);D.Advance(T);TestFalse(TEXT("held never repeats"),D.PressGuard(T,0,true));
        D.ReleaseGuard();D.PressGuard(T,0,true);TestEqual(TEXT("repress .60"),D.bParryOpen,T>=.60);
        D.Advance(T+1.);TestFalse(TEXT("no cooldown buffer"),D.bParryOpen);
    }
    FDefenseState D;TestFalse(TEXT("invalid edge rejected"),D.PressGuard(0,0,false));
    TestFalse(TEXT("held rejected edge cannot resume"),D.PressGuard(.1,0,true));D.ReleaseGuard();TestTrue(TEXT("release rearms"),D.PressGuard(.1,0,true));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2Angles,"AnimeMMORPG.U03.B2.AngleAndIndependentHitFlags",B2Flags)
bool FB2Angles::RunTest(const FString&)
{
    for(double Angle:{-180.,-60.00001,-60.,0.,60.,60.00001,180.})
    {
        FDefenseState D;D.PressGuard(0,0,true);D.Advance(.12);
        TestTrue(TEXT("inclusive sixty degrees"),D.Defend(.12,FRotator(0,Angle,0).Vector(),FVector::ForwardVector,true,true)==(FMath::Abs(Angle)<=60?EDefense::Block:EDefense::Hit));
    }
    FDefenseState D;D.PressGuard(0,0,true);
    TestTrue(TEXT("unparryable still blockable"),D.Defend(0,FVector::ForwardVector,FVector::ForwardVector,true,false)==EDefense::Block);
    TestTrue(TEXT("bypass cannot parry"),D.Defend(0,FVector::ForwardVector,FVector::ForwardVector,false,true)==EDefense::Hit);
    TestTrue(TEXT("coincident opposite attack"),D.Defend(0,FVector::ZeroVector,FVector::BackwardVector,true,true)==EDefense::Parry);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2Posture,"AnimeMMORPG.U03.B2.PostureBreakAndEligibleRegen",B2Flags)
bool FB2Posture::RunTest(const FString&)
{
    FDefenseState D;D.PressGuard(0,0,true);D.Advance(.12);
    for(int I=0;I<4;++I)TestTrue(TEXT("including breaking hit blocks"),D.Defend(.12,FVector::ForwardVector,FVector::BackwardVector,true,false)==EDefense::Block);
    TestEqual(TEXT("25 to zero"),D.Posture,0.);TestTrue(TEXT("break"),D.Hard==EHardCC::GuardBreak);
    const double End=.12+.8;D.Advance(End-1e-9);TestTrue(TEXT("before .8"),D.Locked(End-1e-9));D.Advance(End);TestFalse(TEXT("at .8"),D.Locked(End));TestEqual(TEXT("refill"),D.Posture,100.);
    TestFalse(TEXT("no automatic rearm after break"),D.PressGuard(End,0,true));D.ReleaseGuard();D.PressGuard(End,0,true);
    D.ImmuneEnd=End+2;D.Posture=25;D.Defend(End,FVector::ForwardVector,FVector::BackwardVector,true,false);TestFalse(TEXT("immune break drops guard"),D.bGuard);TestFalse(TEXT("immune break no lock"),D.Locked(End));TestEqual(TEXT("immune refill"),D.Posture,100.);
    FDefenseState R;R.PressGuard(0,0,true);R.Posture=25;R.LastHit=0;R.Advance(10);TestEqual(TEXT("held no regen"),R.Posture,25.);R.ReleaseGuard();R.Advance(10.5);TestEqual(TEXT("no held backfill"),R.Posture,37.5);
    FDefenseState E;E.Posture=25;E.LastHit=0;E.Advance(2.-1e-9);TestEqual(TEXT("before2"),E.Posture,25.);E.Advance(2.);TestEqual(TEXT("at2"),E.Posture,25.);E.Advance(3.);TestEqual(TEXT("eligible second"),E.Posture,50.);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2CC,"AnimeMMORPG.U03.B2.ControlReplacementBudgetAndFreeReset",B2Flags)
bool FB2CC::RunTest(const FString&)
{
    FDefenseState D;D.ApplyHard(EHardCC::Stun,1,0);D.Advance(.25);
    TestFalse(TEXT("shorter rejects"),D.ApplyHard(EHardCC::Knockdown,.5,.25));TestFalse(TEXT("equal remaining rejects"),D.ApplyHard(EHardCC::Grab,.75,.25));TestTrue(TEXT("longer replaces"),D.ApplyHard(EHardCC::Launch,3,.25));
    D.Advance(2.-1e-9);TestTrue(TEXT("before budget"),D.Locked(D.Last));D.Advance(2.);TestFalse(TEXT("budget2 exits"),D.Locked(2));TestEqual(TEXT("immunity2"),D.ImmuneEnd,4.);
    TestFalse(TEXT("immune before end"),D.ApplyHard(EHardCC::Grab,1,4.-1e-9));D.Advance(4.);TestTrue(TEXT("immune exact end"),D.ApplyHard(EHardCC::Grab,1,4.));
    for(double Gap:{.50-1e-9,.50,.50+1e-9})
    {
        FDefenseState S;S.ApplyHard(EHardCC::Stun,.5,0);S.Advance(.5+Gap);TestTrue(TEXT("free time not accumulated"),S.LockedBudget<=.5);
        TestTrue(TEXT("reset at .50"),Gap<.50?S.LockedBudget==.5:S.LockedBudget==0.);
    }
    FDefenseState Long,Short;Long.ApplyHard(EHardCC::Stun,5,0);Short=Long;Long.Advance(10);for(int I=1;I<=1000;++I)Short.Advance(I*.01);
    TestEqual(TEXT("long short hard"),uint8(Long.Hard),uint8(Short.Hard));TestEqual(TEXT("long short immunity"),Long.ImmuneEnd,Short.ImmuneEnd);TestEqual(TEXT("long short budget"),Long.LockedBudget,Short.LockedBudget);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2Escape,"AnimeMMORPG.U03.B2.EscapeSlowAndCooldown",B2Flags)
bool FB2Escape::RunTest(const FString&)
{
    FDefenseState D;TestFalse(TEXT("invalid X"),D.Escape(0));TestEqual(TEXT("invalid no CD"),D.XReadyAt,0.);
    D.Slows={{.2,5},{.6,1}};TestEqual(TEXT("strongest"),D.Slow(0),.6);D.Advance(1);TestEqual(TEXT("weaker survives"),D.Slow(1),.2);
    D.ApplyHard(EHardCC::Launch,1,1);TestTrue(TEXT("pending launch"),D.bPendingLaunch);TestTrue(TEXT("X valid"),D.Escape(1));TestFalse(TEXT("launch cleared"),D.bPendingLaunch);TestEqual(TEXT("slow cleared"),D.Slow(1),0.);TestEqual(TEXT("budget cleared"),D.LockedBudget,0.);
    D.Slows.Add({.4,3});TestEqual(TEXT("X does not prevent new slow"),D.Slow(1),.4);
    for(double T:{2.-1e-9,2.,2.+1e-9}){FDefenseState C=D;C.Advance(T);TestEqual(TEXT("one second immunity"),C.ApplyHard(EHardCC::Grab,1,T),T>=2.);}
    for(double T:{31.-1e-9,31.,31.+1e-9}){FDefenseState C=D;C.Advance(T);C.ApplyHard(EHardCC::Stun,1,T);TestEqual(TEXT("30 second CD"),C.Escape(T),T>=31.);}
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FB2Admission,"AnimeMMORPG.U03.B2.TimelineGuardReplacementAndAirborneX",B2Flags)
bool FB2Admission::RunTest(const FString&)
{
    using namespace AnimeMMORPG;const U02::FLifeId Life{FGuid(42,0,0,1),1};FAdmissionContext C;C.bDefenseEnabled=true;TArray<FActiveInterval> Out;
    for(double T:{.16-1e-9,.16,.22,.3})
    {
        FTimelineModel M(Life);M.SubmitBatchUnopposed({{1,Life,ECommand::Attack,0,0}},C,Out);
        const auto R=M.SubmitBatchUnopposed({{2,Life,ECommand::Guard,T,0}},C,Out);
        TestEqual(TEXT("startup only"),R[0].Result==EAdmission::Accepted,T<.16);TestEqual(TEXT("rejection preserves action"),M.Current()!=nullptr,T>=.16);
    }
    FTimelineModel M(Life);struct FEmpty:ITimelineResolver{TOptional<double> NextEvent(const FTimelineModel&,double)override{return{};}void ResolveInterval(const FActiveInterval&)override{}void ResolveEvent(FTimelineModel&,double)override{}} Empty;
    M.ArriveAtBarrier(0,Empty);M.HardAtBarrier(EHardCC::Launch,1);M.GroundedAtBarrier(false);M.FinishBarrier(Empty);C.bGrounded=false;
    auto R=M.SubmitBatchUnopposed({{1,Life,ECommand::Escape,0,0}},C,Out);TestTrue(TEXT("airborne X"),R[0].Result==EAdmission::Accepted);
    TestFalse(TEXT("pending cleared"),M.Defense().bPendingLaunch);TestEqual(TEXT("no energy cost"),M.Resources().Energy(),100.);
    U02::FVitalModel V;const auto Damage=V.Apply(61,1,.01,0,.30);TestEqual(TEXT("crit once block before round"),Damage.Damage,U02::FVitalModel::Calculate(61,1,0,true,.30));
    return true;
}
#endif
