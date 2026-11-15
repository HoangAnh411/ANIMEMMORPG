#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U03/U03FeedbackWindow.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03DFeedbackWindow,"AnimeMMORPG.U03.D.AbsoluteFeedbackWindow",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03DFeedbackWindow::RunTest(const FString&)
{
    using namespace AnimeMMORPG::U03;
    TestTrue(TEXT("Full window at timestamp"),FMath::IsNearlyEqual(FeedbackRemaining(10,10),1.2,1.e-12));
    TestTrue(TEXT("Late snapshot gets remaining time"),FMath::IsNearlyEqual(FeedbackRemaining(10,10.9),.3,1.e-12));
    TestEqual(TEXT("Exact expiry hidden"),FeedbackRemaining(10,11.2),0.);
    TestEqual(TEXT("Future event hidden"),FeedbackRemaining(10,9.9),0.);
    for(double Step:{1./30,1./60,1./120,.7})
    {
        for(double T=10;T<12;T+=Step)
        {
            const double First=FeedbackRemaining(10,T);
            TestEqual(TEXT("Duplicate sampling does not extend event"),FeedbackRemaining(10,T),First);
            TestTrue(TEXT("Remaining bounded by original timestamp"),First<=1.2);
        }
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03DRecentHitVisibility,"AnimeMMORPG.U03.D.RecentHitVisibility",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03DRecentHitVisibility::RunTest(const FString&)
{
    using namespace AnimeMMORPG::U03;
    TestTrue(TEXT("Current visible hit"),RecentHitVisible(10,10.5,true,true,true));
    TestFalse(TEXT("New life/revision hides old hit"),RecentHitVisible(10,10.5,false,true,true));
    TestFalse(TEXT("Offscreen hides immediately"),RecentHitVisible(10,10.5,true,false,true));
    TestFalse(TEXT("Environment hides immediately"),RecentHitVisible(10,10.5,true,true,false));
    TestFalse(TEXT("Visibility cannot rearm expiry"),RecentHitVisible(10,11.2,true,true,true));
    return true;
}
#endif
