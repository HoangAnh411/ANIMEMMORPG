#pragma once
#include "CoreMinimal.h"
#include "U02/U02ActionModel.h"

// A0 only: no UObject, input, clock, world or runtime binding.
namespace AnimeMMORPG::U03
{
enum class EAction : uint8 { Attack1, Attack2, Attack3, Q, E, Monster };
enum class ECommand : uint8 { Escape, Dodge, Guard, Feint, Q, E, Attack, Jump };
enum class EAdmission : uint8 { Accepted, Queued, Replaced, Stale, Invalid, Locked, Busy, Resource, Cooldown, Unsupported };
enum class ECutoff : uint8 { Dodge, Guard, Interrupt, Death, LostGround };
struct FActionDefinition
{
    EAction Id; uint32 Version; double ActiveStart, ActiveEnd, Duration; int32 RawDamage;
    double Cost, Cooldown;
    FVector HalfExtentsCm = FVector(100,60,90), CenterFromFeetCm = FVector(100,0,90);
    bool bBlockable = true, bParryable = true, bInterrupt = false;
};
const FActionDefinition& Definition(EAction Id);
class FActionInstance
{
public:
    FActionInstance(EAction Id, U02::FActionId Identity, double Start, double Yaw);
    const FActionDefinition& GetDefinition() const { return Rules; }
    U02::FActionId Identity; double Start, Yaw, Cutoff = TNumericLimits<double>::Max();
    double End() const { return Start + Rules.Duration; }
    bool Startup(double T) const { return T >= Start && T < Start + Rules.ActiveStart && T < Cutoff; }
    bool Cancel(ECutoff Reason, double T, bool bReplacementValid = true);
private:
    const FActionDefinition Rules; // captured value; never references a mutable registry
};
struct FCombatIntent
{
    uint64 Sequence = 0; U02::FLifeId Life; ECommand Command = ECommand::Attack;
    double Receive = 0, AimYaw = 0; FVector2D Direction = FVector2D::ZeroVector;
};
struct FAdmissionResult { uint64 Sequence; EAdmission Result; uint64 ActionSequence; };
struct FActiveInterval { U02::FActionId Identity; EAction DefinitionId; int32 RawDamage; double Begin, End; double Yaw; bool bEndExclusive = true; };
struct FAdmissionContext { bool bPlaying=true, bGrounded=true, bHardCC=false, bGuard=false, bDodging=false, bFeint=false, bDead=false; };
class FResourceModel
{
public:
    double Energy() const { return Value; }
    bool Advance(double T);
    EAdmission CanSpend(const FActionDefinition& D, double T) const;
    bool Spend(const FActionDefinition& D, double T);
private:
    double Value=100, Last=0, RegenStart=0; double Ready[6] = {};
};
class FTimelineModel
{
public:
    explicit FTimelineModel(U02::FLifeId InLife) : Life(InLife) {}
    bool Advance(double T, TArray<FActiveInterval>& Out);
    // Caller drains old geometry/results through T before admission; Out contains those intervals.
    TArray<FAdmissionResult> SubmitBatch(TArray<FCombatIntent> Batch, const FAdmissionContext& Context, TArray<FActiveInterval>& Out);
    bool Cancel(ECutoff Reason, double T, bool bReplacementValid, TArray<FActiveInterval>& Out);
    void ClearPending() { Pending.Reset(); }
    const FActionInstance* Current() const { return Action.Get(); }
    const FResourceModel& Resources() const { return Resource; }
private:
    void Start(EAction Id, double T, double Yaw);
    EAdmission Admit(const FCombatIntent& I, const FAdmissionContext& C);
    U02::FLifeId Life; uint64 Watermark=0, Next=0; double Now=0, GraceEnd=0;
    EAction NextCombo=EAction::Attack1;
    TUniquePtr<FActionInstance> Action; TOptional<FCombatIntent> Pending;
    FResourceModel Resource;
};
}
