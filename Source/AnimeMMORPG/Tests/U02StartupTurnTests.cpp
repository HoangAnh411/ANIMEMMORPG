#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U02/U02StartupTurn.h"
using namespace AnimeMMORPG::U02;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU02TurnTrajectory,"AnimeMMORPG.U02.C.StartupTurnTrajectory",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU02TurnTrajectory::RunTest(const FString&)
{
    for(double Angle:{0.,45.,-45.,90.,-90.,179.,-179.,180.})
    {
        FStartupTurn T;T.Begin(0,Angle,10,10.16);
        TestEqual(TEXT("Acceptance preserves body"),T.Sample(10),0.);
        double Previous=0;
        for(int I=1;I<=160;++I)
        {
            const double Y=T.Sample(10+I*.001);
            const double Distance=FMath::Abs(FStartupTurn::Delta(0,Y));
            TestTrue(TEXT("Continuous monotonic shortest arc without overshoot"),Distance+1.e-9>=Previous && Distance<=FMath::Abs(Angle)+1.e-9);
            Previous=Distance;
        }
        TestTrue(TEXT("Deadline reaches target"),FMath::Abs(FStartupTurn::Delta(T.Sample(10.16),Angle))<1.e-9);
        TestEqual(TEXT("Midpoint smoothstep"),FStartupTurn::Delta(0,T.Sample(10.08)),FStartupTurn::Delta(0,Angle)*.5,1.e-9);
        for(double Rate:{30.,60.,120.})
        {
            double Now=10;while(Now<10.16)Now+=1./Rate;
            TestTrue(TEXT("Frame crossing deadline has locked target"),FMath::Abs(FStartupTurn::Delta(T.Sample(Now),Angle))<1.e-9);
        }
    }
    TestEqual(TEXT("180 tie fixed positive"),FStartupTurn::Delta(0,-180),180.);
    for(double From:{179.,-179.})
    {
        FStartupTurn T;T.Begin(From,-From,0,.16);
        TestTrue(TEXT("Wrap crosses two degrees, not whole circle"),FMath::Abs(FStartupTurn::Delta(From,T.Sample(.08)))<1.01);
    }
    for(double At:{.001,.08,.159})
    {
        FStartupTurn T;T.Begin(0,90,0,.16);const double Before=T.Sample(At);
        T.Retarget(At,-90);
        TestEqual(TEXT("Retarget continuous at current body"),T.Sample(At),Before);
        TestEqual(TEXT("Retarget cannot extend startup"),T.ActiveStart,.16);
        TestEqual(TEXT("Latest aim reached at original deadline"),T.Sample(.16),-90.);
        T.Retarget(.16,30);T.Retarget(.22,60);
        TestEqual(TEXT("Active/recovery ignore aim changes"),T.Sample(.3),-90.);
        T.Begin(45,45,1,1.16);
        TestEqual(TEXT("New action/reset cannot inherit old turn"),T.Sample(1.08),45.);
    }
    return true;
}
#endif
