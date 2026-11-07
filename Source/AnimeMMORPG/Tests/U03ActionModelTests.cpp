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
    AddInfo(FString::Printf(TEXT("U03A0_TRACE oldAction=%llu oldRaw=%d newAction=%llu newRaw=%d"),Old.Identity.Sequence,Old.GetDefinition().RawDamage,New.Identity.Sequence,New.GetDefinition().RawDamage));
    TestEqual(TEXT("old immutable raw"),Old.GetDefinition().RawDamage,60);TestEqual(TEXT("new raw"),New.GetDefinition().RawDamage,100);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Timeline,"AnimeMMORPG.U03.A0.TimelineAndBuffer",U03A0Flags)
bool FU03Timeline::RunTest(const FString&)
{
    for(const double Step:{1./30,1./60,1./120,2.})
    {
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
        M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);M.SubmitBatchUnopposed({U03A0Intent(2,.30)}, {},Out);
        for(double T=.30+Step;T<1.;T+=Step) M.AdvanceUnopposed(T,Out);
        M.AdvanceUnopposed(1.,Out);double Total=0;bool Second=false;
        for(const auto& S:Out){AddInfo(FString::Printf(TEXT("U03A0_TRACE step=%.17g action=%llu definition=%u raw=%d interval=%c%.17g,%.17g%c yaw=%.17g"),Step,S.Identity.Sequence,static_cast<uint32>(S.DefinitionId),S.RawDamage,TCHAR('['),S.Begin,S.End,S.bEndExclusive?TCHAR(')'):TCHAR(']'),S.Yaw));
            Total+=S.End-S.Begin;Second|=S.DefinitionId==EAction::Attack2;TestTrue(TEXT("nonempty clipped"),S.Begin<=S.End);}
        TestTrue(TEXT("whole active both actions"),FMath::Abs(Total-.13)<1e-12);TestTrue(TEXT("buffer starts second within long update"),Second);
    }
    FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
    M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    auto R=M.SubmitBatchUnopposed({U03A0Intent(2,.25)}, {},Out);TestTrue(TEXT("queue"),R[0].Result==EAdmission::Queued);
    M.AdvanceUnopposed(.40,Out);TestNull(TEXT("expiry exactly end not consumed"),M.Current());
    M.SubmitBatchUnopposed({U03A0Intent(3,.40)}, {},Out);TestTrue(TEXT("new edge exactly end uses combo grace"),M.Current()->GetDefinition().Id==EAction::Attack2);
    FTimelineModel N(U03A0Life());Out.Reset();N.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    N.SubmitBatchUnopposed({U03A0Intent(2,.26,ECommand::Attack,10)}, {},Out);
    R=N.SubmitBatchUnopposed({U03A0Intent(3,.35,ECommand::Attack,30)}, {},Out);TestTrue(TEXT("replacement"),R[0].Result==EAdmission::Replaced);
    N.AdvanceUnopposed(.40,Out);TestEqual(TEXT("known queued aim"),N.Current()->Yaw,30.);
    N.SubmitBatchUnopposed({U03A0Intent(4,.75)}, {},Out);N.AdvanceUnopposed(.40+.45,Out);TestTrue(TEXT("third"),N.Current()->GetDefinition().Id==EAction::Attack3);
    N.SubmitBatchUnopposed({U03A0Intent(5,1.35)}, {},Out);N.AdvanceUnopposed(.40+.45+.60,Out);TestTrue(TEXT("third buffers first"),N.Current()->GetDefinition().Id==EAction::Attack1);
    FTimelineModel Combo(U03A0Life()); Out.Reset();
    Combo.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    Combo.SubmitBatchUnopposed({U03A0Intent(2,.30)}, {},Out);
    Combo.SubmitBatchUnopposed({U03A0Intent(3,.75)}, {},Out);
    Combo.AdvanceUnopposed(.40+.45+.60,Out);
    int32 Sum=0; TArray<uint64> Seen;
    for(const auto& Slice:Out) if(!Seen.Contains(Slice.Identity.Sequence)){Seen.Add(Slice.Identity.Sequence);Sum+=Slice.RawDamage;}
    TestEqual(TEXT("three definitions total220 raw"),Sum,220);
    TestNull(TEXT("chain ends at sum durations"),Combo.Current());
    FTimelineModel Grace(U03A0Life()); Out.Reset();Grace.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    Grace.SubmitBatchUnopposed({U03A0Intent(2,.40+.15)}, {},Out);
    TestTrue(TEXT("exact grace expiry returns first"),Grace.Current()->GetDefinition().Id==EAction::Attack1);
    FTimelineModel Clear(U03A0Life());Out.Reset();Clear.SubmitBatchUnopposed({U03A0Intent(1,0),U03A0Intent(2,.30)}, {},Out);
    Clear.ClearPending();Clear.AdvanceUnopposed(1,Out);TestNull(TEXT("menu/focus pending clear no successor"),Clear.Current());
    AddInfo(TEXT("U03A0_TRACE buffer .30 -> action2 start .40; active [.58,.65), long endpoint 1.0; expiry .25+.15==.40 rejected"));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03Admission,"AnimeMMORPG.U03.A0.AdmissionOrdering",U03A0Flags)
