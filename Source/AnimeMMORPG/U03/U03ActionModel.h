#pragma once
#include "CoreMinimal.h"
#include "U02/U02ActionModel.h"

// A0 only: no UObject, input, clock, world or runtime binding.
namespace AnimeMMORPG::U03
{
enum class EAction : uint8 { Attack1, Attack2, Attack3, Q, E, Monster };
enum class ECommand : uint8 { Escape, Dodge, Guard, Feint, Q, E, Attack, Jump, Target };
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
    double ReadyAt(EAction Id) const { return Ready[static_cast<uint8>(Id)]; }
    bool Spend(const FActionDefinition& D, double T);
private:
    double Value=100, Last=0, RegenStart=0; double Ready[6] = {};
};
class FTimelineModel;
// NextEvent discovers the earliest unresolved world event before the proposed structural boundary.
// ResolveInterval is strictly before that event; ResolveEvent runs at the committed clock BEFORE
// endpoint sampling, expiry, successor creation, or command admission. Consume events on delivery.
// NextEvent must return the next stable-ordered event; Advance drains ALL events at Now, even at T.
class ITimelineResolver
{
public:
    virtual ~ITimelineResolver() = default;
    virtual TOptional<double> NextEvent(const FTimelineModel& Model, double Through) = 0;
    virtual void ResolveInterval(const FActiveInterval& Interval) = 0;
    virtual void ResolveEvent(FTimelineModel& Model, double At) = 0;
};
class FTimelineModel
{
public:
    explicit FTimelineModel(U02::FLifeId InLife, double StartClock = 0) : Life(InLife), Now(StartClock) {}
    bool Advance(double T, ITimelineResolver& Resolver);
    TArray<FAdmissionResult> SubmitBatch(TArray<FCombatIntent> Batch, const FAdmissionContext& Context, ITimelineResolver& Resolver);
    // Only at the current resolver event; never advances or rewinds the clock.
    bool CancelCurrent(ECutoff Reason, bool bReplacementValid = true);
    bool SetGroundedCurrent(bool bGrounded); // Resolver-only authority event, not command permission.
    double Time() const { return Now; }
    U02::FLifeId GetLife() const { return Life; }
    uint64 CommandWatermark() const { return Watermark; }
    const TOptional<FCombatIntent>& GetPending() const { return Pending; }
    bool UpdateAim(double T, double Yaw);
    bool ResetLife(U02::FLifeId NewLife, double T);
    bool SpendResourceFixture(EAction Skill) { return !bBarrierOpen && !bAdvancing && (Skill==EAction::Q||Skill==EAction::E) && Resource.Spend(Definition(Skill),Now); }
    // Cooperative world barrier: arrive ALL subjects, resolve the sorted world group,
    // then finish ALL subjects. No subject may transition/admit while another is behind.
    double NextBoundaryThrough(double T) const;
    bool ArriveAtBarrier(double T, ITimelineResolver& Collector);
    bool CancelAtBarrier(ECutoff Reason);
    bool GroundedAtBarrier(bool Grounded);
    bool FinishBarrier(ITimelineResolver& Collector);
    // Explicitly event-free helpers for definition/admission tests, NOT world adapter APIs.
    bool AdvanceUnopposed(double T, TArray<FActiveInterval>& Out);
    TArray<FAdmissionResult> SubmitBatchUnopposed(TArray<FCombatIntent> Batch, const FAdmissionContext& Context, TArray<FActiveInterval>& Out);
    bool CancelUnopposed(ECutoff Reason, double T, bool bReplacementValid, TArray<FActiveInterval>& Out);
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
    bool bDead = false, bGrounded = true, bResolvingEvent = false, bAdvancing = false, bBarrierOpen = false;
    void DeliverBefore(double Stop, ITimelineResolver& Collector);
    void CompleteCurrent(ITimelineResolver& Collector);
};
}
