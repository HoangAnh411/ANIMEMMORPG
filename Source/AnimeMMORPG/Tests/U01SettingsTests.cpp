#include "Misc/AutomationTest.h"
#include "U01/U01Settings.h"
#include "U01/U01ControlPolicy.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "InputAction.h"
#include "InputMappingContext.h"
#include "Engine/LocalPlayer.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
namespace
{
using namespace AnimeMMORPG::U01;
static constexpr EAutomationTestFlags EFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01EBindings,"AnimeMMORPG.U01.E.BindingValidation",EFlags)
bool FU01EBindings::RunTest(const FString&)
{
    FPreferences P;
    for(int32 I=0;I<ControlCount;++I){TestTrue(TEXT("Single unused key accepted per action"),BindingError(P,I,EKeys::H).IsEmpty());TestFalse(TEXT("Other binding rejected without swapping"),BindingError(P,I,P.Keys[(I+1)%ControlCount]).IsEmpty());}
    TestTrue(TEXT("Right Ctrl canonical family"),BindingError(P,Sprint,EKeys::RightControl).IsEmpty());
    TestFalse(TEXT("Ctrl alias collision rejected"),BindingError(P,Jump,EKeys::RightControl).IsEmpty());
    const FKey Rejected[]={EKeys::Escape,EKeys::LeftShift,EKeys::RightShift,EKeys::LeftMouseButton,EKeys::RightMouseButton,EKeys::Q,EKeys::E,EKeys::R,EKeys::F,EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::X,EKeys::Tab,EKeys::I,EKeys::K,EKeys::M,EKeys::MouseX,EKeys::MouseScrollUp,EKeys::Gamepad_FaceButton_Bottom,FKey()};
    for(FKey Key:Rejected)TestFalse(*FString::Printf(TEXT("Reject %s"),*Key.ToString()),BindingError(P,Jump,Key).IsEmpty());
    TestFalse(TEXT("Reject chord"),BindingError(P,Jump,EKeys::H,true).IsEmpty());
    TestTrue(TEXT("Middle mouse valid"),BindingError(P,Jump,EKeys::MiddleMouseButton).IsEmpty());
    TestTrue(TEXT("Thumb mouse valid"),BindingError(P,Jump,EKeys::ThumbMouseButton).IsEmpty());
    auto* State=NewObject<UU01SettingsSubsystem>(NewObject<ULocalPlayer>());
    TestFalse(TEXT("Rejected edit returns false"),State->Bind(Jump,EKeys::W));TestEqual(TEXT("Rejected edit preserves jump"),State->Get().Keys[Jump],EKeys::SpaceBar);
    TestFalse(TEXT("Rejected edit leaves clean"),State->IsDirty());
    TestTrue(TEXT("Apply valid edit"),State->Bind(Jump,EKeys::H));TestTrue(TEXT("Edit marks dirty"),State->IsDirty());
    State->SetSensitivity(2.5f);State->SetInvertY(true);State->SetRightShoulder(false);
    TestEqual(TEXT("Sensitivity live"),State->Get().Sensitivity,2.5f);State->RestoreDefaults();
    TestEqual(TEXT("Restore bindings"),State->Get().Keys[Jump],EKeys::SpaceBar);TestEqual(TEXT("Restore sensitivity"),State->Get().Sensitivity,1.f);
    TestFalse(TEXT("Restore invert"),State->Get().bInvertY);TestTrue(TEXT("Restore shoulder"),State->Get().bRightShoulder);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01ERecovery,"AnimeMMORPG.U01.E.PartialRecovery",EFlags)
