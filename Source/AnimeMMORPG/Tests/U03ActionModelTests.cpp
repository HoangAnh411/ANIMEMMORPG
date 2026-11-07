#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Algo/Reverse.h"
#include "U03/U03ActionModel.h"
using namespace AnimeMMORPG;
using namespace AnimeMMORPG::U03;
namespace {
U02::FLifeId U03A0Life(uint32 Id=1){return {FGuid(Id,0,0,1),1};}
FCombatIntent U03A0Intent(uint64 Seq,double T,ECommand C=ECommand::Attack,double Yaw=0){return {Seq,U03A0Life(),C,T,Yaw};}
constexpr auto U03A0Flags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Definitions,"AnimeMMORPG.U03.A0.DefinitionIdentity",U03A0Flags)
bool FU03Definitions::RunTest(const FString&)
{
    const int32 Raw[]={60,70,90,100,80,100};
    const double Starts[]={.16,.18,.26,.30,.25,.60},Ends[]={.22,.25,.36,.40,.35,.75},Durations[]={.40,.45,.60,.80,.75,1.50};
    for(int32 I=0;I<6;++I){const auto& D=Definition(static_cast<EAction>(I));TestEqual(TEXT("raw"),D.RawDamage,Raw[I]);TestEqual(TEXT("start"),D.ActiveStart,Starts[I]);TestEqual(TEXT("end"),D.ActiveEnd,Ends[I]);TestEqual(TEXT("duration"),D.Duration,Durations[I]);TestEqual(TEXT("box"),D.HalfExtentsCm,FVector(100,60,90));}
    FActionInstance Old(EAction::Attack1,{U03A0Life(),1},0,0),New(EAction::Q,{U03A0Life(),2},1,0);
    TestEqual(TEXT("old immutable raw"),Old.GetDefinition().RawDamage,60);TestEqual(TEXT("new raw"),New.GetDefinition().RawDamage,100);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Timeline,"AnimeMMORPG.U03.A0.TimelineAndBuffer",U03A0Flags)
bool FU03Timeline::RunTest(const FString&)
{
    for(const double Step:{1./30,1./60,1./120,2.})
    {
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
        M.SubmitBatch({U03A0Intent(1,0)}, {},Out);M.SubmitBatch({U03A0Intent(2,.30)}, {},Out);
        for(double T=.30+Step;T<1.;T+=Step) M.Advance(T,Out);
        M.Advance(1.,Out);double Total=0;bool Second=false;
        for(const auto& S:Out){Total+=S.End-S.Begin;Second|=S.DefinitionId==EAction::Attack2;TestTrue(TEXT("nonempty clipped"),S.Begin<S.End);}
        TestTrue(TEXT("whole active both actions"),FMath::Abs(Total-.13)<1e-12);TestTrue(TEXT("buffer starts second within long update"),Second);
    }
    FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
    M.SubmitBatch({U03A0Intent(1,0)}, {},Out);
    auto R=M.SubmitBatch({U03A0Intent(2,.25)}, {},Out);TestTrue(TEXT("queue"),R[0].Result==EAdmission::Queued);
    M.Advance(.40,Out);TestNull(TEXT("expiry exactly end not consumed"),M.Current());
    M.SubmitBatch({U03A0Intent(3,.40)}, {},Out);TestTrue(TEXT("new edge exactly end uses combo grace"),M.Current()->GetDefinition().Id==EAction::Attack2);
    FTimelineModel N(U03A0Life());Out.Reset();N.SubmitBatch({U03A0Intent(1,0)}, {},Out);
    N.SubmitBatch({U03A0Intent(2,.26,ECommand::Attack,10)}, {},Out);
    R=N.SubmitBatch({U03A0Intent(3,.35,ECommand::Attack,30)}, {},Out);TestTrue(TEXT("replacement"),R[0].Result==EAdmission::Replaced);
    N.Advance(.40,Out);TestEqual(TEXT("known queued aim"),N.Current()->Yaw,30.);
    N.SubmitBatch({U03A0Intent(4,.75)}, {},Out);N.Advance(.40+.45,Out);TestTrue(TEXT("third"),N.Current()->GetDefinition().Id==EAction::Attack3);
    N.SubmitBatch({U03A0Intent(5,1.35)}, {},Out);N.Advance(.40+.45+.60,Out);TestTrue(TEXT("third buffers first"),N.Current()->GetDefinition().Id==EAction::Attack1);
    FTimelineModel Combo(U03A0Life()); Out.Reset();
    Combo.SubmitBatch({U03A0Intent(1,0)}, {},Out);
    Combo.SubmitBatch({U03A0Intent(2,.30)}, {},Out);
    Combo.SubmitBatch({U03A0Intent(3,.75)}, {},Out);
    Combo.Advance(.40+.45+.60,Out);
    int32 Sum=0; TArray<uint64> Seen;
    for(const auto& Slice:Out) if(!Seen.Contains(Slice.Identity.Sequence)){Seen.Add(Slice.Identity.Sequence);Sum+=Slice.RawDamage;}
    TestEqual(TEXT("three definitions total220 raw"),Sum,220);
    TestNull(TEXT("chain ends at sum durations"),Combo.Current());
    FTimelineModel Grace(U03A0Life()); Out.Reset();Grace.SubmitBatch({U03A0Intent(1,0)}, {},Out);
    Grace.SubmitBatch({U03A0Intent(2,.40+.15)}, {},Out);
    TestTrue(TEXT("exact grace expiry returns first"),Grace.Current()->GetDefinition().Id==EAction::Attack1);
    FTimelineModel Clear(U03A0Life());Out.Reset();Clear.SubmitBatch({U03A0Intent(1,0),U03A0Intent(2,.30)}, {},Out);
    Clear.ClearPending();Clear.Advance(1,Out);TestNull(TEXT("menu/focus pending clear no successor"),Clear.Current());
    AddInfo(TEXT("U03A0_TRACE buffer .30 -> action2 start .40; active [.58,.65), long endpoint 1.0; expiry .25+.15==.40 rejected"));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Admission,"AnimeMMORPG.U03.A0.AdmissionOrdering",U03A0Flags)
