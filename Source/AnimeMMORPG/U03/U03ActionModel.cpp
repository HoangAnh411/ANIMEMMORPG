#include "U03ActionModel.h"
namespace AnimeMMORPG::U03
{
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
    if(Reason==ECutoff::Dodge||Reason==ECutoff::Guard||Reason==ECutoff::Interrupt)
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
    if (!FMath::IsFinite(T) || T < Now || bAdvancing) return false;
    TGuardValue<bool> Advancing(bAdvancing, true);
    bool First = true;
    while (First || Now < T)
    {
        First = false;
        double Boundary = T;
        auto Split = [&](double At) { if (At > Now) Boundary = FMath::Min(Boundary, At); };
        if (Action)
        {
            const auto& D = Action->GetDefinition();
            Split(Action->Start + D.ActiveStart);
            Split(Action->Start + D.ActiveEnd);
            Split(Action->End());
        }
        if (Pending.IsSet()) Split(Pending->Receive + .15);
        if (!Action) Split(GraceEnd);
        const TOptional<double> Event = Resolver.NextEvent(*this, Boundary);
        if (Event.IsSet() && (!FMath::IsFinite(Event.GetValue()) || Event.GetValue() < Now || Event.GetValue() > Boundary)) return false;
        const double Stop = Event.IsSet() ? Event.GetValue() : Boundary;
        if (Action && Stop > Now)
        {
            const auto& D = Action->GetDefinition();
            const double Begin = FMath::Max(Now, Action->Start + D.ActiveStart);
            const double End = FMath::Min(Stop, FMath::Min(Action->Start + D.ActiveEnd, Action->Cutoff));
            if (Begin < End)
                Resolver.ResolveInterval({Action->Identity,D.Id,D.RawDamage,Begin,End,Action->Yaw,true});
        }
        Resource.Advance(Stop);
        Now = Stop;
        if (Event.IsSet())
        {
            TGuardValue<bool> Resolving(bResolvingEvent, true);
            Resolver.ResolveEvent(*this, Now);
        }
        // Only now can an endpoint contact exist: cancellation at this timestamp excludes it.
        if (Action)
        {
            const auto& D = Action->GetDefinition();
            if (Now >= Action->Start + D.ActiveStart && Now < Action->Start + D.ActiveEnd && Now < Action->Cutoff)
                Resolver.ResolveInterval({Action->Identity,D.Id,D.RawDamage,Now,Now,Action->Yaw,false});
            const bool Cancelled = Now >= Action->Cutoff;
            if (Cancelled || Now >= Action->End())
            {
                const bool Natural = !Cancelled;
                const double End = Natural ? Action->End() : Action->Cutoff;
                GraceEnd = Natural && D.Id <= EAction::Attack3 ? End + .15 : 0;
                Action.Reset();
                if (Natural && Pending.IsSet() && Pending->Receive + .15 > End)
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
    return true;
}
bool FTimelineModel::CancelCurrent(ECutoff Reason, bool Valid)
{
    if (!bResolvingEvent) return false;
    if (Reason == ECutoff::Death)
    {
        bDead = true;
        Pending.Reset(); NextCombo = EAction::Attack1; GraceEnd = 0;
    }
    if (!Action || !Action->Cancel(Reason, Now, Valid)) return Reason == ECutoff::Death;
    Pending.Reset();
    NextCombo = EAction::Attack1;
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
    if(bDead||!C.bPlaying||!C.bGrounded||C.bHardCC||C.bGuard||C.bDodging||C.bFeint||C.bDead) return EAdmission::Locked;
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
    Resource.Spend(Definition(Id),Now); Pending.Reset();Start(Id,Now,I.AimYaw); return EAdmission::Accepted;
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
            if(!ValidTime||!FMath::IsFinite(I.AimYaw)||!(I.Life==Life)||I.Sequence==0||I.Sequence<=Watermark)
                Results.Add({I.Sequence,ValidTime&&I.Life==Life&&I.Sequence<=Watermark?EAdmission::Stale:EAdmission::Invalid,0});
            else {Watermark=I.Sequence;Group.Add(I);}
        }
        Group.Sort([](const auto& A,const auto& B){return A.Command!=B.Command?A.Command<B.Command:A.Sequence<B.Sequence;});
        for(const auto& I:Group) Results.Add({I.Sequence,Admit(I,C),Action?Action->Identity.Sequence:0});
    }
    return Results;
}
}
