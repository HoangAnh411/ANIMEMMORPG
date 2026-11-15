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
inline bool ConsumeFeedback(uint64 Serial,uint64& Watermark)
{if(!Serial||Serial<=Watermark)return false;Watermark=Serial;return true;}
inline bool FreshFeedbackAudio(bool New,bool Primed,bool Visible,double At,double Now)
{return New&&Primed&&Visible&&FeedbackRemaining(At,Now)>0&&Now-At<=.15;}
inline bool SameFeedbackScope(uint64 Life,uint64 ExpectedLife,FGuid Encounter,FGuid ExpectedEncounter,uint64 Revision,uint64 ExpectedRevision)
{return Life==ExpectedLife&&Encounter==ExpectedEncounter&&Revision==ExpectedRevision;}
}