bool FU03Admission::RunTest(const FString&)
{
    for(bool Reverse:{false,true})
    {
        FTimelineModel Bad(U03A0Life()); TArray<FActiveInterval> BadOut;
        TArray<FCombatIntent> Copies={U03A0Intent(1,0,ECommand::Attack),U03A0Intent(1,0,ECommand::Q)};
        if(Reverse) Algo::Reverse(Copies);
        const auto Invalid=Bad.SubmitBatchUnopposed(Copies,{},BadOut);
        TestEqual(TEXT("conflicting duplicate copies rejected"),Invalid.Num(),2);
        TestTrue(TEXT("malformed duplicate invalid"),Invalid[0].Result==EAdmission::Invalid && Invalid[1].Result==EAdmission::Invalid);
        TestNull(TEXT("collection cannot choose conflicting duplicate action"),Bad.Current());
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
        TArray<FCombatIntent> B={U03A0Intent(1,0,ECommand::Attack),U03A0Intent(2,0,ECommand::E),U03A0Intent(3,0,ECommand::Q),U03A0Intent(4,0,ECommand::Dodge)};
        if(Reverse) Algo::Reverse(B);
        const auto R=M.SubmitBatchUnopposed(B,{},Out);
        TestEqual(TEXT("all distinct sequences survive priority sorting"),R.Num(),4);
        TestTrue(TEXT("dodge explicit unsupported"),R[0].Result==EAdmission::Unsupported);
        TestTrue(TEXT("Q before E before attack"),M.Current()->GetDefinition().Id==EAction::Q);
        TestTrue(TEXT("duplicate"),M.SubmitBatchUnopposed({U03A0Intent(3,.1)}, {},Out)[0].Result==EAdmission::Stale);
        auto Wrong=U03A0Intent(5,.1);Wrong.Life.Generation=2;
        TestTrue(TEXT("wrong life"),M.SubmitBatchUnopposed({Wrong},{},Out)[0].Result==EAdmission::Invalid);
        TestTrue(TEXT("old time"),M.SubmitBatchUnopposed({U03A0Intent(6,0)}, {},Out)[0].Result==EAdmission::Invalid);
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
    FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    TestTrue(TEXT("interrupt startup"),M.CancelUnopposed(ECutoff::Interrupt,.1,true,Out));M.AdvanceUnopposed(1,Out);TestEqual(TEXT("no late active"),Out.Num(),0);
    FResourceModel Poor;
    // Only the two skill definitions consume energy in this reference set.
    TestTrue(TEXT("E cost"),Poor.Spend(Definition(EAction::E),0));
    TestTrue(TEXT("Q cost same timestamp"),Poor.Spend(Definition(EAction::Q),0));
    TestEqual(TEXT("only Q/E cost"),Poor.Energy(),55.);
    TestFalse(TEXT("backwards resource time"),Poor.Advance(-1));
    FTimelineModel Skill(U03A0Life());TArray<FActiveInterval> SkillOut;
    Skill.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},SkillOut);
    TestTrue(TEXT("Q refuses normal active"),Skill.SubmitBatchUnopposed({U03A0Intent(2,.16,ECommand::Q)}, {},SkillOut)[0].Result==EAdmission::Busy);
    TestTrue(TEXT("Q takes normal recovery"),Skill.SubmitBatchUnopposed({U03A0Intent(3,.22,ECommand::Q)}, {},SkillOut)[0].Result==EAdmission::Accepted);
    TestTrue(TEXT("normal never buffers inside Q"),Skill.SubmitBatchUnopposed({U03A0Intent(4,.30)}, {},SkillOut)[0].Result==EAdmission::Busy);
    TestTrue(TEXT("E cannot cancel Q"),Skill.SubmitBatchUnopposed({U03A0Intent(5,.31,ECommand::E)}, {},SkillOut)[0].Result==EAdmission::Busy);
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
        for(const auto& H:C)
        {
            const bool Accepted=L.ResolveHit(H);
            AddInfo(FString::Printf(TEXT("U03A0_TRACE reverse=%d hit=%.17g source=%u action=%llu target=%u hurtbox=%u accepted=%d"),Reverse,H.TimestampSeconds,H.Id.Action.Source.Pawn.A,H.Id.Action.Sequence,H.Id.Target.Pawn.A,H.HurtboxId,Accepted));
            if(Accepted){++Hits;L.MarkDead(H.Id.Target);}
        }
        TestEqual(TEXT("same-time lethal only first survives"),Hits,1);TestTrue(TEXT("source1 survives"),L.IsAlive(A));TestFalse(TEXT("source2 dead before retaliation"),L.IsAlive(B));
    }
    FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    M.AdvanceUnopposed(.18,Out);
    TestEqual(TEXT("barrier reaches receive timestamp"),Out.Last().End,.18);
    TestFalse(TEXT("hit at current active endpoint belongs to old barrier"),Out.Last().bEndExclusive);
    const bool GuardAtHit=false;int32 HP=100;
    // Barrier consumes previously collected hit BEFORE accepting press stamped .18.
    if(Out.Num()>0&&!GuardAtHit)HP-=Out[0].RawDamage;
    auto R=M.SubmitBatchUnopposed({U03A0Intent(2,.18,ECommand::Guard)}, {},Out);
    AddInfo(FString::Printf(TEXT("U03A0_TRACE barrier=%.17g exclusive=%d HP=%d guardAdmission=%u"),Out.Last().End,Out.Last().bEndExclusive,HP,static_cast<uint32>(R[0].Result)));
    TestEqual(TEXT("late guard cannot retroactively block"),HP,40);TestTrue(TEXT("guard runtime deferred"),R[0].Result==EAdmission::Unsupported);
    U02::FResolveLedger L;L.RegisterLife(U03A0Life(1));L.RegisterLife(U03A0Life(2));U02::FActionId Id{U03A0Life(1),1};L.RegisterAction(Id,.16,.22);L.InvalidateAction(Id,.18);
    TestFalse(TEXT("interrupt removes remaining event at cutoff"),L.ResolveHit({{Id,U03A0Life(2)},.18,1}));
    AddInfo(TEXT("U03A0_TRACE sorted .18 source1 kills source2; .18 source2 retaliation invalid; guard press admitted after old .18 hit barrier, HP40"));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03IntegratedTimeline,"AnimeMMORPG.U03.A0.LongUpdateResolverInterruptAndDeath",U03A0Flags)
