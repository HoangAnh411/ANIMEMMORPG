#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U02/U02ActionModel.h"
#include "U01/U01ControlPolicy.h"
#include <limits>

using namespace AnimeMMORPG::U02;
static constexpr auto U02Flags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;
static FLifeId Life(uint32 Id, uint64 Generation = 1) { return {FGuid(Id,0,0,1),Generation}; }

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02Timeline, "AnimeMMORPG.U02.A.PhaseDeadlines", U02Flags)
bool FU02Timeline::RunTest(const FString&)
{
    FAttack1Definition Definition;
    TestTrue(TEXT("Locked definition valid"), Definition.IsValid());
    Definition.ActiveEndSeconds = .23;
    TestFalse(TEXT("Rule override rejected"), Definition.IsValid());
    FActionModel Model(Life(1));
    TestTrue(TEXT("Accept at authority time"), Model.SubmitAttackIntent(1,0,0,{}) == EReject::None);
    const double Times[] = {0,.159,.160,.219,.220,.399,.400};
    const EPhase Phases[] = {EPhase::Startup,EPhase::Startup,EPhase::Active,EPhase::Active,EPhase::Recovery,EPhase::Recovery,EPhase::Finished};
    for (int32 I=0; I<UE_ARRAY_COUNT(Times); ++I)
    {
        FActiveSlice Slice;
        TestTrue(TEXT("Monotonic advance"), Model.AdvanceAction(Times[I],Slice));
        const auto S = Model.GetCombatSnapshot(Times[I]);
        TestTrue(FString::Printf(TEXT("Phase at %.3f"),Times[I]), S.Phase == Phases[I]);
        TestEqual(TEXT("Combat lock follows live action"), S.bCombatLocked, Times[I] < .4);
        AddInfo(FString::Printf(TEXT("U02A_TIMELINE time=%.3f phase=%d slice=%d begin=%.17g end=%.17g endExclusive=%d lock=%d"),
            Times[I],int32(S.Phase),Slice.bEvaluate,Slice.BeginSeconds,Slice.EndSeconds,Slice.bEndExclusive,S.bCombatLocked));
    }
    FActiveSlice Slice;
    TestFalse(TEXT("Backwards clock rejected"),Model.AdvanceAction(.399,Slice));
    TestFalse(TEXT("Nonfinite clock rejected"),Model.AdvanceAction(std::numeric_limits<double>::infinity(),Slice));
    TestTrue(TEXT("Deadline allows new edge immediately"),Model.SubmitAttackIntent(2,.4,0,{})==EReject::None);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02ActiveInterval, "AnimeMMORPG.U02.A.WholeActiveInterval", U02Flags)
bool FU02ActiveInterval::RunTest(const FString&)
{
    FActionModel Model(Life(1)); Model.SubmitAttackIntent(1,0,0,{});
    FActiveSlice Slice;
    Model.AdvanceAction(.5,Slice);
    TestTrue(TEXT("Whole active survives long frame"),Slice.bEvaluate);
    TestEqual(TEXT("Clipped entry"),Slice.BeginSeconds,.16);
    TestEqual(TEXT("Clipped exit"),Slice.EndSeconds,.22);
    TestEqual(TEXT("Previous/current interpolation entry"),Slice.BeginAlpha,.32);
    TestEqual(TEXT("Previous/current interpolation exit"),Slice.EndAlpha,.44);
    TestTrue(TEXT("Exit deadline excluded"),Slice.bEndExclusive);
    AddInfo(FString::Printf(TEXT("U02A_SWEEP previous=0 now=0.5 clipped=[%.17g,%.17g) alpha=[%.17g,%.17g]"),Slice.BeginSeconds,Slice.EndSeconds,Slice.BeginAlpha,Slice.EndAlpha));
    Model.AdvanceAction(.6,Slice); TestFalse(TEXT("No recovery sweep"),Slice.bEvaluate);
    for (double Dt : {1./30,1./60,1./120,.007,.5})
    {
        FActionModel M(Life(1)); M.SubmitAttackIntent(1,0,0,{});
        double Covered=0;
        for (int32 I=1; I*Dt < .5+Dt; ++I)
        {
            M.AdvanceAction(I*Dt,Slice);
            if (Slice.bEvaluate)
            {
                TestTrue(TEXT("Every sample clipped to active"),Slice.BeginSeconds>=.16 && Slice.EndSeconds<=.22);
                Covered += Slice.EndSeconds-Slice.BeginSeconds;
            }
        }
        // Numerical assertion tolerance only; no gameplay comparisons use epsilon.
        TestTrue(TEXT("Partition covers all 60ms active"),FMath::Abs(Covered-.06)<1.e-12);
    }
    FActionModel Point(Life(1)); Point.SubmitAttackIntent(1,0,0,{});
    Point.AdvanceAction(.16,Slice);
    TestTrue(TEXT("Stationary overlap evaluated at exact entry"),Slice.bEvaluate && Slice.BeginSeconds==Slice.EndSeconds);
    Point.AdvanceAction(.16,Slice); TestFalse(TEXT("No duplicate zero-time advance"),Slice.bEvaluate);
    FActionModel Teleport(Life(1)); Teleport.SubmitAttackIntent(1,0,0,{});
    Teleport.AdvanceAction(.18,Slice,false);
    TestTrue(TEXT("Teleport only current active overlap, no connecting sweep"),Slice.bEvaluate && Slice.BeginAlpha==1 && Slice.EndAlpha==1);
    FActionModel Skip(Life(1)); Skip.SubmitAttackIntent(1,0,0,{});
    Skip.AdvanceAction(.3,Slice,false); TestFalse(TEXT("Teleport crossing active does not sweep across arena"),Slice.bEvaluate);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02Cancel, "AnimeMMORPG.U02.A.CancellationAndAim", U02Flags)
