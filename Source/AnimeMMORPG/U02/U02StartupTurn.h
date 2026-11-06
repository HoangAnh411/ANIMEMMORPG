#pragma once
#include "CoreMinimal.h"

namespace AnimeMMORPG::U02
{
// Action-local, simulation-time trajectory. Exactly opposite headings always turn positive.
struct FStartupTurn
{
    double FromYaw = 0, TargetYaw = 0, SegmentStart = 0, ActiveStart = 0;
    static double Delta(double From, double To)
    {
        double D = FMath::Fmod(To-From,360.);
        if(D< -180.) D+=360.;
        if(D>=180.) D-=360.;
        return D == -180. ? 180. : D;
    }
    double Sample(double Now) const
    {
        if(Now>=ActiveStart) return FRotator::NormalizeAxis(TargetYaw);
        const double A=ActiveStart>SegmentStart ? FMath::Clamp((Now-SegmentStart)/(ActiveStart-SegmentStart),0.,1.) : 1.;
        return FRotator::NormalizeAxis(FromYaw+Delta(FromYaw,TargetYaw)*A*A*(3.-2.*A));
    }
    void Begin(double Body, double Aim, double Start, double Deadline)
    { FromYaw=Body;TargetYaw=Aim;SegmentStart=Start;ActiveStart=Deadline; }
    void Retarget(double Now, double Aim)
    {
        if(Now>=ActiveStart || Delta(TargetYaw,Aim)==0.)return;
        FromYaw=Sample(Now);SegmentStart=Now;TargetYaw=Aim;
    }
};
}
