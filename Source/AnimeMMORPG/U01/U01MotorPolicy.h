#pragma once

#include "CoreMinimal.h"
#include "Foundation/UnitsAndTime.h"

namespace AnimeMMORPG::U01
{
// Clock values are seconds in one world/session. No epsilon expands either deadline.
class FJumpWindow
{
public:
    static constexpr double WindowSeconds = .10;
    bool Press(double Now)
    {
        if (bHeld) return false;
        bHeld = true;
        PressedAt = Now;
        return true;
    }
    void Release() { bHeld = false; }
    bool IsHeld() const { return bHeld; }
    void LeaveGround(double Now, bool bVoluntary)
    {
        LeftGroundAt = (!bVoluntary && !bConsumedInAir) ? TOptional<double>(Now) : TOptional<double>();
    }
    void Land() { bConsumedInAir = false; LeftGroundAt.Reset(); }
    bool HasBuffer(double Now) const
    {
        return PressedAt.IsSet() && Foundation::IsWithinHalfOpenInterval(Now, PressedAt.GetValue(), PressedAt.GetValue() + WindowSeconds);
    }
    bool HasCoyote(double Now) const
    {
        return !bConsumedInAir && LeftGroundAt.IsSet() && Foundation::IsWithinHalfOpenInterval(Now, LeftGroundAt.GetValue(), LeftGroundAt.GetValue() + WindowSeconds);
    }
    bool CanConsume(double Now, bool bGrounded) const { return HasBuffer(Now) && (bGrounded || HasCoyote(Now)); }
    bool Consume(double Now, bool bGrounded)
    {
        if (!CanConsume(Now, bGrounded)) return false;
        PressedAt.Reset(); LeftGroundAt.Reset(); bConsumedInAir = true;
        return true;
    }
    void ClearInput() { PressedAt.Reset(); LeftGroundAt.Reset(); }
    void ResetSession() { *this = FJumpWindow(); }
private:
    TOptional<double> PressedAt;
    TOptional<double> LeftGroundAt;
    bool bHeld = false;
    bool bConsumedInAir = false;
};
}
