#pragma once
#include "U02CombatComponent.h"

namespace AnimeMMORPG::U02
{
// Presentation clock only; never changes action/motor/collision state.
struct FPresentationSample
{
    bool bPlay=false;
    double PositionSeconds=0;
};
inline FPresentationSample SamplePresentation(const FU02RepCombatSnapshot& S,double ServerNow)
{
    FPresentationSample Out;
    if(!FMath::IsFinite(ServerNow)||!S.ActionSequence||!S.bLocked||S.Phase<uint8(EPhase::Startup)||S.Phase>uint8(EPhase::Recovery))return Out;
    const double Elapsed=ServerNow-S.StartSeconds;
    if(Elapsed<0||Elapsed>=.4)return Out;
    Out.bPlay=true;Out.PositionSeconds=Elapsed;return Out;
}
}
