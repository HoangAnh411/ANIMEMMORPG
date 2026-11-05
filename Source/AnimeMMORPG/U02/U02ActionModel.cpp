#include "U02ActionModel.h"

namespace AnimeMMORPG::U02
{
bool FAttack1Definition::IsValid() const
{
    // Locked action configuration; per-instance Blueprint rule overrides are forbidden.
    return ActiveStartSeconds == .16 && ActiveEndSeconds == .22 && DurationSeconds == .40 && RawDamage == 60
        && HalfExtentsCm == FVector(100,60,90) && CenterFromFeetCm == FVector(100,0,90);
}
bool PawnLess(const FGuid& A, const FGuid& B)
{
    if (A.A != B.A) return A.A < B.A;
    if (A.B != B.B) return A.B < B.B;
    if (A.C != B.C) return A.C < B.C;
    return A.D < B.D;
}
static bool LifeLess(const FLifeId& A, const FLifeId& B)
{
    return A.Pawn != B.Pawn ? PawnLess(A.Pawn,B.Pawn) : A.Generation < B.Generation;
}
bool HitLess(const FHitId& A, const FHitId& B)
{
    if (!(A.Action.Source == B.Action.Source)) return LifeLess(A.Action.Source,B.Action.Source);
    if (A.Action.Sequence != B.Action.Sequence) return A.Action.Sequence < B.Action.Sequence;
    return LifeLess(A.Target,B.Target);
}
bool CandidateLess(const FHitCandidate& A, const FHitCandidate& B)
{
    if (A.TimestampSeconds != B.TimestampSeconds) return A.TimestampSeconds < B.TimestampSeconds;
    if (A.Id.Action.Source.Pawn != B.Id.Action.Source.Pawn) return PawnLess(A.Id.Action.Source.Pawn,B.Id.Action.Source.Pawn);
    if (!(A.Id == B.Id)) return HitLess(A.Id,B.Id);
    return A.HurtboxId < B.HurtboxId;
}
bool FActionModel::ValidNow(double Now) const
{
    return FMath::IsFinite(Now) && Now >= 0 && Now >= LastObserved;
}
EPhase FActionModel::PhaseAt(double Now) const
{
    if (!bHasAction) return EPhase::Idle;
    if (bCancelled) return EPhase::Cancelled;
    if (Now < Start + Definition.ActiveStartSeconds) return EPhase::Startup;
    if (Now < Start + Definition.ActiveEndSeconds) return EPhase::Active;
    if (Now < Start + Definition.DurationSeconds) return EPhase::Recovery;
    return EPhase::Finished;
}
EReject FActionModel::SubmitAttackIntent(uint64 Command, double Now, double Yaw, const FAttackContext& Context)
{
    if (!ValidNow(Now)) return EReject::InvalidTime;
    LastObserved = Now;
    if (Command == 0 || Command <= LastCommandSequence) return EReject::StaleCommand;
    LastCommandSequence = Command; // Rejected commands cannot be replayed after unlock.
    if (!FMath::IsFinite(Yaw)) return EReject::InvalidAim;
    if (!Context.bPlaying) return EReject::NotPlaying;
    if (!Context.bGrounded) return EReject::Airborne;
    if (Context.bInteracting) return EReject::Interacting;
    if (Context.bDefeated) return EReject::Defeated;
    const EPhase Phase = PhaseAt(Now);
    if (Phase == EPhase::Startup || Phase == EPhase::Active || Phase == EPhase::Recovery) return EReject::Busy;
    // Adapter must advance/resolve old intervals before accepting a new action.
    Start = LastAdvance = Now;
    AimYaw = FRotator::NormalizeAxis(Yaw);
    Action = {Life, ++NextActionSequence};
    bHasAction = true;
    bCancelled = false;
    return EReject::None;
}
bool FActionModel::AdvanceAction(double Now, FActiveSlice& Out, bool bContinuous)
{
    Out = {};
    if (!ValidNow(Now)) return false;
    LastObserved = Now;
    if (bHasAction && !bCancelled && Now > LastAdvance)
    {
        const double ActiveBegin = Start + Definition.ActiveStartSeconds;
        const double ActiveEnd = Start + Definition.ActiveEndSeconds;
        const double Begin = bContinuous ? FMath::Max(LastAdvance,ActiveBegin) : Now;
        const double End = FMath::Min(Now,ActiveEnd);
        // Includes a point overlap at exact active entry, excludes exact active exit.
        if (Begin <= End && Begin >= ActiveBegin && Begin < ActiveEnd)
        {
            Out.bEvaluate = true;
            Out.BeginSeconds = Begin;
            Out.EndSeconds = End;
            Out.BeginAlpha = (Begin-LastAdvance)/(Now-LastAdvance);
            Out.EndAlpha = (End-LastAdvance)/(Now-LastAdvance);
            Out.bEndExclusive = End == ActiveEnd;
        }
    }
    LastAdvance = Now;
    return true;
}
bool FActionModel::UpdateAim(double Now, double Yaw)
{
    if (!ValidNow(Now) || !FMath::IsFinite(Yaw) || PhaseAt(Now) != EPhase::Startup) return false;
    LastObserved = Now;
    AimYaw = FRotator::NormalizeAxis(Yaw);
    return true;
}
bool FActionModel::CancelAction(ECancel Reason, double Now)
{
    if (!ValidNow(Now) || !bHasAction || bCancelled) return false;
    LastObserved = Now;
    const EPhase Phase = PhaseAt(Now);
    if (Phase == EPhase::Finished) return false;
    if (Reason == ECancel::Menu || Reason == ECancel::Focus) return false;
    if ((Reason == ECancel::Dodge || Reason == ECancel::Guard) && Phase != EPhase::Startup) return false;
    bCancelled = true;
    return true;
}
bool FActionModel::ResetLabCombat(double Now)
{
    if (!ValidNow(Now) || Life.Generation == MAX_uint64) return false;
    ++Life.Generation;
    bHasAction = bCancelled = false;
    Action = {};
    Start = AimYaw = 0;
    NextActionSequence = 0;
    LastObserved = LastAdvance = Now;
    // Command anti-replay belongs to connection/session; do not reset it with life.
    return true;
}
FCombatSnapshot FActionModel::GetCombatSnapshot(double Now) const
{
    FCombatSnapshot Result;
    Result.Life = Life;
    Result.Action = Action;
    Result.Phase = PhaseAt(Now);
    Result.StartSeconds = Start;
    Result.ActiveStartSeconds = Start + Definition.ActiveStartSeconds;
    Result.ActiveEndSeconds = Start + Definition.ActiveEndSeconds;
    Result.EndSeconds = Start + Definition.DurationSeconds;
    Result.LastAdvanceSeconds = LastAdvance;
    Result.AimYawDegrees = AimYaw;
    Result.bCombatLocked = Result.Phase == EPhase::Startup || Result.Phase == EPhase::Active || Result.Phase == EPhase::Recovery;
    Result.bYawLocked = Result.Phase == EPhase::Active || Result.Phase == EPhase::Recovery;
    return Result;
}
bool FResolveLedger::IsAlive(FLifeId Life) const
{
    return Subjects.ContainsByPredicate([&](const FSubject& S) { return S.Life == Life && S.bAlive; });
}
bool FResolveLedger::RegisterLife(FLifeId Life)
{
    if (!Life.Pawn.IsValid() || Life.Generation == 0) return false;
    for (FSubject& Subject : Subjects)
    {
        if (Subject.Life.Pawn != Life.Pawn) continue;
        if (Life.Generation <= Subject.Life.Generation) return false;
        Subject = {Life,true};
        Windows.RemoveAll([&](const FWindow& W) { return W.Action.Source.Pawn == Life.Pawn; });
        Resolved.RemoveAll([&](const FHitId& Hit) { return Hit.Action.Source.Pawn == Life.Pawn || Hit.Target.Pawn == Life.Pawn; });
        return true;
    }
    Subjects.Add({Life,true});
    return true;
}
bool FResolveLedger::RegisterAction(FActionId Action, double Begin, double End)
{
    if (!IsAlive(Action.Source) || Action.Sequence == 0 || !FMath::IsFinite(Begin) || !FMath::IsFinite(End) || Begin < 0 || Begin >= End) return false;
    if (Windows.ContainsByPredicate([&](const FWindow& W) { return W.Action == Action; })) return false;
    Windows.Add({Action,Begin,End});
    return true;
}
bool FResolveLedger::ResolveHit(const FHitCandidate& C)
{
    if (!FMath::IsFinite(C.TimestampSeconds) || C.HurtboxId == 0 || !C.bGeometryValid || !C.bUnobstructed
        || C.Id.Action.Source.Pawn == C.Id.Target.Pawn || !IsAlive(C.Id.Action.Source) || !IsAlive(C.Id.Target)) return false;
    const FWindow* Window = Windows.FindByPredicate([&](const FWindow& W) { return W.Action == C.Id.Action; });
    if (!Window || C.TimestampSeconds < Window->Begin || C.TimestampSeconds >= Window->End || Resolved.Contains(C.Id)) return false;
    Resolved.Add(C.Id); // Only valid resolution consumes per-target dedup.
    return true;
}
bool FResolveLedger::MarkDead(FLifeId Life)
{
    for (FSubject& S : Subjects)
        if (S.Life == Life && S.bAlive) { S.bAlive = false; return true; }
    return false;
}
bool FResolveLedger::InvalidateAction(FActionId Action, double At)
{
    if (!FMath::IsFinite(At)) return false;
    for (FWindow& W : Windows)
        if (W.Action == Action) { W.End = FMath::Min(W.End,At); return true; }
    return false;
}
}