bool FU02Cancel::RunTest(const FString&)
{
    for (ECancel Reason : {ECancel::Dodge,ECancel::Guard})
    {
        FActionModel Startup(Life(1)); Startup.SubmitAttackIntent(1,0,0,{});
        TestTrue(TEXT("Real model cancel API accepts startup"),Startup.CancelAction(Reason,.159));
        FActiveSlice S; Startup.AdvanceAction(.5,S); TestFalse(TEXT("Cancelled startup emits no active"),S.bEvaluate);
        for (double Time : {.16,.219,.22,.399})
        {
            FActionModel M(Life(1)); M.SubmitAttackIntent(1,0,0,{});
            TestFalse(TEXT("Voluntary cancel forbidden from active through recovery"),M.CancelAction(Reason,Time));
        }
    }
    for (ECancel Reason : {ECancel::LostGround,ECancel::Death,ECancel::Reset,ECancel::Removed})
    {
        FActionModel M(Life(1)); M.SubmitAttackIntent(1,0,0,{});
        TestTrue(TEXT("Authority invalidation can stop pending active"),M.CancelAction(Reason,.18));
    }
    FActionModel M(Life(1)); M.SubmitAttackIntent(1,0,0,{});
    TestTrue(TEXT("Startup tracks aim"),M.UpdateAim(.159,75));
    TestFalse(TEXT("Active locks yaw at entry"),M.UpdateAim(.16,90));
    TestFalse(TEXT("Recovery keeps yaw"),M.UpdateAim(.22,120));
    TestEqual(TEXT("Locked yaw is latest valid startup aim"),M.GetCombatSnapshot(.22).AimYawDegrees,75.);
    TestFalse(TEXT("Menu does not cancel accepted action"),M.CancelAction(ECancel::Menu,.22));
    TestFalse(TEXT("Focus does not cancel accepted action"),M.CancelAction(ECancel::Focus,.22));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02Intent, "AnimeMMORPG.U02.A.IntentIdentityAndReset", U02Flags)
