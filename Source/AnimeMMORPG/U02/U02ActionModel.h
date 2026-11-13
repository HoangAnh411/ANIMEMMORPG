#pragma once

#include "CoreMinimal.h"

// U02-A: value types only. No actor, input binding, collision query or replication.
namespace AnimeMMORPG::U02
{
enum class EPhase : uint8 { Idle, Startup, Active, Recovery, Finished, Cancelled };
enum class EReject : uint8 { None, InvalidTime, InvalidAim, StaleCommand, NotPlaying, Airborne, Interacting, Defeated, Busy };
enum class ECancel : uint8 { Dodge, Guard, LostGround, Death, Reset, Removed, Menu, Focus };

struct FAttack1Definition
{
    double ActiveStartSeconds = .16, ActiveEndSeconds = .22, DurationSeconds = .40;
    int32 RawDamage = 60;
    FVector HalfExtentsCm = FVector(100, 60, 90);
    FVector CenterFromFeetCm = FVector(100, 0, 90);
    bool IsValid() const;
};

// FGuid word order is explicit; never sort by memory bytes, pointers or actor names.
bool PawnLess(const FGuid& A, const FGuid& B);
struct FLifeId
{
    FGuid Pawn;
    uint64 Generation = 1;
    bool operator==(const FLifeId& Other) const { return Pawn == Other.Pawn && Generation == Other.Generation; }
};
struct FActionId
{
    FLifeId Source;
    uint64 Sequence = 0;
    bool operator==(const FActionId& Other) const { return Source == Other.Source && Sequence == Other.Sequence; }
};
struct FHitId
{
    FActionId Action;
    FLifeId Target;
    bool operator==(const FHitId& Other) const { return Action == Other.Action && Target == Other.Target; }
};
bool HitLess(const FHitId& A, const FHitId& B);

struct FAttackContext
{
    bool bPlaying = true, bGrounded = true, bInteracting = false, bDefeated = false;
};

struct FActiveSlice
{
    bool bEvaluate = false;
    double BeginSeconds = 0, EndSeconds = 0;
    // Fractions of the original previous/current collision snapshot interval.
    double BeginAlpha = 0, EndAlpha = 0;
    // End is a sampling limit; candidate timestamp MUST remain < active deadline.
    bool bEndExclusive = false;
};

struct FCombatSnapshot
{
    FLifeId Life; // Reset/idle snapshots must identify the current life without an action.
    FActionId Action;
    EPhase Phase = EPhase::Idle;
    double StartSeconds = 0, ActiveStartSeconds = 0, ActiveEndSeconds = 0, EndSeconds = 0;
    double LastAdvanceSeconds = 0, AimYawDegrees = 0;
    bool bCombatLocked = false, bYawLocked = false;
};

class FActionModel
{
public:
    explicit FActionModel(FLifeId InLife) : Life(InLife) {}
    EReject SubmitAttackIntent(uint64 CommandSequence, double ServerNowSeconds, double AimYawDegrees, const FAttackContext& Context);
    bool AdvanceAction(double NowSeconds, FActiveSlice& OutSlice, bool bContinuousSnapshots = true);
    bool UpdateAim(double NowSeconds, double AimYawDegrees);
    bool CancelAction(ECancel Reason, double NowSeconds);
    bool ResetLabCombat(double NowSeconds); // Authority/lab authorization belongs to future adapter.
    FCombatSnapshot GetCombatSnapshot(double NowSeconds) const;
    EPhase PhaseAt(double NowSeconds) const;
    FLifeId GetLife() const { return Life; }
private:
    bool ValidNow(double Now) const;
    FLifeId Life;
    FActionId Action;
    uint64 LastCommandSequence = 0, NextActionSequence = 0;
    double Start = 0, LastAdvance = 0, LastObserved = 0, AimYaw = 0;
    bool bHasAction = false, bCancelled = false;
    FAttack1Definition Definition;
};

// Orthogonal policies: combat lock never writes the U01 physical release gate.
struct FMotorAuthority
{
    bool bControl = false, bInteracting = false, bDefeated = false, bCombat = false;
    bool BlocksMotor() const { return bControl || bInteracting || bDefeated || bCombat; }
    bool ArmsReleaseGate() const { return bControl || bInteracting || bDefeated; }
    bool KeepsGravity() const { return true; }
    static bool ReplayCombatLock(bool bAuthorityCombat, bool bSavedCombat) { return bAuthorityCombat || bSavedCombat; }
};

struct FHitCandidate
{
    FHitId Id;
    double TimestampSeconds = 0;
    uint32 HurtboxId = 0;
    bool bGeometryValid = true, bUnobstructed = true;
    uint8 DefinitionId = 0; uint32 DefinitionVersion = 1; int32 RawDamage = 60;
    FVector ToSource=FVector::ForwardVector, AttackDirection=FVector::ForwardVector;
    bool bBlockable=true,bParryable=true;
};
bool CandidateLess(const FHitCandidate& A, const FHitCandidate& B);

// Pure lifetime/dedup model. Caller sorts ALL world candidates before resolving,
// then applies vital state and MarkDead synchronously before the next candidate.
// No HP/damage/RNG here. One ledger per world/session; recreate on world change.
class FResolveLedger
{
public:
    bool RegisterLife(FLifeId Life);
    bool RegisterAction(FActionId Action, double ActiveStartSeconds, double ActiveEndSeconds);
    bool ResolveHit(const FHitCandidate& Candidate);
    bool CanResolveHit(const FHitCandidate& Candidate) const;
    bool MarkDead(FLifeId Life);
    bool InvalidateAction(FActionId Action, double AtSeconds);
    bool IsAlive(FLifeId Life) const;
private:
    struct FSubject { FLifeId Life; bool bAlive = true; };
    struct FWindow { FActionId Action; double Begin = 0, End = 0; };
    TArray<FSubject> Subjects;
    TArray<FWindow> Windows;
    TArray<FHitId> Resolved;
};
}
