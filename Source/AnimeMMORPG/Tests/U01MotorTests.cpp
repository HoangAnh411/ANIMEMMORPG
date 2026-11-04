#include "Misc/AutomationTest.h"
#include "U01/U01Character.h"
#include "U01/U01MotorPolicy.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Tests/AutomationCommon.h"
#include "AIController.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
class FU01PhysicsFixture : public FTestWorldWrapper
{
public:
    explicit FU01PhysicsFixture(FAutomationTestBase& InTest) : Test(InTest)
    {
        if (!CreateTestWorld(EWorldType::Game)) { ForwardErrorMessages(&Test); return; }
        GetTestWorld()->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
    }
    ~FU01PhysicsFixture() { ForwardErrorMessages(&Test); }
    AActor* Box(FVector Center, FVector Size, FRotator Rotation = FRotator::ZeroRotator)
    {
        AActor* Actor = GetTestWorld()->SpawnActor<AActor>();
        UBoxComponent* Shape = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Shape);
        Shape->SetBoxExtent(Size * .5);
        Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Shape->SetCollisionObjectType(ECC_WorldStatic);
        Shape->SetCollisionResponseToAllChannels(ECR_Block);
        Actor->SetActorLocationAndRotation(Center, Rotation);
        Shape->RegisterComponent();
        return Actor;
    }
    void FlatFloor() { Box(FVector(5000,0,-50), FVector(24000,24000,100)); }
    bool Start(FVector Position = FVector(0,0,110))
    {
        Pawn = GetTestWorld()->SpawnActor<AU01Character>(Position, FRotator::ZeroRotator);
        if (!Pawn) { Test.AddError(TEXT("Cannot spawn U01 physics pawn")); return false; }
        Pawn->AutoPossessAI = EAutoPossessAI::Disabled;
        auto* Controller = GetTestWorld()->SpawnActor<AAIController>();
        Controller->Possess(Pawn);
        if (!BeginPlayInTestWorld()) { ForwardErrorMessages(&Test); return false; }
        Tick(1.25f);
        return true;
    }
    void Step(float Dt, FVector Input = FVector::ZeroVector, bool bSprint = false)
    {
        Pawn->GetU01Movement()->SetSprintRequested(bSprint);
        Pawn->AddMovementInput(Input, 1);
        TickTestWorld(Dt);
    }
    void Tick(float Seconds, FVector Input = FVector::ZeroVector, bool bSprint = false, float Dt = 1.f/60)
    {
        const int32 Steps = FMath::RoundToInt(Seconds / Dt);
        for (int32 Index=0; Index<Steps; ++Index) Step(Dt, Input, bSprint);
    }
    double FeetZ() const { return Pawn->GetU01Movement()->GetActorFeetLocation().Z; }
    void Record(const FString& Case, const TMap<FString,double>& Values)
    {
        auto Json = MakeShared<FJsonObject>();
        FString SHA; FParse::Value(FCommandLine::Get(), TEXT("U01SourceSHA="), SHA);
        Json->SetStringField(TEXT("sourceSHA"), SHA);
        Json->SetStringField(TEXT("case"), Case);
        Json->SetNumberField(TEXT("pid"), FPlatformProcess::GetCurrentProcessId());
        Json->SetStringField(TEXT("world"), GetTestWorld()->GetPathName());
        Json->SetNumberField(TEXT("worldType"), int32(GetTestWorld()->WorldType));
        Json->SetNumberField(TEXT("netMode"), int32(GetTestWorld()->GetNetMode()));
        Json->SetStringField(TEXT("pawn"), Pawn->GetPathName());
        Json->SetStringField(TEXT("controller"), GetPathNameSafe(Pawn->GetController()));
        Json->SetNumberField(TEXT("localRole"), int32(Pawn->GetLocalRole()));
        Json->SetStringField(TEXT("method"), TEXT("Controlled input fixture in real Game physics world; not keyboard/renderer FPS"));
        Json->SetStringField(TEXT("feetWorldCm"), Pawn->GetU01Movement()->GetActorFeetLocation().ToString());
        for (const auto& Value : Values) Json->SetNumberField(Value.Key, Value.Value);
        FString Text;
        FJsonSerializer::Serialize(Json, TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text));
        Test.AddInfo(TEXT("U01C_MEASURE ") + Text);
    }
    AU01Character* Pawn = nullptr;
