#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U03/U03ActionModel.h"
using namespace AnimeMMORPG;
using namespace AnimeMMORPG::U03;
namespace {
constexpr auto SkillFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
U02::FLifeId SkillLife(){return {FGuid(701,0,0,1),1};}
FCombatIntent SkillIntent(uint64 S,double T,ECommand C){return {S,SkillLife(),C,T,0};}
EAdmission SkillPress(FTimelineModel& M,uint64 S,double T,ECommand C,TArray<FActiveInterval>& Out,FAdmissionContext Context={})
{return M.SubmitBatchUnopposed({SkillIntent(S,T,C)},Context,Out)[0].Result;}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1Feint,"AnimeMMORPG.U03.C1.FeintEdgesResourcesAndLife",SkillFlags)
bool FC1Feint::RunTest(const FString&)
{
    for(double At:{.299999,.30,.300001})
    {
        FTimelineModel M(SkillLife());TArray<FActiveInterval> Out;
        TestEqual(TEXT("cast"),SkillPress(M,1,0,ECommand::Q,Out),EAdmission::Accepted);
        const auto R=SkillPress(M,2,At,ECommand::Q,Out);
        TestEqual(TEXT("startup only, priority over cast cooldown"),R,At<.30?EAdmission::Accepted:EAdmission::Busy);
        TestEqual(TEXT("no refund/spend"),M.Resources().Energy(),80.);
        TestEqual(TEXT("original CD"),M.Resources().ReadyAt(EAction::Q),4.);
        M.AdvanceUnopposed(1.,Out);
        TestEqual(TEXT("no remaining active after Feint"),Out.IsEmpty(),At<.30);
    }
    FTimelineModel M(SkillLife());TArray<FActiveInterval> Out;
    SkillPress(M,1,0,ECommand::Q,Out);SkillPress(M,2,.10,ECommand::Q,Out);
    FAdmissionContext C;C.bDefenseEnabled=C.bDodgeEnabled=true;
    uint64 Seq=2;
    for(auto Command:{ECommand::Attack,ECommand::Guard,ECommand::Dodge,ECommand::Q,ECommand::E,ECommand::Jump})
        TestEqual(TEXT("Feint lock rejects without buffering"),SkillPress(M,++Seq,.299999,Command,Out,C),EAdmission::Locked);
    TestFalse(TEXT("no attack buffer"),M.GetPending().IsSet());TestFalse(TEXT("no dodge buffer"),M.GetPendingDodge().IsSet());
    TestEqual(TEXT("lock exact endpoint"),SkillPress(M,++Seq,.10+.20,ECommand::Attack,Out,C),EAdmission::Accepted);
    M.AdvanceUnopposed(1.5,Out);TestEqual(TEXT("Feint did not reset regen delay"),M.Resources().Energy(),85.);
    auto Life=SkillLife();++Life.Generation;TestTrue(TEXT("new life"),M.ResetLife(Life,2));
    TestEqual(TEXT("life clears Feint identity"),M.Feint().Sequence,uint64(0));TestEqual(TEXT("life clears resources"),M.Resources().Energy(),100.);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1Replacement,"AnimeMMORPG.U03.C1.RecoveryAndReplacementPermissions",SkillFlags)