bool FU01ERecovery::RunTest(const FString&)
{
    FPreferences P,Out;P.Keys[Jump]=EKeys::H;P.Sensitivity=2.25f;P.bInvertY=true;P.bRightShoulder=false;
    TestTrue(TEXT("Clean decode"),DecodePreferences(EncodePreferences(P),Out).IsEmpty());TestEqual(TEXT("Keep clean binding"),Out.Keys[Jump],EKeys::H);
    TSharedPtr<FJsonObject> Json;FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(EncodePreferences(P)),Json);
    Json->SetStringField(TEXT("sensitivity"),TEXT("2.5"));
    auto Bindings=Json->GetObjectField(TEXT("bindings"));Bindings->SetStringField(TEXT("Forward"),TEXT("Q"));Bindings->SetStringField(TEXT("Backward"),TEXT("W"));
    Bindings->SetStringField(TEXT("Left"),TEXT("J"));Bindings->SetStringField(TEXT("Right"),TEXT("J"));Bindings->SetStringField(TEXT("Interact"),TEXT("J"));
    FString Text;FJsonSerializer::Serialize(Json.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    const FString Notice=DecodePreferences(Text,Out);TestFalse(TEXT("Recovery reports fields"),Notice.IsEmpty());
    TestEqual(TEXT("Wrong type number restored"),Out.Sensitivity,1.f);TestTrue(TEXT("Keep valid invert"),Out.bInvertY);TestFalse(TEXT("Keep valid shoulder"),Out.bRightShoulder);
    TestEqual(TEXT("Keep independent valid jump"),Out.Keys[Jump],EKeys::H);
    TestEqual(TEXT("Conflict closure restored forward"),Out.Keys[AnimeMMORPG::U01::Forward],EKeys::W);TestEqual(TEXT("Conflict closure restored backward"),Out.Keys[Backward],EKeys::S);
    TestEqual(TEXT("Triple conflict third restored"),Out.Keys[Interact],EKeys::G);
    for(int32 I=0;I<ControlCount;++I)TestTrue(TEXT("Recovery leaves no duplicate/reserved binding"),BindingError(Out,I,Out.Keys[I]).IsEmpty());
    TestFalse(TEXT("Malformed JSON feedback"),DecodePreferences(TEXT("broken"),Out).IsEmpty());
    TestEqual(TEXT("Malformed resets defaults"),Out.Keys[Jump],EKeys::SpaceBar);
    TestFalse(TEXT("Unsupported version feedback"),DecodePreferences(TEXT("{\"version\":2}"),Out).IsEmpty());
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01EStorage,"AnimeMMORPG.U01.E.SaveAndFailure",EFlags)
bool FU01EStorage::RunTest(const FString&)
{
    const FString Slot=TEXT("U01E_Test_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString Path=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("SaveGames"),Slot+TEXT(".sav"));
    FPreferences P,Out;FString Message;P.Keys[AnimeMMORPG::U01::Forward]=EKeys::H;P.Sensitivity=2;P.bInvertY=true;P.bRightShoulder=false;
    TestTrue(TEXT("Missing file defaults"),ReadPreferences(Slot,0,Out,Message));TestFalse(TEXT("Load missing does not create file"),UGameplayStatics::DoesSaveGameExist(Slot,0));
    TestTrue(TEXT("Actual SaveGame write"),WritePreferences(Slot,0,P,Message));TestTrue(TEXT("Actual SaveGame read"),ReadPreferences(Slot,0,Out,Message));
    TestEqual(TEXT("Binding persists"),Out.Keys[AnimeMMORPG::U01::Forward],EKeys::H);TestEqual(TEXT("Sensitivity persists"),Out.Sensitivity,2.f);TestTrue(TEXT("Invert persists"),Out.bInvertY);TestFalse(TEXT("Shoulder persists"),Out.bRightShoulder);
    auto* Corrupt=NewObject<UU01ControlSave>();Corrupt->Payload=TEXT("{\"version\":1,\"sensitivity\":2,\"invertY\":true,\"rightShoulder\":false,\"bindings\":{\"Jump\":\"H\"}}");
    TestTrue(TEXT("Write partial fixture"),UGameplayStatics::SaveGameToSlot(Corrupt,Slot,0));
    TArray<uint8> Before,After;FFileHelper::LoadFileToArray(Before,*Path);
    TestFalse(TEXT("Partial file reports recovery"),ReadPreferences(Slot,0,Out,Message));TestEqual(TEXT("Partial valid jump kept"),Out.Keys[Jump],EKeys::H);
    FFileHelper::LoadFileToArray(After,*Path);TestTrue(TEXT("Loading never overwrites damaged storage"),Before==After);
    Corrupt->Version=99;TestTrue(TEXT("Write future schema fixture"),UGameplayStatics::SaveGameToSlot(Corrupt,Slot,0));
    TestFalse(TEXT("Future SaveGame rejected"),ReadPreferences(Slot,0,Out,Message));
    TestTrue(TEXT("Delete fixture save"),UGameplayStatics::DeleteGameInSlot(Slot,0));
    TestTrue(TEXT("Create deterministic write blocker at test-only save path"),IFileManager::Get().MakeDirectory(*Path,true));
    TestFalse(TEXT("Filesystem write failure propagated"),WritePreferences(Slot,0,P,Message));TestFalse(TEXT("Failure visible"),Message.IsEmpty());
    IFileManager::Get().DeleteDirectory(*Path,false,false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01ELocalMapping,"AnimeMMORPG.U01.E.LocalMappingIsolation",EFlags)
bool FU01ELocalMapping::RunTest(const FString&)
{
    auto* Template=NewObject<UInputMappingContext>();TArray<const UInputAction*> Actions;
    FPreferences Defaults,A;A.Keys[AnimeMMORPG::U01::Forward]=EKeys::H;A.Keys[Jump]=EKeys::ThumbMouseButton;
    for(int32 I=0;I<ControlCount;++I){auto* Action=NewObject<UInputAction>();Actions.Add(Action);Template->MapKey(Action,Defaults.Keys[I]);}
    auto* Look=NewObject<UInputAction>();Template->MapKey(Look,EKeys::MouseX);
    auto* PlayerA=NewObject<ULocalPlayer>();auto* PlayerB=NewObject<ULocalPlayer>();
    auto* ContextA=MakeLocalMapping(PlayerA,Template,A,Actions);auto* ContextB=MakeLocalMapping(PlayerB,Template,Defaults,Actions);
    TestNotNull(TEXT("Local A context"),ContextA);TestNotNull(TEXT("Local B context"),ContextB);if(!ContextA||!ContextB)return false;
    TestTrue(TEXT("Separate object and owner"),ContextA!=ContextB&&ContextA!=Template&&ContextA->GetOuter()==PlayerA&&ContextB->GetOuter()==PlayerB);
    auto Has=[](const UInputMappingContext* C,const UInputAction* Action,FKey Key){for(const auto& Map:C->GetMappings())if(Map.Action==Action&&Map.Key==Key)return true;return false;};
    TestTrue(TEXT("A rebound key active"),Has(ContextA,Actions[AnimeMMORPG::U01::Forward],EKeys::H));TestFalse(TEXT("A old key removed"),Has(ContextA,Actions[AnimeMMORPG::U01::Forward],EKeys::W));
    TestTrue(TEXT("B unchanged"),Has(ContextB,Actions[AnimeMMORPG::U01::Forward],EKeys::W));TestFalse(TEXT("B never receives A binding"),Has(ContextB,Actions[AnimeMMORPG::U01::Forward],EKeys::H));
    TestTrue(TEXT("Template unchanged"),Has(Template,Actions[AnimeMMORPG::U01::Forward],EKeys::W));TestFalse(TEXT("Template not mutated"),Has(Template,Actions[AnimeMMORPG::U01::Forward],EKeys::H));
    TestTrue(TEXT("Fixed mouse axis preserved"),Has(ContextA,Look,EKeys::MouseX));TestTrue(TEXT("Right Ctrl default alias mapped"),Has(ContextA,Actions[Sprint],EKeys::RightControl));
    TestTrue(TEXT("Mouse rebind mapped"),Has(ContextA,Actions[Jump],EKeys::ThumbMouseButton));
    FReleaseGate Gate;Gate.Down(EKeys::H,false);Gate.Down(EKeys::ThumbMouseButton,false);Gate.Lock();
    TestFalse(TEXT("Rebound movement quarantined"),Gate.Allows(EKeys::H));TestFalse(TEXT("Rebound mouse jump quarantined"),Gate.Allows(EKeys::ThumbMouseButton));
    Gate.Up(EKeys::H);TestTrue(TEXT("Only physical release rearms movement"),Gate.Allows(EKeys::H));TestFalse(TEXT("Other mouse remains blocked"),Gate.Allows(EKeys::ThumbMouseButton));
    Gate.Up(EKeys::ThumbMouseButton);TestTrue(TEXT("Mouse release rearms jump"),Gate.Allows(EKeys::ThumbMouseButton));
    return true;
}
}
#endif