bool FU03Admission::RunTest(const FString&)
{
    for(bool Reverse:{false,true})
    {
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
        TArray<FCombatIntent> B={U03A0Intent(1,0,ECommand::Attack),U03A0Intent(2,0,ECommand::E),U03A0Intent(3,0,ECommand::Q),U03A0Intent(4,0,ECommand::Dodge)};
        if(Reverse) Algo::Reverse(B);
        const auto R=M.SubmitBatch(B,{},Out);
        TestEqual(TEXT("all distinct sequences survive priority sorting"),R.Num(),4);
        TestTrue(TEXT("dodge explicit unsupported"),R[0].Result==EAdmission::Unsupported);
        TestTrue(TEXT("Q before E before attack"),M.Current()->GetDefinition().Id==EAction::Q);
        TestTrue(TEXT("duplicate"),M.SubmitBatch({U03A0Intent(3,.1)}, {},Out)[0].Result==EAdmission::Stale);
        auto Wrong=U03A0Intent(5,.1);Wrong.Life.Generation=2;
        TestTrue(TEXT("wrong life"),M.SubmitBatch({Wrong},{},Out)[0].Result==EAdmission::Invalid);
        TestTrue(TEXT("old time"),M.SubmitBatch({U03A0Intent(6,0)}, {},Out)[0].Result==EAdmission::Invalid);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Resource,"AnimeMMORPG.U03.A0.ResourceAndCutoff",U03A0Flags)
bool FU03Resource::RunTest(const FString&)
{
    FResourceModel R;TestTrue(TEXT("Q spend"),R.Spend(Definition(EAction::Q),0));R.Advance(1);TestEqual(TEXT("at regen deadline"),R.Energy(),80.);R.Advance(1.5);TestEqual(TEXT("integral"),R.Energy(),85.);
    TestFalse(TEXT("CD rejects without cost"),R.Spend(Definition(EAction::Q),1.5));TestEqual(TEXT("no cost"),R.Energy(),85.);
    R.Advance(4);TestTrue(TEXT("exact CD ready"),R.Spend(Definition(EAction::Q),4));
    for(const auto Reason:{ECutoff::Dodge,ECutoff::Guard,ECutoff::Interrupt})
    {
        FActionInstance A(EAction::Attack1,{U03A0Life(),1},0,0);TestFalse(TEXT("invalid replacement preserves action"),A.Cancel(Reason,.1,false));TestFalse(TEXT("exact active start cannot cancel"),A.Cancel(Reason,.16));TestTrue(TEXT("startup cancellable"),A.Cancel(Reason,.15));
    }
    FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;M.SubmitBatch({U03A0Intent(1,0)}, {},Out);
    TestTrue(TEXT("interrupt startup"),M.Cancel(ECutoff::Interrupt,.1,true,Out));M.Advance(1,Out);TestEqual(TEXT("no late active"),Out.Num(),0);
    FResourceModel Poor;
    // Only the two skill definitions consume energy in this reference set.
    TestTrue(TEXT("E cost"),Poor.Spend(Definition(EAction::E),0));
    TestTrue(TEXT("Q cost same timestamp"),Poor.Spend(Definition(EAction::Q),0));
    TestEqual(TEXT("only Q/E cost"),Poor.Energy(),55.);
    TestFalse(TEXT("backwards resource time"),Poor.Advance(-1));
    FTimelineModel Skill(U03A0Life());TArray<FActiveInterval> SkillOut;
    Skill.SubmitBatch({U03A0Intent(1,0)}, {},SkillOut);
    TestTrue(TEXT("Q refuses normal active"),Skill.SubmitBatch({U03A0Intent(2,.16,ECommand::Q)}, {},SkillOut)[0].Result==EAdmission::Busy);
    TestTrue(TEXT("Q takes normal recovery"),Skill.SubmitBatch({U03A0Intent(3,.22,ECommand::Q)}, {},SkillOut)[0].Result==EAdmission::Accepted);
    TestTrue(TEXT("normal never buffers inside Q"),Skill.SubmitBatch({U03A0Intent(4,.30)}, {},SkillOut)[0].Result==EAdmission::Busy);
    TestTrue(TEXT("E cannot cancel Q"),Skill.SubmitBatch({U03A0Intent(5,.31,ECommand::E)}, {},SkillOut)[0].Result==EAdmission::Busy);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Barrier,"AnimeMMORPG.U03.A0.ResolveBarrierAndLethal",U03A0Flags)
bool FU03Barrier::RunTest(const FString&)
{
    // Uses real inherited ledger/comparator; fixture HP/guard deliberately has no runtime adapter.
    for(bool Reverse:{false,true})
    {
        U02::FResolveLedger L;const auto A=U03A0Life(1),B=U03A0Life(2);L.RegisterLife(A);L.RegisterLife(B);
        const U02::FActionId AA{A,1},BB{B,1};L.RegisterAction(AA,.16,.22);L.RegisterAction(BB,.16,.22);
        TArray<U02::FHitCandidate> C={{{AA,B},.18,1},{{BB,A},.18,1},{{AA,B},.19,2}};
        if(Reverse) Algo::Reverse(C);C.Sort(U02::CandidateLess);int32 Hits=0;
        for(const auto& H:C)if(L.ResolveHit(H)){++Hits;L.MarkDead(H.Id.Target);}
        TestEqual(TEXT("same-time lethal only first survives"),Hits,1);TestTrue(TEXT("source1 survives"),L.IsAlive(A));TestFalse(TEXT("source2 dead before retaliation"),L.IsAlive(B));
    }
    FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;M.SubmitBatch({U03A0Intent(1,0)}, {},Out);
    M.Advance(.18,Out);const bool GuardAtHit=false;int32 HP=100;
    // Barrier consumes previously collected hit BEFORE accepting press stamped .18.
    if(Out.Num()>0&&!GuardAtHit)HP-=Out[0].RawDamage;
    auto R=M.SubmitBatch({U03A0Intent(2,.18,ECommand::Guard)}, {},Out);
    TestEqual(TEXT("late guard cannot retroactively block"),HP,40);TestTrue(TEXT("guard runtime deferred"),R[0].Result==EAdmission::Unsupported);
    U02::FResolveLedger L;L.RegisterLife(U03A0Life(1));L.RegisterLife(U03A0Life(2));U02::FActionId Id{U03A0Life(1),1};L.RegisterAction(Id,.16,.22);L.InvalidateAction(Id,.18);
    TestFalse(TEXT("interrupt removes remaining event at cutoff"),L.ResolveHit({{Id,U03A0Life(2)},.18,1}));
    AddInfo(TEXT("U03A0_TRACE sorted .18 source1 kills source2; .18 source2 retaliation invalid; guard press admitted after old .18 hit barrier, HP40"));
    return true;
}
#endif