private:
    FAutomationTestBase& Test;
};
constexpr auto MotorFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01JumpWindowTest, "AnimeMMORPG.U01.C.JumpWindows", MotorFlags)
bool FU01JumpWindowTest::RunTest(const FString&)
{
    using AnimeMMORPG::U01::FJumpWindow;
    for (double Age : {0., .099, .100, .101})
    {
        FJumpWindow Coyote;
        Coyote.LeaveGround(0, false);
        Coyote.Press(Age);
        TestEqual(FString::Printf(TEXT("Coyote age %.3f"), Age), Coyote.Consume(Age, false), Age < .1);
        FJumpWindow Buffer;
        Buffer.Press(0);
        Buffer.Release(); // A brief tap survives release and is consumed on landing.
        Buffer.Land();
        TestEqual(FString::Printf(TEXT("Buffer age %.3f"), Age), Buffer.Consume(Age, true), Age < .1);
    }
    FJumpWindow Gate;
    Gate.Press(0); TestTrue(TEXT("Ground edge accepted"), Gate.Consume(0, true));
    Gate.LeaveGround(0, true); Gate.Release(); Gate.Press(.05);
    TestFalse(TEXT("Voluntary jump cannot grant coyote/double jump"), Gate.Consume(.05, false));
    Gate.Land();
    TestFalse(TEXT("Expired buffer at landing"), Gate.Consume(.5, true));
    TestFalse(TEXT("Held key cannot generate new press on landing"), Gate.Press(.5));
    Gate.Release(); TestTrue(TEXT("Release then new edge"), Gate.Press(.5));
    Gate.ClearInput(); TestFalse(TEXT("Lock clears pending jump"), Gate.Consume(.5, true));
    TestFalse(TEXT("Lock does not fake physical release"), Gate.Press(.6));
    Gate.ResetSession(); TestFalse(TEXT("New session cannot reuse deadline"), Gate.CanConsume(.01, false));
    TestFalse(TEXT("Before coyote start invalid"), [&]{ FJumpWindow W; W.LeaveGround(1,false); return W.HasCoyote(.999); }());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01FlatMovementTest, "AnimeMMORPG.U01.C.FlatMovement", MotorFlags)