bool FC1Replacement::RunTest(const FString&)
{
    for(auto Skill:{ECommand::Q,ECommand::E})for(int Combo=0;Combo<3;++Combo)for(int Phase=0;Phase<3;++Phase)
    {
        FTimelineModel M(SkillLife());TArray<FActiveInterval> Out;uint64 Seq=0;double Start=0;
        SkillPress(M,++Seq,0,ECommand::Attack,Out);
        for(int I=0;I<Combo;++I){const double Duration=Definition(EAction(I)).Duration;SkillPress(M,++Seq,Start+Duration-.10,ECommand::Attack,Out);Start+=Duration;M.AdvanceUnopposed(Start,Out);}
        const auto& D=Definition(EAction(Combo));const double T=Start+(Phase==0?D.ActiveStart/2:Phase==1?D.ActiveStart:D.ActiveEnd);
        TestEqual(TEXT("skill only replaces normal recovery"),SkillPress(M,++Seq,T,Skill,Out),Phase==2?EAdmission::Accepted:EAdmission::Busy);
        TestEqual(TEXT("rejected skill preserves energy"),M.Resources().Energy(),Phase==2?(Skill==ECommand::Q?80.:75.):100.);
        if(Phase==2){TestFalse(TEXT("clear pending"),M.GetPending().IsSet());TestEqual(TEXT("skills cannot replace each other"),SkillPress(M,++Seq,T+.01,Skill==ECommand::Q?ECommand::E:ECommand::Q,Out),EAdmission::Busy);}
    }
    for(auto Skill:{ECommand::Q,ECommand::E})for(auto Replacement:{ECommand::Guard,ECommand::Dodge})for(int Phase=0;Phase<3;++Phase)
    {
        FTimelineModel M(SkillLife());TArray<FActiveInterval> Out;FAdmissionContext C;C.bDefenseEnabled=C.bDodgeEnabled=true;
        SkillPress(M,1,0,Skill,Out,C);const auto& D=Definition(Skill==ECommand::Q?EAction::Q:EAction::E);
        const double T=Phase==0?D.ActiveStart-.000001:Phase==1?D.ActiveStart:D.ActiveEnd;
        TestEqual(TEXT("guard/dodge only replace startup"),SkillPress(M,2,T,Replacement,Out,C),Phase==0?EAdmission::Accepted:Replacement==ECommand::Guard?EAdmission::Locked:EAdmission::Busy);
        TestEqual(TEXT("cancellation never refunds"),M.Resources().Energy(),Skill==ECommand::Q?80.:75.);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1InterruptEdges,"AnimeMMORPG.U03.C1.InterruptEdgesAndCapturedEffects",SkillFlags)
bool FC1InterruptEdges::RunTest(const FString&)
{
    for(auto Id:{EAction::Attack1,EAction::Q,EAction::E})for(double Offset:{-.000001,0.,.000001})
    {
        FTimelineModel M(SkillLife());TArray<FActiveInterval> Out;const auto Command=Id==EAction::Q?ECommand::Q:Id==EAction::E?ECommand::E:ECommand::Attack;
        SkillPress(M,1,0,Command,Out);const double At=Definition(Id).ActiveStart+Offset;
        TestEqual(TEXT("pure Interrupt is half-open startup"),M.CancelUnopposed(ECutoff::Interrupt,At,true,Out),Offset<0);
        TestFalse(TEXT("Interrupt adds no hard CC"),M.Defense().Locked(At));
    }
    for(auto Command:{ECommand::Q,ECommand::E})
    {
        FTimelineModel M(SkillLife());TArray<FActiveInterval> Out;SkillPress(M,1,0,Command,Out);M.AdvanceUnopposed(1,Out);
        TestFalse(TEXT("skill produced active slices"),Out.IsEmpty());
        for(const auto& I:Out){TestEqual(TEXT("captured Interrupt"),I.bInterrupt,Command==ECommand::E);TestTrue(TEXT("captured block/parry"),I.bBlockable&&I.bParryable);TestEqual(TEXT("captured version"),I.DefinitionVersion,uint32(1));}
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC1Cooldown,"AnimeMMORPG.U03.C1.CooldownRegenAndResourceRejection",SkillFlags)
bool FC1Cooldown::RunTest(const FString&)
{
    for(auto Id:{EAction::Q,EAction::E})for(double Offset:{-.000001,0.,.000001})
    {
        FResourceModel R;const auto& D=Definition(Id);TestTrue(TEXT("spend"),R.Spend(D,0));R.Advance(1);TestEqual(TEXT("regen exact delay"),R.Energy(),100.-D.Cost);
        R.Advance(1.25);TestEqual(TEXT("partial eligible interval"),R.Energy(),102.5-D.Cost);R.Advance(D.Cooldown+Offset);
        const double Before=R.Energy();TestEqual(TEXT("cooldown boundary"),R.Spend(D,D.Cooldown+Offset),Offset>=0);
        TestEqual(TEXT("failure spends nothing"),R.Energy(),Before-(Offset>=0?D.Cost:0));
    }
    FResourceModel R;FActionDefinition D=Definition(EAction::Q);D.Cooldown=0;
    for(int I=0;I<5;++I)TestTrue(TEXT("exact energy accepted"),R.Spend(D,0));
    TestEqual(TEXT("zero energy"),R.Energy(),0.);TestFalse(TEXT("insufficient energy"),R.Spend(D,0));R.Advance(20);TestEqual(TEXT("regen cap"),R.Energy(),100.);
    return true;
}
#endif
