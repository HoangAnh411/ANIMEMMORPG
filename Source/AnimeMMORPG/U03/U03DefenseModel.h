#pragma once
#include "CoreMinimal.h"

namespace AnimeMMORPG::U03
{
enum class EHardCC : uint8 { None, Stun, Knockdown, Launch, Grab, GuardBreak };
enum class EDefense : uint8 { Hit, Block, Parry };
struct FSlow
{
    double Fraction=0, End=0;
};
// Current authority state only. Call Advance before a mutation at the committed world time.
// The world barrier, rather than presentation history, supplies hit-time state.
struct FDefenseState
{
    bool bGuard=false, bGuardHeld=false, bParryOpen=false, bPendingLaunch=false;
    uint64 GuardSequence=0;
    double Yaw=0, Posture=100, ParryStart=0, ParryEnd=0, ParryReadyAt=0;
    EHardCC Hard=EHardCC::None;
    double HardEnd=0, LockedBudget=0, FreeSince=0, ImmuneEnd=0, XReadyAt=0;
    double Last=0, LastHit=-TNumericLimits<double>::Max();
    TArray<FSlow> Slows;
    bool Locked(double T) const { return Hard!=EHardCC::None && T<HardEnd; }
    double Slow(double T) const
    { double V=0; for(const auto& S:Slows)if(T<S.End)V=FMath::Max(V,S.Fraction); return V; }
    void DropGuard() { bGuard=false; bParryOpen=false; }
    void EndHard(double T)
    {
        if(Hard==EHardCC::GuardBreak)Posture=100;
        Hard=EHardCC::None;HardEnd=T;FreeSince=T;bPendingLaunch=false;
    }
    double Boundary(double Now,double Through) const
    {
        double V=Through;
        auto Split=[&](double T){if(T>Now)V=FMath::Min(V,T);};
        if(Locked(Now)){Split(HardEnd);Split(Now+FMath::Max(0.,2.-LockedBudget));}
        else if(LockedBudget>0)Split(FreeSince+.50);
        Split(ImmuneEnd);if(bParryOpen)Split(ParryEnd);
        for(const auto& S:Slows)Split(S.End);
        if(!bGuard && Posture<100){Split(LastHit+2.);if(Now>=LastHit+2.)Split(Now+(100.-Posture)/25.);}
        return V;
    }
    void Advance(double T)
    {
        check(T>=Last);
        // Integrate at every internal boundary, including long unopposed model updates.
        while(Last<T)
        {
            const double Stop=Boundary(Last,T);
            if(Locked(Last))LockedBudget=FMath::Min(2.,LockedBudget+Stop-Last);
            if(!bGuard && Hard!=EHardCC::GuardBreak)
                Posture=FMath::Min(100.,Posture+25.*FMath::Max(0.,Stop-FMath::Max(Last,LastHit+2.)));
            Last=Stop;
            if(Hard!=EHardCC::None && (Last>=HardEnd || LockedBudget>=2.))
            {const bool Limit=LockedBudget>=2.;EndHard(Last);if(Limit)ImmuneEnd=FMath::Max(ImmuneEnd,Last+2.);}
            if(Hard==EHardCC::None && Last>=FreeSince+.50)LockedBudget=0;
            if(Last>=ParryEnd)bParryOpen=false;
            Slows.RemoveAll([&](const FSlow& S){return Last>=S.End;});
        }
    }
    bool PressGuard(double T,double Aim,bool Valid)
    {
        if(bGuardHeld)return false;
        bGuardHeld=true;
        if(!Valid || Locked(T) || Posture<=0)return false;
        bGuard=true;++GuardSequence;Yaw=FRotator::NormalizeAxis(Aim);
        if(T>=ParryReadyAt){ParryStart=T;ParryEnd=T+.12;ParryReadyAt=T+.60;bParryOpen=true;}
        return true;
    }
    void ReleaseGuard() {DropGuard();bGuardHeld=false;}
    bool ApplyHard(EHardCC Kind,double Duration,double T)
    {
        if(Kind==EHardCC::None || !FMath::IsFinite(Duration) || Duration<=0 || T<ImmuneEnd)return false;
        if(Locked(T) && Duration<=HardEnd-T)return false;
        if(!Locked(T) && T>=FreeSince+.50)LockedBudget=0;
        // Replacing a guard break also exits its posture lifecycle.
        if(Hard==EHardCC::GuardBreak && Kind!=Hard)Posture=100;
        Hard=Kind;HardEnd=T+Duration;bPendingLaunch=Kind==EHardCC::Launch;DropGuard();return true;
    }
    bool Escape(double T)
    {
        if(!Locked(T)||T<XReadyAt)return false;
        EndHard(T);Slows.Empty();LockedBudget=0;ImmuneEnd=FMath::Max(ImmuneEnd,T+1.);XReadyAt=T+30.;return true;
    }
    EDefense Defend(double T,FVector ToSource,FVector AttackDirection,bool Blockable,bool Parryable)
    {
        LastHit=T;
        if(!bGuard || !Blockable)return EDefense::Hit;
        ToSource.Z=0;
        if(ToSource.IsNearlyZero()){ToSource=-AttackDirection;ToSource.Z=0;}
        if(ToSource.IsNearlyZero() || FVector::DotProduct(FRotator(0,Yaw,0).Vector(),ToSource.GetSafeNormal())<.5-1.e-12)return EDefense::Hit;
        if(Parryable && bParryOpen && T>=ParryStart && T<ParryEnd)
        {bParryOpen=false;return EDefense::Parry;}
        Posture=FMath::Max(0.,Posture-25.);
        if(Posture==0)
        {DropGuard();if(!ApplyHard(EHardCC::GuardBreak,.8,T))Posture=100;}
        return EDefense::Block;
    }
};
}
