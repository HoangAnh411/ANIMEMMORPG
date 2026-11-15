#pragma once
#include "CoreMinimal.h"

namespace AnimeMMORPG::U03
{
// Absolute server-time window. Rendering this sample never rearms it.
inline double FeedbackRemaining(double EventTime,double ServerNow)
{
    if(!FMath::IsFinite(EventTime)||!FMath::IsFinite(ServerNow)||ServerNow<EventTime)return 0;
    return FMath::Max(0.,EventTime+1.2-ServerNow);
}
inline bool RecentHitVisible(double EventTime,double ServerNow,bool SameIdentity,bool OnScreen,bool Clear)
{return SameIdentity&&OnScreen&&Clear&&FeedbackRemaining(EventTime,ServerNow)>0;}
}