bool FU03IntegratedTimeline::RunTest(const FString&)
{
    struct FResolver final : ITimelineResolver
    {
        U02::FResolveLedger Ledger;
        TArray<U02::FHitCandidate> Events;
        TArray<FActiveInterval> Intervals;
        ECutoff Reason; bool Accepted=false; int32 Confirmed=0, LateHits=0;
        FResolver(ECutoff InReason, bool Reverse) : Reason(InReason)
        {
            Ledger.RegisterLife(U03A0Life(1)); Ledger.RegisterLife(U03A0Life(2));
            Ledger.RegisterAction({U03A0Life(2),1},.45,.50);
            Events={{{{U03A0Life(2),1},U03A0Life(1)},.45,1},{{{U03A0Life(1),2},U03A0Life(2)},.60,1}};
            if(Reverse) Algo::Reverse(Events);
            Events.Sort(U02::CandidateLess);
        }
        TOptional<double> NextEvent(const FTimelineModel& M,double Through) override
        {
            if(const auto* A=M.Current())
                Ledger.RegisterAction(A->Identity,A->Start+A->GetDefinition().ActiveStart,A->Start+A->GetDefinition().ActiveEnd);
            return Events.Num() && Events[0].TimestampSeconds<=Through ? TOptional<double>(Events[0].TimestampSeconds) : TOptional<double>();
        }
        void ResolveInterval(const FActiveInterval& I) override
        {
            Intervals.Add(I);
            if(I.Begin<=.18 && (I.End>.18 || (I.End==.18&&!I.bEndExclusive)))
                if(Ledger.ResolveHit({{I.Identity,U03A0Life(2)},.18,1})) ++Confirmed;
        }
        void ResolveEvent(FTimelineModel& M,double At) override
        {
            const auto E=Events[0]; Events.RemoveAt(0);
            if(!Ledger.ResolveHit(E)) return;
            if(At==.45)
            {
                const auto* A=M.Current();
                if(A && A->GetDefinition().Id==EAction::Attack2 && A->Start==.40 && M.Time()==.45)
                {
                    const auto Id=A->Identity;
                    Accepted=M.CancelCurrent(Reason);
                    Ledger.InvalidateAction(Id,At);
                    if(Reason==ECutoff::Death) Ledger.MarkDead(U03A0Life(1));
                }
            }
            else ++LateHits;
        }
    };
    for(const auto Reason:{ECutoff::Interrupt,ECutoff::Death}) for(bool Reverse:{false,true})
    {
        FTimelineModel M(U03A0Life()); TArray<FActiveInterval> Setup;
        M.SubmitBatchUnopposed({U03A0Intent(1,0),U03A0Intent(2,.30)}, {},Setup);
        FResolver Resolver(Reason,Reverse);
        // Include the already-confirmed interval from setup in the same real ledger.
        Resolver.Ledger.RegisterAction({U03A0Life(),1},.16,.22);
        for(const auto& I:Setup) Resolver.ResolveInterval(I);
        TestTrue(TEXT("long update completes"),M.Advance(1.,Resolver));
        TestTrue(TEXT("resolver interrupts/deaths live successor at .45 before endpoint1"),Resolver.Accepted);
        TestNull(TEXT("successor removed"),M.Current());
        TestEqual(TEXT("confirmed earlier hit retained"),Resolver.Confirmed,1);
        TestEqual(TEXT("late source event removed by cutoff/death"),Resolver.LateHits,0);
        TestFalse(TEXT("no successor active interval ever published"),Resolver.Intervals.ContainsByPredicate([](const auto& I){return I.DefinitionId==EAction::Attack2;}));
        AddInfo(FString::Printf(TEXT("U03A0_TRACE integrated reason=%u reverse=%d acceptedAt=.45 successorStart=.40 confirmed=%d late=%d final=%.17g"),static_cast<uint32>(Reason),Reverse,Resolver.Confirmed,Resolver.LateHits,M.Time()));
    }
    struct FBoundaryDeath final : ITimelineResolver
    {
        bool Pending=true;
        TOptional<double> NextEvent(const FTimelineModel&,double Through) override
        { return Pending&&Through>=.40?TOptional<double>(.40):TOptional<double>(); }
        void ResolveInterval(const FActiveInterval&) override {}
        void ResolveEvent(FTimelineModel& M,double) override { Pending=false;M.CancelCurrent(ECutoff::Death); }
    };
    FTimelineModel BoundaryDead(U03A0Life());TArray<FActiveInterval> BoundarySetup;
    BoundaryDead.SubmitBatchUnopposed({U03A0Intent(1,0),U03A0Intent(2,.30)}, {},BoundarySetup);
    FBoundaryDeath BoundaryResolver;
    TestTrue(TEXT("death exactly action-end completes update"),BoundaryDead.Advance(1.,BoundaryResolver));
    TestNull(TEXT("death at action-end cannot consume pending successor"),BoundaryDead.Current());
    // Submission cannot bypass the same resolver barrier and admit after a death event.
    FTimelineModel Dead(U03A0Life());TArray<FActiveInterval> Setup;
    Dead.SubmitBatchUnopposed({U03A0Intent(1,0),U03A0Intent(2,.30)}, {},Setup);
    FResolver Resolver(ECutoff::Death,false);
    const auto R=Dead.SubmitBatch({U03A0Intent(3,1.)},{},Resolver);
    TestTrue(TEXT("death resolved before admission even with stale context"),R[0].Result==EAdmission::Locked);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03CutoffIntervals,"AnimeMMORPG.U03.A0.CutoffIntervalsAndConfirmedHits",U03A0Flags)
