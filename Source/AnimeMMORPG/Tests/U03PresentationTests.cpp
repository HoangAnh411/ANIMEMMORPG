#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U03/U03FeedbackWindow.h"
#include "U01/U01Settings.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "U01/U01AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"

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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03DMigration,"AnimeMMORPG.U03.D.LegacyConflictAndFutureSchema",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03DMigration::RunTest(const FString&)
{
    namespace C=AnimeMMORPG::U01;
    C::FPreferences P,Out;P.Keys[C::Forward]=EKeys::H;
    TSharedPtr<FJsonObject> J;FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(C::EncodePreferences(P)),J);
    J->SetNumberField(TEXT("version"),1);const auto B=J->GetObjectField(TEXT("bindings"));
    for(const TCHAR* Name:{TEXT("Attack"),TEXT("Guard"),TEXT("Dodge"),TEXT("EscapeCC"),TEXT("Q"),TEXT("E"),TEXT("Target")})B->RemoveField(Name);
    B->SetStringField(TEXT("Jump"),TEXT("Q"));
    FString Text;FJsonSerializer::Serialize(J.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    const FString Before=Text;
    TestFalse(TEXT("New combat default conflicts with legacy binding: report recovery"),C::DecodePreferences(Text,Out).IsEmpty());
    TestEqual(TEXT("Independent valid legacy binding preserved"),Out.Keys[C::Forward],EKeys::H);
    TestEqual(TEXT("Conflict restores legacy jump"),Out.Keys[C::Jump],EKeys::SpaceBar);
    TestEqual(TEXT("New Q default preserved"),Out.Keys[C::SkillQ],EKeys::Q);
    TestEqual(TEXT("Decoder does not mutate input"),Text,Before);
    for(int32 I=0;I<C::ControlCount;++I)TestTrue(TEXT("No conflict after v1 migration"),C::BindingError(Out,I,Out.Keys[I]).IsEmpty());
    J->SetNumberField(TEXT("version"),99);Text.Empty();FJsonSerializer::Serialize(J.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    TestFalse(TEXT("Unsupported JSON schema reports fallback"),C::DecodePreferences(Text,Out).IsEmpty());
    TestEqual(TEXT("Unsupported schema restores defaults"),Out.Keys[C::Forward],EKeys::W);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03DDedup,"AnimeMMORPG.U03.D.FeedbackDedupAndLateAudio",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03DDedup::RunTest(const FString&)
{
    using namespace AnimeMMORPG::U03;uint64 Watermark=0;
    TestTrue(TEXT("First identity consumed"),ConsumeFeedback(7,Watermark));
    TestFalse(TEXT("Duplicate snapshot silent"),ConsumeFeedback(7,Watermark));
    TestFalse(TEXT("Stale snapshot silent"),ConsumeFeedback(6,Watermark));
    TestTrue(TEXT("New event accepted"),ConsumeFeedback(8,Watermark));
    Watermark=20; // initial-only authority history watermark supplied on join
    TestFalse(TEXT("Fresh-timestamp historical event on reconnect stays silent"),ConsumeFeedback(20,Watermark));
    TestTrue(TEXT("First event after connection baseline is new"),ConsumeFeedback(21,Watermark));
    TestFalse(TEXT("Reconnect baseline is silent"),FreshFeedbackAudio(true,false,true,10,10.02));
    TestTrue(TEXT("Fresh visible new event audible"),FreshFeedbackAudio(true,true,true,10,10.02));
    TestFalse(TEXT("Late snapshot has visual remainder but no audio replay"),FreshFeedbackAudio(true,true,true,10,10.3));
    TestTrue(TEXT("Late visual still inside event window"),FeedbackRemaining(10,10.3)>0);
    TestFalse(TEXT("Future snapshot cannot sound"),FreshFeedbackAudio(true,true,true,10,9.9));
    TestFalse(TEXT("Hidden proxy silent"),FreshFeedbackAudio(true,true,false,10,10.02));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03DDefenseAssets,"AnimeMMORPG.U03.D.DefensePoseAssets",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03DDefenseAssets::RunTest(const FString&)
{
    auto* C=LoadClass<UU01AnimInstance>(nullptr,TEXT("/Game/AnimeMMORPG/U03/Animation/ABP_U03.ABP_U03_C"));
    if(!TestNotNull(TEXT("Existing U03 animation class"),C))return false;
    const auto* Defaults=C->GetDefaultObject<UU01AnimInstance>();
    if(!TestEqual(TEXT("Five serialized pose dependencies"),Defaults->DefenseMontages.Num(),5))return false;
    for(const auto& M:Defaults->DefenseMontages)
    {
        if(!TestNotNull(TEXT("Pose montage"),M.Get()))return false;
        TestEqual(TEXT("Separate presentation slot"),M->SlotAnimTracks[0].SlotName,FName(TEXT("U03Defense")));
        TestEqual(TEXT("No gameplay notifies"),M->Notifies.Num(),0);
        const auto* A=Cast<UAnimSequence>(M->SlotAnimTracks[0].AnimTrack.AnimSegments[0].GetAnimReference());
        if(!TestNotNull(TEXT("Authored pose sequence"),A))return false;
        TestFalse(TEXT("No root motion authority"),A->bEnableRootMotion);
        TestEqual(TEXT("No notify dependency"),A->Notifies.Num(),0);
        TestTrue(TEXT("Fixed root pose"),A->ExtractRootMotionFromRange(0,1,FAnimExtractContext()).GetTranslation().IsNearlyZero(.001));
    }
    return true;
}
#endif
