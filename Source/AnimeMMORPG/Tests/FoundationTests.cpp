#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Foundation/UnitsAndTime.h"
#include "Math/Transform.h"

using namespace AnimeMMORPG::Foundation;
namespace { constexpr double Tolerance = 1.e-9; }

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU00Units, "AnimeMMORPG.U00.Foundation.Units", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FU00Units::RunTest(const FString& Parameters)
{
    const double Meters[] = {0.0, 1.0, 10.0, -2.5};
    const double Centimeters[] = {0.0, 100.0, 1000.0, -250.0};
    for (int32 I = 0; I < 4; ++I)
    {
        TestEqual(TEXT("Meters to centimeters"), MetersToCentimeters(Meters[I]), Centimeters[I]);
        TestEqual(TEXT("Centimeters to meters"), CentimetersToMeters(Centimeters[I]), Meters[I]);
    }
    for (double Value : {0.0, 0.1, 1.23456789, -1234.56789, 10000.0})
    {
        TestTrue(TEXT("Meter round trip within absolute 1e-9"), FMath::Abs(CentimetersToMeters(MetersToCentimeters(Value)) - Value) <= Tolerance);
        TestTrue(TEXT("Centimeter round trip within absolute 1e-9"), FMath::Abs(MetersToCentimeters(CentimetersToMeters(Value)) - Value) <= Tolerance);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU00Axes, "AnimeMMORPG.U00.Foundation.Axes", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FU00Axes::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Forward +X"), FVector::ForwardVector.Equals(FVector(1, 0, 0), Tolerance));
    TestTrue(TEXT("Right +Y"), FVector::RightVector.Equals(FVector(0, 1, 0), Tolerance));
    TestTrue(TEXT("Up +Z"), FVector::UpVector.Equals(FVector(0, 0, 1), Tolerance));
    const FTransform Pose(FRotator(0, 90, 0), FVector(100, 200, 300));
    TestTrue(TEXT("Yaw +90 turns forward to +Y"), Pose.TransformVectorNoScale(FVector::ForwardVector).Equals(FVector(0, 1, 0), Tolerance));
    TestTrue(TEXT("Yaw +90 turns right to -X"), Pose.TransformVectorNoScale(FVector::RightVector).Equals(FVector(-1, 0, 0), Tolerance));
    TestTrue(TEXT("Yaw preserves up"), Pose.TransformVectorNoScale(FVector::UpVector).Equals(FVector(0, 0, 1), Tolerance));
    TestTrue(TEXT("Local 1m position rotates and translates to world cm"), Pose.TransformPosition(FVector(MetersToCentimeters(1), 0, 0)).Equals(FVector(100, 300, 300), Tolerance));
    TestTrue(TEXT("Negative yaw turns forward to -Y"), FRotator(0, -90, 0).RotateVector(FVector::ForwardVector).Equals(FVector(0, -1, 0), Tolerance));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU00Interval, "AnimeMMORPG.U00.Foundation.HalfOpenInterval", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FU00Interval::RunTest(const FString& Parameters)
{
    const double Times[] = {9.0, 10.0, 11.0, 12.0, 13.0};
    const bool Expected[] = {false, true, true, false, false};
    for (int32 I = 0; I < 5; ++I)
    {
        TestEqual(TEXT("Before/start/inside/end/after"), IsWithinHalfOpenInterval(Times[I], 10, 12), Expected[I]);
        TestFalse(TEXT("Empty interval"), IsWithinHalfOpenInterval(Times[I], 10, 10));
        TestFalse(TEXT("Reversed interval"), IsWithinHalfOpenInterval(Times[I], 12, 10));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU00Order, "AnimeMMORPG.U00.Foundation.CallOrder", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FU00Order::RunTest(const FString& Parameters)
{
    const double Inputs[] = {0.0, -2.5, 1.0, 10.0};
    double Baseline[4]; bool Active[4];
    for (int32 I = 0; I < 4; ++I) { Baseline[I] = MetersToCentimeters(Inputs[I]); Active[I] = IsWithinHalfOpenInterval(Inputs[I], 0, 10); }
    for (int32 I = 3; I >= 0; --I)
    {
        IsWithinHalfOpenInterval(1000, 1, 2);
        CentimetersToMeters(-999);
        TestEqual(TEXT("Conversion independent of intervening calls and order"), MetersToCentimeters(Inputs[I]), Baseline[I]);
        TestEqual(TEXT("Interval independent of intervening calls and order"), IsWithinHalfOpenInterval(Inputs[I], 0, 10), Active[I]);
    }
    return true;
}
#endif