bool FU02Intent::RunTest(const FString&)
{
    FActionModel M(Life(1));
    TestTrue(TEXT("First accepted"),M.SubmitAttackIntent(1,0,0,{})==EReject::None);
    const FActionId First=M.GetCombatSnapshot(0).Action;
    TestTrue(TEXT("Busy input rejected without buffer"),M.SubmitAttackIntent(2,.1,0,{})==EReject::Busy);
    FActiveSlice Slice; M.AdvanceAction(.4,Slice);
    TestTrue(TEXT("No buffered auto-follow action"),M.GetCombatSnapshot(.4).Phase==EPhase::Finished);
    TestTrue(TEXT("Previously rejected command cannot replay"),M.SubmitAttackIntent(2,.4,0,{})==EReject::StaleCommand);
    TestTrue(TEXT("Reset succeeds"),M.ResetLabCombat(.4));
    const auto ResetSnapshot = M.GetCombatSnapshot(.4);
    TestTrue(TEXT("Idle reset snapshot identifies new life independently of action"),ResetSnapshot.Life==Life(1,2));
    TestTrue(TEXT("Reset snapshot has no stale action or lock"),ResetSnapshot.Phase==EPhase::Idle && ResetSnapshot.Action.Sequence==0 && !ResetSnapshot.bCombatLocked);
    TestTrue(TEXT("Old command remains stale across reset"),M.SubmitAttackIntent(1,.4,0,{})==EReject::StaleCommand);
    TestTrue(TEXT("Fresh edge can accept"),M.SubmitAttackIntent(3,.4,0,{})==EReject::None);
    const FActionId Next=M.GetCombatSnapshot(.4).Action;
    TestFalse(TEXT("Reused sequence is distinct by generation"),Next==First);
    TestEqual(TEXT("Generation increments"),Next.Source.Generation,uint64(2));
    for (int32 Case=0; Case<4; ++Case)
    {
        FActionModel N(Life(1)); FAttackContext C;
        if(Case==0)C.bPlaying=false; if(Case==1)C.bGrounded=false;
        if(Case==2)C.bInteracting=true; if(Case==3)C.bDefeated=true;
        const EReject Expected[]={EReject::NotPlaying,EReject::Airborne,EReject::Interacting,EReject::Defeated};
        TestTrue(TEXT("Authority admission context"),N.SubmitAttackIntent(1,0,0,C)==Expected[Case]);
    }
    FActionModel N(Life(1));
    TestTrue(TEXT("Nonfinite aim rejected"),N.SubmitAttackIntent(1,0,std::numeric_limits<double>::quiet_NaN(),{})==EReject::InvalidAim);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02LockBoundary, "AnimeMMORPG.U02.A.CombatLockReleaseGateBoundary", U02Flags)
bool FU02LockBoundary::RunTest(const FString&)
{
    using AnimeMMORPG::U01::FReleaseGate;
    FReleaseGate Gate; Gate.Down(EKeys::W,false);
    FMotorAuthority Authority; Authority.bCombat=true;
    TestTrue(TEXT("Combat blocks motor"),Authority.BlocksMotor());
    TestFalse(TEXT("Combat does not arm release gate"),Authority.ArmsReleaseGate());
    if(Authority.ArmsReleaseGate())Gate.Lock();
    TestTrue(TEXT("Gravity preserved"),Authority.KeepsGravity());
    TestTrue(TEXT("Client saved move cannot clear server combat lock"),FMotorAuthority::ReplayCombatLock(true,false));
    Authority.bCombat=false;
    TestTrue(TEXT("Held W available after recovery"),!Authority.BlocksMotor() && Gate.Allows(EKeys::W));
    Authority.bControl=true; if(Authority.ArmsReleaseGate())Gate.Lock();
    Authority.bControl=false; TestFalse(TEXT("Menu gate survives combat finish/resume"),Gate.Allows(EKeys::W));
    Gate.Up(EKeys::W); Gate.Down(EKeys::W,false); TestTrue(TEXT("Physical release rearms W"),Gate.Allows(EKeys::W));
    Gate.Down(EKeys::LeftMouseButton,false); Gate.Lock();
    TestFalse(TEXT("Held LMB through menu/resume cannot attack"),Gate.Allows(EKeys::LeftMouseButton));
    Gate.Up(EKeys::LeftMouseButton); Gate.Down(EKeys::LeftMouseButton,false);
    TestTrue(TEXT("New LMB edge rearms"),Gate.Allows(EKeys::LeftMouseButton));
    Authority.bDefeated=true;
    TestTrue(TEXT("Removing combat cannot remove Defeated"),Authority.BlocksMotor());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02Resolve, "AnimeMMORPG.U02.A.ResolveDedupAndGeneration", U02Flags)
