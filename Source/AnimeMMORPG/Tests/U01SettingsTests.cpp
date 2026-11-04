#include "Misc/AutomationTest.h"
#include "U01/U01Settings.h"
#include "U01/U01ControlPolicy.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "InputAction.h"
#include "InputMappingContext.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/MemoryWriter.h"
#include "Misc/Crc.h"
namespace
{
namespace Controls=AnimeMMORPG::U01;
// Author a valid envelope containing deliberately invalid SaveGame fields.
static bool StoreFixture(UU01ControlSave* Save,const FString& Slot)
{
    TArray<uint8> Payload,Bytes;if(!UGameplayStatics::SaveGameToMemory(Save,Payload))return false;
    uint32 Magic=0x45313055,Version=1,Length=Payload.Num(),CRC=FCrc::MemCrc32(Payload.GetData(),Payload.Num());
    FMemoryWriter Writer(Bytes);Writer<<Magic<<Version<<Length<<CRC;Writer.Serialize(Payload.GetData(),Payload.Num());
    return UGameplayStatics::SaveDataToSlot(Bytes,Slot,0);
}
static constexpr EAutomationTestFlags EFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01EBindings,"AnimeMMORPG.U01.E.BindingValidation",EFlags)
bool FU01EBindings::RunTest(const FString&)
{
    Controls::FSingleKeyCapture Capture;
    using Decision=Controls::ECaptureDecision;
    TestTrue(TEXT("Ctrl down waits for release"),Capture.Observe(EKeys::LeftControl,true,false)==Decision::Wait);
    TestTrue(TEXT("Ctrl plus key rejected before binding"),Capture.Observe(EKeys::H,true,true)==Decision::RejectChord);
    TestTrue(TEXT("Chord release cannot commit Ctrl"),Capture.Observe(EKeys::LeftControl,false,false)==Decision::Wait);
    TestTrue(TEXT("Plain Ctrl down waits"),Capture.Observe(EKeys::RightControl,true,false)==Decision::Wait);
    TestTrue(TEXT("Plain Ctrl up commits"),Capture.Observe(EKeys::RightControl,false,false)==Decision::Commit);
    Capture.Observe(EKeys::LeftControl,true,false);
    TestTrue(TEXT("Escape cancels deferred modifier"),Capture.Observe(EKeys::Escape,true,true)==Decision::Cancel);
    TestTrue(TEXT("Cancelled modifier release ignored"),Capture.Observe(EKeys::LeftControl,false,false)==Decision::Wait);
    Capture.Observe(EKeys::LeftControl,true,false);Capture.Reset();
    TestTrue(TEXT("Focus/capture reset drops deferred Ctrl"),Capture.Observe(EKeys::LeftControl,false,false)==Decision::Wait);
    TestTrue(TEXT("Keyboard key commits on down"),Capture.Observe(EKeys::H,true,false)==Decision::Commit);
    TestTrue(TEXT("Mouse with modifier rejected"),Capture.Observe(EKeys::MiddleMouseButton,true,true)==Decision::RejectChord);
    Controls::FPreferences P;
    for(int32 I=0;I<Controls::ControlCount;++I){TestTrue(TEXT("Single unused key accepted per action"),Controls::BindingError(P,I,EKeys::H).IsEmpty());TestFalse(TEXT("Other binding rejected without swapping"),Controls::BindingError(P,I,P.Keys[(I+1)%Controls::ControlCount]).IsEmpty());}
    TestTrue(TEXT("Right Ctrl canonical family"),Controls::BindingError(P,Controls::Sprint,EKeys::RightControl).IsEmpty());
    TestFalse(TEXT("Ctrl alias collision rejected"),Controls::BindingError(P,Controls::Jump,EKeys::RightControl).IsEmpty());
    const FKey Rejected[]={EKeys::Escape,EKeys::LeftShift,EKeys::RightShift,EKeys::LeftMouseButton,EKeys::RightMouseButton,EKeys::Q,EKeys::E,EKeys::R,EKeys::F,EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::X,EKeys::Tab,EKeys::I,EKeys::K,EKeys::M,EKeys::MouseX,EKeys::MouseScrollUp,EKeys::Gamepad_FaceButton_Bottom,FKey()};
    for(FKey Key:Rejected)TestFalse(*FString::Printf(TEXT("Reject %s"),*Key.ToString()),Controls::BindingError(P,Controls::Jump,Key).IsEmpty());
    TestFalse(TEXT("Reject chord"),Controls::BindingError(P,Controls::Jump,EKeys::H,true).IsEmpty());
    TestTrue(TEXT("Middle mouse valid"),Controls::BindingError(P,Controls::Jump,EKeys::MiddleMouseButton).IsEmpty());
    TestTrue(TEXT("Thumb mouse valid"),Controls::BindingError(P,Controls::Jump,EKeys::ThumbMouseButton).IsEmpty());
    auto* State=NewObject<UU01SettingsSubsystem>(NewObject<ULocalPlayer>(GEngine));
    TestFalse(TEXT("Rejected edit returns false"),State->Bind(Controls::Jump,EKeys::W));TestEqual(TEXT("Rejected edit preserves jump"),State->Get().Keys[Controls::Jump],EKeys::SpaceBar);
    TestFalse(TEXT("Rejected edit leaves clean"),State->IsDirty());
    TestTrue(TEXT("Apply valid edit"),State->Bind(Controls::Jump,EKeys::H));TestTrue(TEXT("Edit marks dirty"),State->IsDirty());
    State->SetSensitivity(2.5f);State->SetInvertY(true);State->SetRightShoulder(false);
    TestEqual(TEXT("Sensitivity live"),State->Get().Sensitivity,2.5f);State->RestoreDefaults();
    TestEqual(TEXT("Restore bindings"),State->Get().Keys[Controls::Jump],EKeys::SpaceBar);TestEqual(TEXT("Restore sensitivity"),State->Get().Sensitivity,1.f);
    TestFalse(TEXT("Restore invert"),State->Get().bInvertY);TestTrue(TEXT("Restore shoulder"),State->Get().bRightShoulder);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01ERecovery,"AnimeMMORPG.U01.E.PartialRecovery",EFlags)
