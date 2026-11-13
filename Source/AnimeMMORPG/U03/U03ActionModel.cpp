#include "U03ActionModel.h"
namespace AnimeMMORPG::U03
{
void FDodgeState::Recharge(double T)
{
    while(Charges<2 && T>=RestoreAt){++Charges;RestoreAt=Charges<2?RestoreAt+2.:0.;}
}
EAdmission FTimelineModel::AdmitDodge(const FCombatIntent& I)
{
    if(DodgeState.Charges==0)return EAdmission::Resource;
    if(Action && !Action->Startup(Now))return EAdmission::Busy;
    if(Now<DodgeState.NextStart)
    {
        const bool Replaced=PendingDodge.IsSet();PendingDodge=I;
        return Replaced?EAdmission::Replaced:EAdmission::Queued;
    }
    // All replacement conditions are validated before mutating an existing attack.
    if(Action){Action->Cancel(ECutoff::Dodge,Now,true);Action.Reset();}
    Pending.Reset();PendingDodge.Reset();GraceEnd=0;NextCombo=EAction::Attack1;
    const FVector2D Local=I.Direction.GetSafeNormal();
    const FRotator Aim(0,I.AimYaw,0);
    DodgeState.Direction=Local.IsNearlyZero()?-Aim.Vector():Aim.RotateVector(FVector(Local.X,Local.Y,0));
    ++DodgeState.Sequence;DodgeState.Start=Now;DodgeState.MotionEnd=Now+.25;DodgeState.LockEnd=Now+.35;DodgeState.NextStart=Now+.60;
    if(DodgeState.Charges==2)DodgeState.RestoreAt=Now+2.;
    --DodgeState.Charges;return EAdmission::Accepted;
}
const FActionDefinition& Definition(EAction Id)
{
    static const FActionDefinition Table[] = {
        {EAction::Attack1,1,.16,.22,.40,60,0,0},
        {EAction::Attack2,1,.18,.25,.45,70,0,0},
        {EAction::Attack3,1,.26,.36,.60,90,0,0},
        {EAction::Q,1,.30,.40,.80,100,20,4},
        {EAction::E,1,.25,.35,.75,80,25,6,FVector(100,60,90),FVector(100,0,90),true,true,true},
        {EAction::Monster,1,.60,.75,1.50,100,0,0}};
    check(static_cast<uint8>(Id)<UE_ARRAY_COUNT(Table));
    return Table[static_cast<uint8>(Id)];
}
FActionInstance::FActionInstance(EAction Id,U02::FActionId InIdentity,double InStart,double InYaw)
    : Identity(InIdentity),Start(InStart),Yaw(InYaw),Rules(Definition(Id)) {}
bool FActionInstance::Cancel(ECutoff Reason,double T,bool Valid)
{
    if(!FMath::IsFinite(T)||T<Start||T>=End()||T>=Cutoff) return false;
    if(Reason==ECutoff::Feint && Rules.Id!=EAction::Q)return false;
    if(Reason==ECutoff::Dodge||Reason==ECutoff::Guard||Reason==ECutoff::Interrupt||Reason==ECutoff::Feint)
        if(!Valid||!Startup(T)) return false;
    Cutoff=T; return true;
}
bool FResourceModel::Advance(double T)
{
    if(!FMath::IsFinite(T)||T<Last) return false;
    Value=FMath::Min(100.,Value+10.*FMath::Max(0.,T-FMath::Max(Last,RegenStart)));
    Last=T; return true;
}
EAdmission FResourceModel::CanSpend(const FActionDefinition& D,double T) const
{
    if(T<Ready[static_cast<uint8>(D.Id)]) return EAdmission::Cooldown;
    return Value<D.Cost?EAdmission::Resource:EAdmission::Accepted;
}
bool FResourceModel::Spend(const FActionDefinition& D,double T)
{
    if(!Advance(T)||CanSpend(D,T)!=EAdmission::Accepted) return false;
    if(D.Cost>0){Value-=D.Cost;RegenStart=T+1.;}
    Ready[static_cast<uint8>(D.Id)]=T+D.Cooldown; return true;
}
void FTimelineModel::Start(EAction Id,double T,double Yaw)
{
    Action=MakeUnique<FActionInstance>(Id,U02::FActionId{Life,++Next},T,FRotator::NormalizeAxis(Yaw));
    if(Id<=EAction::Attack3) NextCombo=Id==EAction::Attack3?EAction::Attack1:static_cast<EAction>(static_cast<uint8>(Id)+1);
    else NextCombo=EAction::Attack1;
}
bool FTimelineModel::Advance(double T, ITimelineResolver& Resolver)
{
    if (!FMath::IsFinite(T) || T < Now || bAdvancing || bBarrierOpen) return false;
    TGuardValue<bool> Advancing(bAdvancing, true);
    bool First = true;
    while (First || Now < T)
    {
        First = false;
        double Boundary = NextBoundaryThrough(T);
        const TOptional<double> Event = Resolver.NextEvent(*this, Boundary);
        if (Event.IsSet() && (!FMath::IsFinite(Event.GetValue()) || Event.GetValue() < Now || Event.GetValue() > Boundary)) return false;
        const double Stop = Event.IsSet() ? Event.GetValue() : Boundary;
        DeliverBefore(Stop, Resolver);
        // Drain the complete timestamp group, including events discovered by a callback.
        // Even at T, nothing may sample, expire, create a successor or admit between events.
        TOptional<double> CurrentEvent = Event;
        while (CurrentEvent.IsSet())
        {
            {
                TGuardValue<bool> Resolving(bResolvingEvent, true);
                Resolver.ResolveEvent(*this, Now);
            }
            CurrentEvent = Resolver.NextEvent(*this, Now);
            if (CurrentEvent.IsSet() && (!FMath::IsFinite(CurrentEvent.GetValue()) || CurrentEvent.GetValue() != Now)) return false;
        }
        CompleteCurrent(Resolver);
    }
    return true;
}

void FTimelineModel::CompleteCurrent(ITimelineResolver& Resolver)
{
    if(PendingDodge.IsSet() && Now>=PendingDodge->Receive+.15)PendingDodge.Reset();
    if(PendingDodge.IsSet() && Now>=DodgeState.NextStart && bGrounded && !bDead && !DefenseState.Locked(Now) && !DefenseState.bGuard)
    {const auto I=PendingDodge.GetValue();PendingDodge.Reset();AdmitDodge(I);}
    // Only now can an endpoint contact exist: cancellation at this timestamp excludes it.
    if (Action)
    {
        const auto& D = Action->GetDefinition();
        if (Now >= Action->Start + D.ActiveStart && Now < Action->Start + D.ActiveEnd && Now < Action->Cutoff)
            Resolver.ResolveInterval({Action->Identity,D.Id,D.RawDamage,Now,Now,Action->Yaw,false,D.bBlockable,D.bParryable,D.bInterrupt,D.Version});
        const bool Cancelled = Now >= Action->Cutoff;
        if (Cancelled || Now >= Action->End())
        {
            const bool Natural = !Cancelled;
            const double End = Natural ? Action->End() : Action->Cutoff;
            GraceEnd = Natural && bGrounded && !bDead && D.Id <= EAction::Attack3 ? End + .15 : 0;
            Action.Reset();
            if (Natural && bGrounded && !bDead && Pending.IsSet() && Pending->Receive + .15 > End)
            {
                const double Yaw = Pending->AimYaw;
                Pending.Reset();
                Start(NextCombo, End, Yaw);
            }
            else Pending.Reset();
        }
    }
    if (Pending.IsSet() && Now >= Pending->Receive + .15) Pending.Reset();
    if (!Action && Now >= GraceEnd) NextCombo = EAction::Attack1;
}
void FTimelineModel::DeliverBefore(double Stop, ITimelineResolver& Resolver)
{
    if (Action && Stop > Now)
    {
        const auto& D = Action->GetDefinition();
        const double Begin = FMath::Max(Now, Action->Start + D.ActiveStart);
        const double End = FMath::Min(Stop, FMath::Min(Action->Start + D.ActiveEnd, Action->Cutoff));
        if (Begin < End)
            Resolver.ResolveInterval({Action->Identity,D.Id,D.RawDamage,Begin,End,Action->Yaw,true,D.bBlockable,D.bParryable,D.bInterrupt,D.Version});
    }
    Resource.Advance(Stop);
    DefenseState.Advance(Stop);
    DodgeState.Recharge(Stop);
    Now = Stop;
}
double FTimelineModel::NextBoundaryThrough(double T) const
{
    double Boundary = DefenseState.Boundary(Now,T);
    auto Split = [&](double At) { if (At > Now) Boundary = FMath::Min(Boundary, At); };
    if (Action) { const auto& D=Action->GetDefinition(); Split(Action->Start+D.ActiveStart); Split(Action->Start+D.ActiveEnd); Split(Action->End()); }
    if (Pending.IsSet()) Split(Pending->Receive+.15);
    if (!Action) Split(GraceEnd);
    Split(FeintState.LockEnd);
    Split(DodgeState.MotionEnd);Split(DodgeState.LockEnd);Split(DodgeState.NextStart);
    if(DodgeState.Charges<2)Split(DodgeState.RestoreAt);
    if(PendingDodge.IsSet())Split(PendingDodge->Receive+.15);
    return Boundary;
}
bool FTimelineModel::ArriveAtBarrier(double T, ITimelineResolver& Collector)
{
    if (bAdvancing || bBarrierOpen || !FMath::IsFinite(T) || T<Now || NextBoundaryThrough(T)!=T) return false;
    DeliverBefore(T,Collector); bBarrierOpen=true; return true;
}
bool FTimelineModel::CancelAtBarrier(ECutoff Reason)
{ if(!bBarrierOpen)return false; TGuardValue<bool> Resolving(bResolvingEvent,true); return CancelCurrent(Reason); }
bool FTimelineModel::GroundedAtBarrier(bool Grounded)
{ if(!bBarrierOpen)return false; TGuardValue<bool> Resolving(bResolvingEvent,true); return SetGroundedCurrent(Grounded); }
bool FTimelineModel::FinishBarrier(ITimelineResolver& Collector)
{ if(!bBarrierOpen)return false; CompleteCurrent(Collector); bBarrierOpen=false; return true; }
bool FTimelineModel::UpdateAim(double T,double Yaw)
{ if(bBarrierOpen||bAdvancing||!FMath::IsFinite(Yaw)||T!=Now)return false;
  if(DefenseState.bGuard){DefenseState.Yaw=FRotator::NormalizeAxis(Yaw);return true;}
  if(!Action||!Action->Startup(T))return false; Action->Yaw=FRotator::NormalizeAxis(Yaw); return true; }
bool FTimelineModel::ResetLife(U02::FLifeId NewLife,double T)
{
    if(bBarrierOpen||bAdvancing||T<Now||NewLife.Pawn!=Life.Pawn||NewLife.Generation<=Life.Generation)return false;
    Life=NewLife;Now=T;Action.Reset();Pending.Reset();NextCombo=EAction::Attack1;GraceEnd=0;
    bDead=false;bGrounded=true;FeintState=FFeintState();Resource=FResourceModel();DefenseState=FDefenseState();DefenseState.Last=T;DefenseState.FreeSince=T;DodgeState=FDodgeState();PendingDodge.Reset();Next=0;return true;
}
bool FTimelineModel::CancelCurrent(ECutoff Reason, bool Valid)
{
    if (!bResolvingEvent) return false;
    const bool Lifecycle = Reason == ECutoff::Death || Reason == ECutoff::LostGround || Reason == ECutoff::HardCC;
    if (Lifecycle)
    {
        if (Reason == ECutoff::Death){bDead = true;DefenseState.EndHard(Now);DefenseState.Slows.Empty();}
        else if(Reason==ECutoff::LostGround)bGrounded = false;
        DefenseState.DropGuard();
        // Lifecycle state and combo invalidation do not depend on an old action's window.
        Pending.Reset(); NextCombo = EAction::Attack1; GraceEnd = 0;
        PendingDodge.Reset();DodgeState.MotionEnd=FMath::Min(DodgeState.MotionEnd,Now);
        if(Reason==ECutoff::Death||Reason==ECutoff::HardCC)DodgeState.LockEnd=FMath::Min(DodgeState.LockEnd,Now);
    }
    if (!Action || !Action->Cancel(Reason, Now, Valid)) return Lifecycle;
    Pending.Reset();
    NextCombo = EAction::Attack1;
    return true;
}
bool FTimelineModel::SetGroundedCurrent(bool Grounded)
{
    if (!bResolvingEvent) return false;
    if (!Grounded) return CancelCurrent(ECutoff::LostGround);
    bGrounded = true; // Explicit authority landing event; never inferred from admission context.
    return true;
}
namespace
{
class FUnopposedCollector final : public ITimelineResolver
{
public:
    explicit FUnopposedCollector(TArray<FActiveInterval>& InOut) : Out(InOut) {}
    TArray<FActiveInterval>& Out;
    TOptional<double> CancelAt;
    ECutoff Reason = ECutoff::Death;
    bool Valid = true, Accepted = false;
    TOptional<double> NextEvent(const FTimelineModel&, double Through) override
    { return CancelAt.IsSet() && CancelAt.GetValue() <= Through ? CancelAt : TOptional<double>(); }
    void ResolveInterval(const FActiveInterval& I) override { Out.Add(I); }
    void ResolveEvent(FTimelineModel& M, double) override
    { CancelAt.Reset(); Accepted = M.CancelCurrent(Reason, Valid); }
};
}
bool FTimelineModel::AdvanceUnopposed(double T, TArray<FActiveInterval>& Out)
{ FUnopposedCollector Collector(Out); return Advance(T, Collector); }
TArray<FAdmissionResult> FTimelineModel::SubmitBatchUnopposed(TArray<FCombatIntent> Batch, const FAdmissionContext& C, TArray<FActiveInterval>& Out)
{ FUnopposedCollector Collector(Out); return SubmitBatch(MoveTemp(Batch), C, Collector); }
bool FTimelineModel::CancelUnopposed(ECutoff Reason, double T, bool Valid, TArray<FActiveInterval>& Out)
{
    if (!FMath::IsFinite(T) || T < Now) return false;
    FUnopposedCollector Collector(Out);
    Collector.CancelAt = T; Collector.Reason = Reason; Collector.Valid = Valid;
    return Advance(T, Collector) && Collector.Accepted;
}
EAdmission FTimelineModel::Admit(const FCombatIntent& I,const FAdmissionContext& C)
{
    if(C.bDefenseEnabled && I.Command==ECommand::GuardRelease){DefenseState.ReleaseGuard();return EAdmission::Accepted;}
    if(C.bDefenseEnabled && I.Command==ECommand::Escape)
    {
        if(bDead||!C.bPlaying||C.bDead)return EAdmission::Locked;
        if(!DefenseState.Locked(Now))return EAdmission::Locked;
        if(Now<DefenseState.XReadyAt)return EAdmission::Cooldown;
        DefenseState.Escape(Now);ClearPending();return EAdmission::Accepted;
    }
    if(C.bDefenseEnabled && I.Command==ECommand::Guard)
    {
        const bool Valid=!bDead&&bGrounded&&C.bPlaying&&C.bGrounded&&!C.bHardCC&&!C.bDead&&!C.bFeint&&!C.bDodging
            &&!FeintState.Locked(Now)&&!DodgeState.Locked(Now)&&!DefenseState.Locked(Now)&&(!Action||Action->Startup(Now));
        if(!DefenseState.PressGuard(Now,I.AimYaw,Valid))return EAdmission::Locked;
        if(Action){Action->Cancel(ECutoff::Guard,Now);Action.Reset();}
        ClearPending();GraceEnd=0;NextCombo=EAction::Attack1;return EAdmission::Accepted;
    }
    if(FeintState.Locked(Now)||DefenseState.bGuard||DefenseState.Locked(Now))return EAdmission::Locked;
    if(bDead||!bGrounded||!C.bPlaying||!C.bGrounded||C.bHardCC||C.bGuard||C.bDodging||C.bFeint||C.bDead) return EAdmission::Locked;
    if(I.Command==ECommand::Dodge && C.bDodgeEnabled)return AdmitDodge(I);
    if(DodgeState.Locked(Now))return EAdmission::Locked;
    if(IsFeintRequest(I.Command))
    {
        if(Now<FeintState.LastSuccess+1.)return EAdmission::Cooldown;
        FeintState.ActionSequence=Action->Identity.Sequence;
        if(!Action->Cancel(ECutoff::Feint,Now))return EAdmission::Busy;
        Action.Reset();ClearPending();GraceEnd=0;NextCombo=EAction::Attack1;
        FeintState.LastSuccess=Now;FeintState.LockEnd=Now+.20;++FeintState.Sequence;
        return EAdmission::Accepted;
    }
    if(I.Command!=ECommand::Attack&&I.Command!=ECommand::Q&&I.Command!=ECommand::E) return EAdmission::Unsupported;
    if(I.Command==ECommand::Attack)
    {
        if(Action)
        {
            if(Action->GetDefinition().Id>EAction::Attack3) return EAdmission::Busy;
            const bool Replaced=Pending.IsSet(); Pending=I;
            return Replaced?EAdmission::Replaced:EAdmission::Queued;
        }
        Start(NextCombo,Now,I.AimYaw);return EAdmission::Accepted;
    }
    if(Action&&(Action->GetDefinition().Id>EAction::Attack3||Now<Action->Start+Action->GetDefinition().ActiveEnd)) return EAdmission::Busy;
    const EAction Id=I.Command==ECommand::Q?EAction::Q:EAction::E;
    const EAdmission Can=Resource.CanSpend(Definition(Id),Now);
    if(Can!=EAdmission::Accepted) return Can;
    Resource.Spend(Definition(Id),Now); ClearPending();GraceEnd=0;Start(Id,Now,I.AimYaw); return EAdmission::Accepted;
}
TArray<FAdmissionResult> FTimelineModel::SubmitBatch(TArray<FCombatIntent> Batch,const FAdmissionContext& C,ITimelineResolver& Resolver)
{
    TArray<FAdmissionResult> Results;
    // Remove non-finite keys before sorting: NaN is not a strict weak ordering.
    Batch.RemoveAll([&](const FCombatIntent& I){
        if(FMath::IsFinite(I.Receive)) return false;
        Results.Add({I.Sequence,EAdmission::Invalid,0});return true;
    });
    // A replay sequence with conflicting payload at the same receive timestamp is malformed.
    // Reject every conflicting copy instead of letting collection order choose gameplay.
    TArray<uint64> Conflicts;
    for(int32 A=0;A<Batch.Num();++A) for(int32 B=A+1;B<Batch.Num();++B)
        if(Batch[A].Sequence==Batch[B].Sequence && Batch[A].Receive==Batch[B].Receive
            && (Batch[A].Command!=Batch[B].Command || Batch[A].AimYaw!=Batch[B].AimYaw
                || !(Batch[A].Life==Batch[B].Life) || Batch[A].Direction!=Batch[B].Direction))
            Conflicts.AddUnique(Batch[A].Sequence);
    Batch.RemoveAll([&](const FCombatIntent& I){
        if(!Conflicts.Contains(I.Sequence)) return false;
        Results.Add({I.Sequence,EAdmission::Invalid,0});return true;
    });
    Batch.Sort([](const auto& A,const auto& B){if(A.Receive!=B.Receive)return A.Receive<B.Receive;return A.Sequence<B.Sequence;});
    int32 Index=0;
    while(Index<Batch.Num())
    {
        const double T=Batch[Index].Receive; TArray<FCombatIntent> Group;
        int32 End=Index+1;while(End<Batch.Num()&&Batch[End].Receive==T)++End;
        const bool ValidTime=FMath::IsFinite(T)&&T>=Now;
        if(ValidTime && !Advance(T,Resolver)) return Results;
        // Sequence validation precedes priority sorting so a higher-priority later sequence cannot erase an earlier command.
        for(;Index<End;++Index)
        {
            const auto& I=Batch[Index];
            if(!ValidTime||!FMath::IsFinite(I.AimYaw)||!FMath::IsFinite(I.Direction.X)||!FMath::IsFinite(I.Direction.Y)||!(I.Life==Life)||I.Sequence==0||I.Sequence<=Watermark)
                Results.Add({I.Sequence,ValidTime&&I.Life==Life&&I.Sequence<=Watermark?EAdmission::Stale:EAdmission::Invalid,0});
            else {Watermark=I.Sequence;Group.Add(I);}
        }
        Group.Sort([this](const auto& A,const auto& B){
            const auto Priority=[this](ECommand Command){return Command==ECommand::GuardRelease?-1:IsFeintRequest(Command)?int32(ECommand::Feint):int32(Command);};
            const int32 AP=Priority(A.Command), BP=Priority(B.Command);
            return AP!=BP?AP<BP:A.Sequence<B.Sequence;});
        for(const auto& I:Group) Results.Add({I.Sequence,Admit(I,C),Action?Action->Identity.Sequence:0});
    }
    return Results;
}
EDefense FTimelineModel::DefendAtBarrier(FVector ToSource,FVector Direction,bool Blockable,bool Parryable)
{
    check(bBarrierOpen);
    const auto R=DefenseState.Defend(Now,ToSource,Direction,Blockable,Parryable);
    if(DefenseState.Locked(Now))CancelAtBarrier(ECutoff::HardCC);
    return R;
}
bool FTimelineModel::HardAtBarrier(EHardCC Kind,double Duration)
{
    if(!bBarrierOpen||bDead||!DefenseState.ApplyHard(Kind,Duration,Now))return false;
    CancelAtBarrier(ECutoff::HardCC);return true;
}
bool FTimelineModel::SlowAtBarrier(double Fraction,double Duration)
{
    if(!bBarrierOpen||bDead||!FMath::IsFinite(Fraction)||Fraction<=0||Fraction>1||!FMath::IsFinite(Duration)||Duration<=0)return false;
    DefenseState.Slows.Add({Fraction,Now+Duration});return true;
}
}