bool FU02Resolve::RunTest(const FString&)
{
    FResolveLedger L; const auto A=Life(1),B=Life(2); const FActionId Action{A,1};
    L.RegisterLife(A); L.RegisterLife(B);
    TestTrue(TEXT("Action registered"),L.RegisterAction(Action,.16,.22));
    TestFalse(TEXT("Duplicate action ID cannot replace window"),L.RegisterAction(Action,.16,.5));
    FHitCandidate C{{Action,B},.159,1};
    TestFalse(TEXT("Before active rejected"),L.ResolveHit(C));
    C.TimestampSeconds=.22; TestFalse(TEXT("Exact end excluded"),L.ResolveHit(C));
    C.TimestampSeconds=.16; C.bUnobstructed=false;
    TestFalse(TEXT("Blocked hurtbox does not consume hit"),L.ResolveHit(C));
    C.bUnobstructed=true; C.HurtboxId=2;
    TestTrue(TEXT("Another valid hurtbox can hit at entry"),L.ResolveHit(C));
    TestFalse(TEXT("Duplicate hit ID rejected"),L.ResolveHit(C));
    C.HurtboxId=3; C.TimestampSeconds=.219;
    TestFalse(TEXT("Other hurtbox still same target/action"),L.ResolveHit(C));
    TestTrue(TEXT("Target reset to generation2"),L.RegisterLife(Life(2,2)));
    TestFalse(TEXT("Old event cannot hit new target life"),L.ResolveHit(C));
    C.Id.Target=Life(2,2); TestTrue(TEXT("New target life distinct identity"),L.ResolveHit(C));
    TestTrue(TEXT("Source reset"),L.RegisterLife(Life(1,2)));
    TestFalse(TEXT("Old source action cannot hit after reset"),L.ResolveHit(C));
    TestFalse(TEXT("Old generation registration cannot revive"),L.RegisterLife(A));
    TestTrue(TEXT("Death once"),L.MarkDead(Life(2,2)));
    TestFalse(TEXT("Duplicate death suppressed"),L.MarkDead(Life(2,2)));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02Ordering, "AnimeMMORPG.U02.A.StableResolveDeathOrdering", U02Flags)
bool FU02Ordering::RunTest(const FString&)
{
    const auto A=Life(1),B=Life(2),C=Life(3);
    const FActionId AttackA{A,1}, AttackB{B,1};
    const TArray<FHitCandidate> Events={{{AttackB,A},.18,2},{{AttackA,B},.18,2},{{AttackA,B},.18,1},{{AttackA,C},.19,1}};
    int32 Permutations=0;
    // All 24 collection permutations, not merely forward/reverse.
    for(int32 I=0;I<4;++I)for(int32 J=0;J<4;++J)for(int32 K=0;K<4;++K)for(int32 N=0;N<4;++N)
    {
        if(I==J||I==K||I==N||J==K||J==N||K==N)continue;
        TArray<FHitCandidate> Sorted={Events[I],Events[J],Events[K],Events[N]}; Sorted.Sort(CandidateLess);
        FResolveLedger L; L.RegisterLife(A);L.RegisterLife(B);L.RegisterLife(C);
        L.RegisterAction(AttackA,.16,.22);L.RegisterAction(AttackB,.16,.22);
        int32 Accepted=0,Deaths=0;
        TestEqual(TEXT("Stable hurtbox tie break"),Sorted[0].HurtboxId,uint32(1));
        for(const auto& Event:Sorted)
        {
            if(!L.ResolveHit(Event))continue;
            ++Accepted;
            // Lethal fixture only: no damage implementation in A.
            if(Event.Id.Target==B)Deaths+=L.MarkDead(B)?1:0;
        }
        TestEqual(TEXT("Killed source same timestamp cannot retaliate; duplicate suppressed"),Accepted,2);
        TestEqual(TEXT("Death emitted once"),Deaths,1);
        TestTrue(TEXT("Lowest source ID survives lethal tie"),L.IsAlive(A)&&!L.IsAlive(B));
        ++Permutations;
    }
    TestEqual(TEXT("All candidate collection permutations tested"),Permutations,24);
    FResolveLedger L;L.RegisterLife(A);L.RegisterLife(B);L.RegisterAction(AttackA,.16,.22);
    L.InvalidateAction(AttackA,.18);
    TestFalse(TEXT("Cancel clips pending hit at exact cutoff"),L.ResolveHit({{AttackA,B},.18,1}));
    TestTrue(TEXT("Earlier active event remains eligible"),L.ResolveHit({{AttackA,B},.17,1}));
    AddInfo(TEXT("U02A_ORDER permutations=24 source1->source2 lethal@0.18; source2 retaliation rejected; death=1; source1->source3@0.19 accepted"));
    return true;
}
#endif