bool FU01FlatMovementTest::RunTest(const FString&)
{
    double Straight = 0;
    for (int32 Case=0; Case<3; ++Case)
    {
        FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor();
        if (!Fixture.Start()) return false;
        const bool bSprint = Case == 1;
        const FVector Input = Case == 2 ? FVector(1,1,0) : FVector::ForwardVector;
        Fixture.Pawn->GetU01Movement()->SetSprintRequested(true);
        TestFalse(TEXT("Sprint without direction inactive"), Fixture.Pawn->GetU01Movement()->IsSprinting());
        Fixture.Tick(1, Input, bSprint); // Exclude acceleration from the measured interval.
        const FVector Start = Fixture.Pawn->GetActorLocation();
        const double StartTime = Fixture.GetTestWorld()->GetTimeSeconds();
        Fixture.Tick(10, Input, bSprint);
        const double Distance = (Fixture.Pawn->GetActorLocation()-Start).Size2D();
        const double Target = bSprint ? 7000 : 5000;
        TestTrue(TEXT("Ten-second steady displacement within 50cm"), FMath::Abs(Distance-Target) <= 50);
        if (Case == 0) Straight = Distance;
        if (Case == 2) TestTrue(TEXT("Diagonal speed within one percent"), FMath::Abs(Distance / Straight - 1) <= .01);
        Fixture.Record(Case == 0 ? TEXT("Walk10s") : Case == 1 ? TEXT("Sprint10s") : TEXT("Diagonal10s"),
            {{TEXT("distanceCm"), Distance}, {TEXT("targetCm"), Target}, {TEXT("seconds"), Fixture.GetTestWorld()->GetTimeSeconds()-StartTime},
             {TEXT("speedCmPerSec"), Fixture.Pawn->GetVelocity().Size2D()}});
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01JumpPhysicsTest, "AnimeMMORPG.U01.C.JumpPhysics", MotorFlags)
bool FU01JumpPhysicsTest::RunTest(const FString&)
{
    for (float Dt : {1.f/30,1.f/60,1.f/120})
    {
        FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor(); if (!Fixture.Start()) return false;
        const double Start = Fixture.FeetZ(); double Peak = Start;
        Fixture.Pawn->Jump();
        for (int32 Index=0; Index<FMath::RoundToInt(2.f/Dt); ++Index)
        {
            Fixture.Step(Dt); Peak = FMath::Max(Peak, Fixture.FeetZ());
            Fixture.Pawn->Jump(); // Simulate holding/repeated command: no new physical edge.
            TestTrue(TEXT("JumpMaxCount one"), Fixture.Pawn->JumpCurrentCount <= 1);
        }
        TestTrue(TEXT("Apex 120cm plus/minus 5cm"), FMath::Abs(Peak-Start-120) <= 5);
        TestTrue(TEXT("Holding Space does not jump again after landing"), Fixture.Pawn->GetU01Movement()->IsMovingOnGround());
        Fixture.Pawn->StopJumping(); Fixture.Pawn->Jump(); Fixture.Tick(.15f);
        const double Before = Fixture.Pawn->GetVelocity().Z;
        Fixture.Pawn->StopJumping(); Fixture.Pawn->Jump(); Fixture.Step(Dt);
        TestTrue(TEXT("New edge during voluntary jump does not boost velocity"), Fixture.Pawn->GetVelocity().Z <= Before);
        Fixture.Record(TEXT("JumpApex"), {{TEXT("stepSeconds"), Dt}, {TEXT("apexCm"), Peak-Start},
            {TEXT("gravityCmPerSec2"), Fixture.Pawn->GetU01Movement()->GetGravityZ()},
            {TEXT("jumpZVelocityCmPerSec"), Fixture.Pawn->GetU01Movement()->JumpZVelocity}});
    }
    {
        FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor(); if (!Fixture.Start()) return false;
        Fixture.Pawn->SetActorLocation(FVector(0,0,220), false, nullptr, ETeleportType::TeleportPhysics);
        Fixture.Pawn->GetU01Movement()->SetMovementMode(MOVE_Falling);
        Fixture.Pawn->GetU01Movement()->Velocity = FVector(0,0,-400);
        bool bPressed = false, bBufferedTakeoff = false;
        for (int32 Index=0; Index<90; ++Index)
        {
            if (!bPressed && Fixture.FeetZ() < 30)
            { Fixture.Pawn->Jump(); Fixture.Pawn->StopJumping(); bPressed = true; }
            Fixture.Step(1.f/120);
            if (bPressed && Fixture.Pawn->GetVelocity().Z > 0) { bBufferedTakeoff = true; break; }
        }
        TestTrue(TEXT("Actual floor landing consumes a recent released tap"), bBufferedTakeoff);
        Fixture.Record(TEXT("LandingBuffer"), {{TEXT("jumped"), bBufferedTakeoff ? 1. : 0.}});
    }
    {
        FU01PhysicsFixture Fixture(*this);
        Fixture.Box(FVector(0,0,250), FVector(400,400,100));
        if (!Fixture.Start(FVector(0,0,410))) return false;
        int32 FallingFrames = 0; bool bTookOff = false;
        for (int32 Index=0; Index<160; ++Index)
        {
            if (Fixture.Pawn->GetU01Movement()->IsFalling())
            {
                ++FallingFrames;
                if (FallingFrames == 4) Fixture.Pawn->Jump();
            }
            Fixture.Step(1.f/120, FVector::ForwardVector);
            if (FallingFrames >= 4 && Fixture.Pawn->GetVelocity().Z > 0) { bTookOff = true; break; }
        }
        TestTrue(TEXT("Actual ledge permits recent involuntary coyote jump"), bTookOff);
        Fixture.Record(TEXT("LedgeCoyote"), {{TEXT("jumped"), bTookOff ? 1. : 0.}});
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01TerrainTest, "AnimeMMORPG.U01.C.Terrain", MotorFlags)
bool FU01TerrainTest::RunTest(const FString&)
{
    for (double Angle : {30.,44.,45.,46.,60.})
    {
        FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor();
        const double Radians = FMath::DegreesToRadians(Angle), Length=800, Thickness=20;
        Fixture.Box(FVector(Length*.5*FMath::Cos(Radians)+Thickness*.5*FMath::Sin(Radians),0,
            Length*.5*FMath::Sin(Radians)-Thickness*.5*FMath::Cos(Radians)), FVector(Length,400,Thickness), FRotator(Angle,0,0));
        if (!Fixture.Start(FVector(-300,0,110))) return false;
        double PeakFeet = Fixture.FeetZ(), HighestGrounded = 0;
        for (int32 Index=0; Index<240; ++Index)
        {
            Fixture.Step(1.f/60, FVector::ForwardVector);
            PeakFeet = FMath::Max(PeakFeet, Fixture.FeetZ());
            if (Fixture.Pawn->GetU01Movement()->IsMovingOnGround()) HighestGrounded = FMath::Max(HighestGrounded, Fixture.FeetZ());
        }
        if (Angle <= 45) TestTrue(TEXT("Walkable slope climbed while grounded"), HighestGrounded > 150);
        else TestTrue(TEXT("Steep slope not climbed by walk input"), PeakFeet < 80);
        Fixture.Record(TEXT("SlopeWalk"), {{TEXT("angleDegrees"),Angle},{TEXT("peakFeetZCm"),PeakFeet},{TEXT("highestGroundedFeetZCm"),HighestGrounded}});
        if (Angle > 45)
        {
            const double X = Length*.5*FMath::Cos(Radians);
            const double Z = X*FMath::Tan(Radians);
            Fixture.Pawn->SetActorLocation(FVector(X,0,Z+180), false, nullptr, ETeleportType::TeleportPhysics);
            Fixture.Pawn->GetU01Movement()->StopMovementImmediately();
            Fixture.Pawn->GetU01Movement()->SetMovementMode(MOVE_Falling);
            Fixture.Tick(1.5f);
            const double SlideX = Fixture.Pawn->GetActorLocation().X-X;
            TestTrue(TEXT("Steep slope slides downhill without input"), SlideX < -20);
            Fixture.Record(TEXT("SlopeSlide"), {{TEXT("angleDegrees"),Angle},{TEXT("deltaXCm"),SlideX}});
        }
    }
    for (double Height : {20.,40.,60.})
    {
        FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor();
        Fixture.Box(FVector(200,0,Height*.5), FVector(400,400,Height));
        if (!Fixture.Start(FVector(-300,0,110))) return false;
        double Peak = Fixture.FeetZ(), MaxX = -300;
        for (int32 Index=0; Index<180; ++Index)
        { Fixture.Step(1.f/60, FVector::ForwardVector); Peak=FMath::Max(Peak,Fixture.FeetZ()); MaxX=FMath::Max(MaxX,Fixture.Pawn->GetActorLocation().X); }
        if (Height <= 45) TestTrue(TEXT("Step within 45cm traversed"), MaxX > 450 && Peak >= Height);
        else TestTrue(TEXT("60cm step blocks walk"), MaxX < 50 && Peak < 50);
        Fixture.Record(TEXT("Step"), {{TEXT("stepHeightCm"),Height},{TEXT("peakFeetZCm"),Peak},{TEXT("maxXCm"),MaxX}});
    }
    for (double Ceiling : {180.,260.})
    {
        FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor();
        Fixture.Box(FVector(1000,0,Ceiling+10), FVector(2000,400,20));
        if (!Fixture.Start(FVector(-300,0,110))) return false;
        Fixture.Tick(1.5f, FVector::ForwardVector);
        if (Ceiling == 180) TestTrue(TEXT("Standing capsule cannot enter 180cm roof"), Fixture.Pawn->GetActorLocation().X < 0);
        else
        {
            TestTrue(TEXT("260cm roof permits standing movement"), Fixture.Pawn->GetActorLocation().X > 100);
            Fixture.Pawn->GetU01Movement()->StopMovementImmediately();
            const double StartFeet=Fixture.FeetZ(); double Peak=StartFeet;
            Fixture.Pawn->Jump();
            for(int32 Index=0; Index<90; ++Index) { Fixture.Step(1.f/120); Peak=FMath::Max(Peak,Fixture.FeetZ()); }
            TestTrue(TEXT("Roof truncates jump without motor penetration"), Peak-StartFeet > 20 && Peak-StartFeet < 100);
        }
        Fixture.Record(TEXT("Ceiling"), {{TEXT("undersideCm"),Ceiling},{TEXT("positionXCm"),Fixture.Pawn->GetActorLocation().X}});
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01MotorLockTest, "AnimeMMORPG.U01.C.MotorLocks", MotorFlags)
bool FU01MotorLockTest::RunTest(const FString&)
{
    FU01PhysicsFixture Fixture(*this); Fixture.FlatFloor(); if (!Fixture.Start()) return false;
    auto* Movement=Fixture.Pawn->GetU01Movement();
    Fixture.Pawn->SetActorLocation(FVector(0,0,650), false, nullptr, ETeleportType::TeleportPhysics);
    Movement->SetMovementMode(MOVE_Falling); Movement->Velocity=FVector(100,50,0);
    Movement->SetMotorLock(EU01MotorLock::Interacting,true);
    Movement->SetMotorLock(EU01MotorLock::Defeated,true);
    Movement->SetMotorLock(EU01MotorLock::Interacting,false);
    TestTrue(TEXT("Independent remaining reason keeps motor locked"),Movement->IsMotorLocked());
    const double Start=Fixture.FeetZ();
    Fixture.Pawn->Jump(); Fixture.Tick(.2f,FVector::ForwardVector,true);
    TestTrue(TEXT("Gravity continues under lock"),Fixture.FeetZ()<Start && Fixture.Pawn->GetVelocity().Z<0);
    TestTrue(TEXT("No controlled horizontal movement under lock"),Fixture.Pawn->GetVelocity().SizeSquared2D()<.01);
    TestEqual(TEXT("No jump under lock"),Fixture.Pawn->JumpCurrentCount,0);
    TestFalse(TEXT("No sprint under lock"),Movement->IsSprinting());
    Movement->SetMotorLock(EU01MotorLock::Defeated,false);
    TestFalse(TEXT("All reasons removed unlocks motor"),Movement->IsMotorLocked());
    Fixture.Record(TEXT("MotorLocks"),{{TEXT("fallCm"),Start-Fixture.FeetZ()},{TEXT("verticalVelocityCmPerSec"),Fixture.Pawn->GetVelocity().Z}});
    return true;
}
#endif
