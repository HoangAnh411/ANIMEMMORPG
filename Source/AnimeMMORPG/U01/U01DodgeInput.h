#pragma once
#include "U01ControlPolicy.h"
#include "U01Settings.h"

namespace AnimeMMORPG::U01
{
// Only controller-observed edges participate. Never consult OS/Enhanced Input
// state here: either can include an edge not yet dispatched to this controller.
inline bool IsNewObservedPress(const TSet<FKey>& Observed, FKey Key, bool bDown)
{ return bDown && !Observed.Contains(Key); }

inline FVector2D ObservedDodgeDirection(const TSet<FKey>& Observed,
    const FReleaseGate& Gate, const FPreferences& Preferences)
{
    const auto Held = [&](EControl Action)
    {
        if (!Preferences.Keys.IsValidIndex(Action)) return false;
        for (const FKey Physical : PhysicalKeys(Preferences.Keys[Action]))
            if (Observed.Contains(Physical) && Gate.Allows(Physical)) return true;
        return false;
    };
    // Aliases contribute one boolean per binding; normalization remains in model.
    return FVector2D(int32(Held(Forward))-int32(Held(Backward)),
                     int32(Held(Right))-int32(Held(Left)));
}
}