bool FU03CutoffIntervals::RunTest(const FString&)
{
    auto Contains=[](const TArray<FActiveInterval>& Out,double T)
    { return Out.ContainsByPredicate([&](const auto& I){return T>=I.Begin&&(T<I.End||(T==I.End&&!I.bEndExclusive));}); };
    for(const auto Reason:{ECutoff::Death,ECutoff::LostGround})
    {
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
        M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
        TestTrue(TEXT("valid forced cutoff"),M.CancelUnopposed(Reason,.18,true,Out));
        TestTrue(TEXT("contact immediately before cutoff remains"),Contains(Out,.179999));
        TestFalse(TEXT("contact exactly cutoff excluded"),Contains(Out,.18));
        M.AdvanceUnopposed(1.,Out);TestFalse(TEXT("no later contact"),Contains(Out,.19));
    }
    FTimelineModel Invalid(U03A0Life());TArray<FActiveInterval> Out;
    Invalid.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    TestFalse(TEXT("active guard cancel invalid"),Invalid.CancelUnopposed(ECutoff::Guard,.18,true,Out));
    TestTrue(TEXT("invalid cancellation preserves current contact"),Contains(Out,.18));
    FTimelineModel Confirmed(U03A0Life());Out.Reset();Confirmed.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
    Confirmed.AdvanceUnopposed(.17,Out);
    U02::FResolveLedger Ledger;Ledger.RegisterLife(U03A0Life(1));Ledger.RegisterLife(U03A0Life(2));
    Ledger.RegisterAction({U03A0Life(1),1},.16,.22);
    TestTrue(TEXT("earlier contact confirmed"),Ledger.ResolveHit({{{U03A0Life(1),1},U03A0Life(2)},.17,1}));
    const int32 EarlierCount=Out.Num();
    TestTrue(TEXT("later death valid"),Confirmed.CancelUnopposed(ECutoff::Death,.18,true,Out));
    TestTrue(TEXT("published earlier contact never erased"),Out.Num()>=EarlierCount&&Contains(Out,.17));
    TestFalse(TEXT("cannot rewind confirmed time"),Confirmed.CancelUnopposed(ECutoff::Death,.16,true,Out));
    TestFalse(TEXT("confirmed ledger dedup persists"),Ledger.ResolveHit({{{U03A0Life(1),1},U03A0Life(2)},.17,1}));
    AddInfo(TEXT("U03A0_TRACE cutoff=.18 before=.179999 retained; exact excluded; invalid guard preserves endpoint; confirmed .17 never rewound"));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03TimestampGroup,"AnimeMMORPG.U03.A0.TimestampGroupBeforeTransitionAndAdmission",U03A0Flags)