bool FU01ERecovery::RunTest(const FString&)
{
    Controls::FPreferences P,Out;P.Keys[Controls::Jump]=EKeys::H;P.Sensitivity=2.25f;P.bInvertY=true;P.bRightShoulder=false;
    TestTrue(TEXT("Clean decode"),Controls::DecodePreferences(Controls::EncodePreferences(P),Out).IsEmpty());TestEqual(TEXT("Keep clean binding"),Out.Keys[Controls::Jump],EKeys::H);
    TSharedPtr<FJsonObject> Json;FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Controls::EncodePreferences(P)),Json);
    Json->SetStringField(TEXT("sensitivity"),TEXT("2.5"));
    auto Bindings=Json->GetObjectField(TEXT("bindings"));Bindings->SetStringField(TEXT("Forward"),TEXT("Q"));Bindings->SetStringField(TEXT("Backward"),TEXT("W"));
    Bindings->SetStringField(TEXT("Left"),TEXT("J"));Bindings->SetStringField(TEXT("Right"),TEXT("J"));Bindings->SetStringField(TEXT("Interact"),TEXT("J"));
    FString Text;FJsonSerializer::Serialize(Json.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    const FString Notice=Controls::DecodePreferences(Text,Out);TestFalse(TEXT("Recovery reports fields"),Notice.IsEmpty());
    TestEqual(TEXT("Wrong type number restored"),Out.Sensitivity,1.f);TestTrue(TEXT("Keep valid invert"),Out.bInvertY);TestFalse(TEXT("Keep valid shoulder"),Out.bRightShoulder);
    TestEqual(TEXT("Keep independent valid jump"),Out.Keys[Controls::Jump],EKeys::H);
    TestEqual(TEXT("Conflict closure restored forward"),Out.Keys[AnimeMMORPG::U01::Forward],EKeys::W);TestEqual(TEXT("Conflict closure restored backward"),Out.Keys[Controls::Backward],EKeys::S);
    TestEqual(TEXT("Triple conflict third restored"),Out.Keys[Controls::Interact],EKeys::G);
    for(int32 I=0;I<Controls::ControlCount;++I)TestTrue(TEXT("Recovery leaves no duplicate/reserved binding"),Controls::BindingError(Out,I,Out.Keys[I]).IsEmpty());
    TestFalse(TEXT("Malformed JSON feedback"),Controls::DecodePreferences(TEXT("broken"),Out).IsEmpty());
    TestEqual(TEXT("Malformed resets defaults"),Out.Keys[Controls::Jump],EKeys::SpaceBar);
    TestFalse(TEXT("Unsupported version feedback"),Controls::DecodePreferences(TEXT("{\"version\":2}"),Out).IsEmpty());
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01EStorage,"AnimeMMORPG.U01.E.SaveAndFailure",EFlags)
bool FU01EStorage::RunTest(const FString&)
{
    const FString Slot=TEXT("U01E_Test_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    const FString Path=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("SaveGames"),Slot+TEXT(".sav"));
    Controls::FPreferences P,Out;FString Message;P.Keys[AnimeMMORPG::U01::Forward]=EKeys::H;P.Sensitivity=2;P.bInvertY=true;P.bRightShoulder=false;
    TestTrue(TEXT("Missing file defaults"),Controls::ReadPreferences(Slot,0,Out,Message));TestFalse(TEXT("Load missing does not create file"),UGameplayStatics::DoesSaveGameExist(Slot,0));
    TestTrue(TEXT("Actual SaveGame write"),Controls::WritePreferences(Slot,0,P,Message));TestTrue(TEXT("Actual SaveGame read"),Controls::ReadPreferences(Slot,0,Out,Message));
    TestEqual(TEXT("Binding persists"),Out.Keys[AnimeMMORPG::U01::Forward],EKeys::H);TestEqual(TEXT("Sensitivity persists"),Out.Sensitivity,2.f);TestTrue(TEXT("Invert persists"),Out.bInvertY);TestFalse(TEXT("Shoulder persists"),Out.bRightShoulder);
    auto* Corrupt=NewObject<UU01ControlSave>();Corrupt->Payload=TEXT("{\"version\":1,\"sensitivity\":2,\"invertY\":true,\"rightShoulder\":false,\"bindings\":{\"Jump\":\"H\"}}");
    TestTrue(TEXT("Write partial fixture"),StoreFixture(Corrupt,Slot));
    TArray<uint8> Before,After;FFileHelper::LoadFileToArray(Before,*Path);
    TestFalse(TEXT("Partial file reports recovery"),Controls::ReadPreferences(Slot,0,Out,Message));TestEqual(TEXT("Partial valid jump kept"),Out.Keys[Controls::Jump],EKeys::H);
    FFileHelper::LoadFileToArray(After,*Path);TestTrue(TEXT("Loading never overwrites damaged storage"),Before==After);
    Corrupt->Version=99;TestTrue(TEXT("Write future schema fixture"),StoreFixture(Corrupt,Slot));
    TestFalse(TEXT("Future SaveGame rejected"),Controls::ReadPreferences(Slot,0,Out,Message));
    TestTrue(TEXT("Write clean envelope before damage"),Controls::WritePreferences(Slot,0,P,Message));
    TArray<uint8> Good;UGameplayStatics::LoadDataFromSlot(Good,Slot,0);
    TArray<TArray<uint8>> BadCases={{},{0x55},{0x55,0x30,0x31,0x45}};
    TArray<uint8> Truncated=Good;Truncated.SetNum(Good.Num()-1);BadCases.Add(Truncated);
    TArray<uint8> Flipped=Good;Flipped.Last()^=0x40;BadCases.Add(Flipped);
    TArray<uint8> Oversized;Oversized.SetNumZeroed(65537);BadCases.Add(Oversized);
    for(const auto& Bad:BadCases)
    {
        TestTrue(TEXT("Store malformed binary fixture"),FFileHelper::SaveArrayToFile(Bad,*Path));
        TestFalse(TEXT("Malformed binary safely rejected"),Controls::ReadPreferences(Slot,0,Out,Message));
        TestFalse(TEXT("Malformed binary reports recovery"),Message.IsEmpty());
        TestEqual(TEXT("Binary damage uses default binding"),Out.Keys[AnimeMMORPG::U01::Forward],EKeys::W);
        TArray<uint8> Unchanged;UGameplayStatics::LoadDataFromSlot(Unchanged,Slot,0);
        TestTrue(TEXT("Malformed binary never overwritten on load"),Bad==Unchanged);
    }
    TestTrue(TEXT("Delete fixture save"),UGameplayStatics::DeleteGameInSlot(Slot,0));
    TestTrue(TEXT("Create deterministic write blocker at test-only save path"),IFileManager::Get().MakeDirectory(*Path,true));
    TestFalse(TEXT("Filesystem write failure propagated"),Controls::WritePreferences(Slot,0,P,Message));TestFalse(TEXT("Failure visible"),Message.IsEmpty());
    IFileManager::Get().DeleteDirectory(*Path,false,false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01ELocalMapping,"AnimeMMORPG.U01.E.LocalMappingIsolation",EFlags)
bool FU01ELocalMapping::RunTest(const FString&)
{
    auto* Template=NewObject<UInputMappingContext>();TArray<const UInputAction*> Actions;
    Controls::FPreferences Defaults,A;A.Keys[AnimeMMORPG::U01::Forward]=EKeys::H;A.Keys[Controls::Jump]=EKeys::ThumbMouseButton;
    for(int32 I=0;I<Controls::ControlCount;++I){auto* Action=NewObject<UInputAction>();Actions.Add(Action);Template->MapKey(Action,Defaults.Keys[I]);}
    auto* Look=NewObject<UInputAction>();Template->MapKey(Look,EKeys::MouseX);
    auto* PlayerA=NewObject<ULocalPlayer>(GEngine);auto* PlayerB=NewObject<ULocalPlayer>(GEngine);
    auto* ContextA=Controls::MakeLocalMapping(PlayerA,Template,A,Actions);auto* ContextB=Controls::MakeLocalMapping(PlayerB,Template,Defaults,Actions);
    TestNotNull(TEXT("Local A context"),ContextA);TestNotNull(TEXT("Local B context"),ContextB);if(!ContextA||!ContextB)return false;
    TestTrue(TEXT("Separate object and owner"),ContextA!=ContextB&&ContextA!=Template&&ContextA->GetOuter()==PlayerA&&ContextB->GetOuter()==PlayerB);
    auto Has=[](const UInputMappingContext* C,const UInputAction* Action,FKey Key){for(const auto& Map:C->GetMappings())if(Map.Action==Action&&Map.Key==Key)return true;return false;};
    TestTrue(TEXT("A rebound key active"),Has(ContextA,Actions[AnimeMMORPG::U01::Forward],EKeys::H));TestFalse(TEXT("A old key removed"),Has(ContextA,Actions[AnimeMMORPG::U01::Forward],EKeys::W));
    TestTrue(TEXT("B unchanged"),Has(ContextB,Actions[AnimeMMORPG::U01::Forward],EKeys::W));TestFalse(TEXT("B never receives A binding"),Has(ContextB,Actions[AnimeMMORPG::U01::Forward],EKeys::H));
    TestTrue(TEXT("Template unchanged"),Has(Template,Actions[AnimeMMORPG::U01::Forward],EKeys::W));TestFalse(TEXT("Template not mutated"),Has(Template,Actions[AnimeMMORPG::U01::Forward],EKeys::H));
    TestTrue(TEXT("Fixed mouse axis preserved"),Has(ContextA,Look,EKeys::MouseX));TestTrue(TEXT("Right Ctrl default alias mapped"),Has(ContextA,Actions[Controls::Sprint],EKeys::RightControl));
    TestTrue(TEXT("Mouse rebind mapped"),Has(ContextA,Actions[Controls::Jump],EKeys::ThumbMouseButton));
    Controls::FReleaseGate Gate;Gate.Down(EKeys::H,false);Gate.Down(EKeys::ThumbMouseButton,false);Gate.Lock();
    TestFalse(TEXT("Rebound movement quarantined"),Gate.Allows(EKeys::H));TestFalse(TEXT("Rebound mouse jump quarantined"),Gate.Allows(EKeys::ThumbMouseButton));
    Gate.Up(EKeys::H);TestTrue(TEXT("Only physical release rearms movement"),Gate.Allows(EKeys::H));TestFalse(TEXT("Other mouse remains blocked"),Gate.Allows(EKeys::ThumbMouseButton));
    Gate.Up(EKeys::ThumbMouseButton);TestTrue(TEXT("Mouse release rearms jump"),Gate.Allows(EKeys::ThumbMouseButton));
    return true;
}
}
#endif
