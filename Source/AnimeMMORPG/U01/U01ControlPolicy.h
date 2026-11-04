#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"

namespace AnimeMMORPG::U01
{
enum class ECaptureDecision : uint8 { Wait, Commit, RejectChord, Cancel };
// Ctrl is bindable on its own. Delay that modifier until release so Ctrl+key
// cannot accidentally commit Ctrl before the second key is observed.
class FSingleKeyCapture
{
public:
    void Reset(){Modifier=FKey();}
    ECaptureDecision Observe(FKey Key,bool bDown,bool bChord)
    {
        if(bDown)
        {
            if(Key==EKeys::Escape){Reset();return ECaptureDecision::Cancel;}
            if(Modifier.IsValid()||bChord){Reset();return ECaptureDecision::RejectChord;}
            if(Key==EKeys::LeftControl||Key==EKeys::RightControl){Modifier=Key;return ECaptureDecision::Wait;}
            return ECaptureDecision::Commit;
        }
        if(Modifier==Key){Reset();return ECaptureDecision::Commit;}
        return ECaptureDecision::Wait;
    }
private:
    FKey Modifier;
};
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
