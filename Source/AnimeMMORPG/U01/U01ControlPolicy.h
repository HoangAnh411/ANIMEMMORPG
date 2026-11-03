#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"

namespace AnimeMMORPG::U01
{
// Physical key events are observed before UMG/Enhanced Input, including UI-only menus.
class FReleaseGate
{
public:
    void Down(FKey Key, bool bLocked) { Pressed.Add(Key); if (bLocked) Blocked.Add(Key); }
    void Up(FKey Key) { Pressed.Remove(Key); Blocked.Remove(Key); }
    void Lock() { Blocked.Append(Pressed); }
    bool Allows(FKey Key) const { return !Blocked.Contains(Key); }
private:
    TSet<FKey> Pressed;
    TSet<FKey> Blocked;
};

inline FRotator ApplyMouse(FRotator Rotation, double Yaw, double Pitch, double Sensitivity)
{
    return FRotator(FMath::Clamp(FRotator::NormalizeAxis(Rotation.Pitch) + Pitch * Sensitivity, -70.0, 60.0),
        FRotator::NormalizeAxis(Rotation.Yaw + Yaw * Sensitivity), 0);
}

// Shorter obstruction distance is applied immediately, only outward recovery is smoothed.
inline float ResolveDistance(float Current, float SafeTarget, float DeltaSeconds)
{
    return SafeTarget <= Current ? SafeTarget : FMath::FInterpTo(Current, SafeTarget, DeltaSeconds, 8.f);
}
}
