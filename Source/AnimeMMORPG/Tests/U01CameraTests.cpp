#include "Misc/AutomationTest.h"
#include "U01/U01ControlPolicy.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01ReleaseGateTest, "AnimeMMORPG.U01.B.ReleaseGate", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FU01ReleaseGateTest::RunTest(const FString&)
{
    AnimeMMORPG::U01::FReleaseGate Gate;
    Gate.Down(EKeys::W, false);
    Gate.Down(EKeys::SpaceBar, false);
    Gate.Lock();
    TestFalse(TEXT("W held through lock is blocked"), Gate.Allows(EKeys::W));
    TestFalse(TEXT("Space held through lock is blocked"), Gate.Allows(EKeys::SpaceBar));
    Gate.Down(EKeys::LeftControl, true);
    TestFalse(TEXT("Press during menu remains blocked on resume"), Gate.Allows(EKeys::LeftControl));
    Gate.Up(EKeys::W);
    TestTrue(TEXT("Only released key re-arms"), Gate.Allows(EKeys::W));
    TestFalse(TEXT("Other held key stays blocked"), Gate.Allows(EKeys::SpaceBar));
    Gate.Up(EKeys::SpaceBar); Gate.Down(EKeys::SpaceBar, false);
    TestTrue(TEXT("New edge after release accepted"), Gate.Allows(EKeys::SpaceBar));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01CameraPolicyTest, "AnimeMMORPG.U01.B.CameraPolicy", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FU01CameraPolicyTest::RunTest(const FString&)
{
    using namespace AnimeMMORPG::U01;
    TestEqual(TEXT("Retract immediately"), ResolveDistance(350, 30, 1.f/120), 30.f);
    const float Recovery = ResolveDistance(30, 350, 1.f/60);
    TestTrue(TEXT("Outward recovery is bounded and smooth"), Recovery > 30 && Recovery < 350);
    TestEqual(TEXT("Pitch upper bound"), ApplyMouse(FRotator::ZeroRotator, 0, 1000, 1).Pitch, 60.0);
    TestEqual(TEXT("Pitch lower bound"), ApplyMouse(FRotator::ZeroRotator, 0, -1000, 1).Pitch, -70.0);
    FRotator Once = ApplyMouse(FRotator::ZeroRotator, 40, 20, 1);
    FRotator Split = FRotator::ZeroRotator;
    for (int32 Index=0; Index<4; ++Index) Split = ApplyMouse(Split, 10, 5, 1);
    TestTrue(TEXT("Same accumulated mouse delta independent of partition"), Once.Equals(Split, 1.e-6));
    return true;
}
#endif
