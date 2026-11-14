#pragma once
#include "CoreMinimal.h"
namespace AnimeMMORPG::U03
{
inline bool WithinTargetSelectionRange(double SquaredDistanceCm) {return SquaredDistanceCm<=2000.*2000.;}
struct FTargetRank
{
    double ScreenDistance=0,WorldDistance=0;
    FString Subject;
    bool operator<(const FTargetRank& B) const
    {return ScreenDistance!=B.ScreenDistance?ScreenDistance<B.ScreenDistance:WorldDistance!=B.WorldDistance?WorldDistance<B.WorldDistance:Subject<B.Subject;}
};
struct FTargetRetention
{
    TOptional<double> OccludedSince;
    bool Update(double Now,double Distance,bool Alive,bool SameLife,bool Clear)
    {
        if(!Alive||!SameLife||Distance>3000)return false;
        if(Clear)OccludedSince.Reset();else if(!OccludedSince.IsSet())OccludedSince=Now;
        return !OccludedSince.IsSet()||Now<OccludedSince.GetValue()+1.;
    }
};
}