bool FU03TimestampGroup::RunTest(const FString&)
{
    struct FGroup final : ITimelineResolver
    {
        double At; U02::FResolveLedger Ledger; TArray<U02::FHitCandidate> Events;
        TArray<uint32> Order; int32 HP=100, Deaths=0, EndpointSamples=0;
        bool SawPrematureSuccessor=false, DeathAccepted=false;
        FGroup(double InAt,bool Reverse) : At(InAt)
        {
            for(uint32 Id=1;Id<=4;++Id) Ledger.RegisterLife(U03A0Life(Id));
            for(uint32 Id=2;Id<=4;++Id) Ledger.RegisterAction({U03A0Life(Id),1},At,At+.01);
            Events={{{{U03A0Life(2),1},U03A0Life(1)},At,1},{{{U03A0Life(3),1},U03A0Life(1)},At,1}};
            if(Reverse) Algo::Reverse(Events);
            Events.Sort(U02::CandidateLess);
        }
        TOptional<double> NextEvent(const FTimelineModel&,double Through) override
        { return Events.Num()&&Events[0].TimestampSeconds<=Through?TOptional<double>(Events[0].TimestampSeconds):TOptional<double>(); }
        void ResolveInterval(const FActiveInterval& I) override
        { if(I.Begin==At&&I.End==At) ++EndpointSamples; }
        void ResolveEvent(FTimelineModel& M,double Now) override
        {
            const auto E=Events[0];Events.RemoveAt(0);Order.Add(E.Id.Action.Source.Pawn.A);
            SawPrematureSuccessor|=M.Current()&&M.Current()->Identity.Sequence!=1;
            if(E.Id.Action.Source.Pawn.A==2)
            {
                // A callback can discover another event at the same timestamp.
                Events.Add({{{U03A0Life(4),1},U03A0Life(1)},At,1});Events.Sort(U02::CandidateLess);
            }
            if(!Ledger.ResolveHit(E)) return;
            HP-=E.Id.Action.Source.Pawn.A==2?20:100;
            if(HP<=0){++Deaths;Ledger.MarkDead(U03A0Life(1));DeathAccepted=M.CancelCurrent(ECutoff::Death);}
        }
    };
    for(double At:{.18,.40}) for(bool Reverse:{false,true}) for(bool Long:{false,true}) for(bool Submit:{false,true})
    {
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Setup;
        M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Setup);
        if(At==.40) M.SubmitBatchUnopposed({U03A0Intent(2,.30)}, {},Setup);
        FGroup Resolver(At,Reverse);const double End=Long?1.:At;
        if(Submit)
        {
            const auto R=M.SubmitBatch({U03A0Intent(3,End)},{},Resolver);
            TestTrue(TEXT("later death in timestamp group precedes admission"),R.Num()==1&&R[0].Result==EAdmission::Locked);
        }
        else TestTrue(TEXT("advance completes full endpoint group"),M.Advance(End,Resolver));
        TestEqual(TEXT("all three events including dynamically discovered one delivered"),Resolver.Order.Num(),3);
        TestTrue(TEXT("stable source order despite collection reverse"),Resolver.Order==TArray<uint32>{2,3,4});
        TestTrue(TEXT("second event death accepted"),Resolver.DeathAccepted);
        TestEqual(TEXT("dead target excludes third hit"),Resolver.Deaths,1);
        TestFalse(TEXT("no successor between same-time events"),Resolver.SawPrematureSuccessor);
        TestEqual(TEXT("no endpoint sample before lethal event"),Resolver.EndpointSamples,0);
        TestNull(TEXT("death suppresses pending successor"),M.Current());
        TestEqual(TEXT("timestamp group empty before return"),Resolver.Events.Num(),0);
        AddInfo(FString::Printf(TEXT("U03A0_TRACE group at=%.17g end=%.17g reverse=%d submit=%d order=2,3,4 hp=%d deaths=%d premature=%d endpointSamples=%d remaining=%d"),At,End,Reverse,Submit,Resolver.HP,Resolver.Deaths,Resolver.SawPrematureSuccessor,Resolver.EndpointSamples,Resolver.Events.Num()));
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03LostGroundBoundary,"AnimeMMORPG.U03.A0.LostGroundAtActionEndAndGrace",U03A0Flags)
bool FU03LostGroundBoundary::RunTest(const FString&)
{
    struct FGroundEvent final : ITimelineResolver
    {
        double At;bool Grounded,Pending=true,Accepted=false;
        FGroundEvent(double InAt,bool InGrounded):At(InAt),Grounded(InGrounded){}
        TOptional<double> NextEvent(const FTimelineModel&,double Through) override
        { return Pending&&At<=Through?TOptional<double>(At):TOptional<double>(); }
        void ResolveInterval(const FActiveInterval&) override {}
        void ResolveEvent(FTimelineModel& M,double) override
        { Pending=false;Accepted=Grounded?M.SetGroundedCurrent(true):M.CancelCurrent(ECutoff::LostGround); }
    };
    for(double At:{.40,.45}) for(bool Long:{false,true})
    {
        FTimelineModel M(U03A0Life());TArray<FActiveInterval> Out;
        M.SubmitBatchUnopposed({U03A0Intent(1,0)}, {},Out);
        if(At==.40) M.SubmitBatchUnopposed({U03A0Intent(2,.30)}, {},Out);
        FGroundEvent Lost(At,false);const double End=Long?1.:At;
        const auto R=M.SubmitBatch({U03A0Intent(3,End)},{},Lost);
        TestTrue(TEXT("floor-loss accepted even ended action or idle grace"),Lost.Accepted);
        TestTrue(TEXT("stale grounded context cannot admit airborne attack"),R.Num()==1&&R[0].Result==EAdmission::Locked);
        TestNull(TEXT("floor-loss never consumes successor buffer"),M.Current());
        TestFalse(TEXT("caller cannot grant landing outside resolver"),M.SetGroundedCurrent(true));
        FGroundEvent Landing(End+.01,true);
        const auto Landed=M.SubmitBatch({U03A0Intent(4,End+.01)},{},Landing);
        TestTrue(TEXT("explicit authority landing event accepted"),Landing.Accepted);
        TestTrue(TEXT("fresh command after landing accepted"),Landed.Num()==1&&Landed[0].Result==EAdmission::Accepted);
        TestTrue(TEXT("combo/grace reset to first after actual landing"),M.Current()&&M.Current()->GetDefinition().Id==EAction::Attack1);
        AddInfo(FString::Printf(TEXT("U03A0_TRACE floorLoss=%.17g advanceEnd=%.17g accepted=%d airborneAdmission=%u landing=%.17g nextDefinition=%u"),At,End,Lost.Accepted,static_cast<uint32>(R[0].Result),End+.01,static_cast<uint32>(M.Current()->GetDefinition().Id)));
    }
    return true;
}

#endif

