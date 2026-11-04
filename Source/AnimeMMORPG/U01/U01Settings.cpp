#include "U01Settings.h"
#include "Engine/LocalPlayer.h"
#include "Kismet/GameplayStatics.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

namespace AnimeMMORPG::U01
{
static const TCHAR* Names[]={TEXT("Forward"),TEXT("Backward"),TEXT("Left"),TEXT("Right"),TEXT("Jump"),TEXT("Sprint"),TEXT("Shoulder"),TEXT("Interact")};
FPreferences::FPreferences():Keys({EKeys::W,EKeys::S,EKeys::A,EKeys::D,EKeys::SpaceBar,EKeys::LeftControl,EKeys::V,EKeys::G}){}
FKey CanonicalKey(FKey Key) {return Key==EKeys::RightControl?EKeys::LeftControl:Key;}
TArray<FKey> PhysicalKeys(FKey Binding) {return CanonicalKey(Binding)==EKeys::LeftControl?TArray<FKey>{EKeys::LeftControl,EKeys::RightControl}:TArray<FKey>{Binding};}
bool AllowedBinding(FKey Key,FString& Reason)
{
    const FKey Reserved[]={EKeys::Escape,EKeys::LeftShift,EKeys::RightShift,EKeys::LeftAlt,EKeys::RightAlt,EKeys::LeftCommand,EKeys::RightCommand,
        EKeys::LeftMouseButton,EKeys::RightMouseButton,EKeys::Q,EKeys::E,EKeys::R,EKeys::F,EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,
        EKeys::X,EKeys::Tab,EKeys::I,EKeys::K,EKeys::M,EKeys::Tilde,EKeys::AnyKey};
    for(FKey Entry:Reserved)if(Key==Entry){Reason=TEXT("Phím dành riêng cho menu/combat/hệ thống.");return false;}
    if(!Key.IsValid()||Key.IsGamepadKey()||Key.IsTouch()||Key.IsAnalog()||Key==EKeys::MouseScrollUp||Key==EKeys::MouseScrollDown)
    {Reason=TEXT("Chỉ nhận một phím bàn phím hoặc nút chuột, không nhận trục/cuộn/tay cầm.");return false;}
    if(Key.IsMouseButton() && Key!=EKeys::MiddleMouseButton&&Key!=EKeys::ThumbMouseButton&&Key!=EKeys::ThumbMouseButton2)
    {Reason=TEXT("Nút chuột này được dành riêng.");return false;}
    Reason.Empty();return true;
}
FString BindingError(const FPreferences& Data,int32 Action,FKey Key,bool bChord)
{
    if(Action<0||Action>=ControlCount)return TEXT("Hành động không hợp lệ.");
    if(bChord)return TEXT("Chỉ nhận một phím/nút, không nhận tổ hợp.");
    FString Reason;if(!AllowedBinding(Key,Reason))return Reason;
    Key=CanonicalKey(Key);
    for(int I=0;I<Data.Keys.Num();++I)if(I!=Action && CanonicalKey(Data.Keys[I])==Key)return FString::Printf(TEXT("Phím đã dùng cho %s; không tự đổi chỗ."),Names[I]);
    return FString();
}
FString EncodePreferences(const FPreferences& Data)
{
    auto Json=MakeShared<FJsonObject>();Json->SetNumberField(TEXT("version"),1);Json->SetNumberField(TEXT("sensitivity"),Data.Sensitivity);
    Json->SetBoolField(TEXT("invertY"),Data.bInvertY);Json->SetBoolField(TEXT("rightShoulder"),Data.bRightShoulder);
    auto Bindings=MakeShared<FJsonObject>();for(int I=0;I<ControlCount;++I)Bindings->SetStringField(Names[I],Data.Keys[I].ToString());
    Json->SetObjectField(TEXT("bindings"),Bindings);FString Text;FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));return Text;
}
FString DecodePreferences(const FString& Text,FPreferences& Out)
{
    Out=FPreferences();TSharedPtr<FJsonObject> Json;
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json)||!Json.IsValid())return TEXT("File thiết lập lỗi JSON: dùng mặc định, chưa ghi đè file.");
    double Version=0;if(!Json->HasTypedField<EJson::Number>(TEXT("version"))||!Json->TryGetNumberField(TEXT("version"),Version)||Version!=1)return TEXT("Version thiết lập chưa hỗ trợ: dùng mặc định, chưa ghi đè file.");
    TArray<FString> Restored;double Sensitivity=0;bool Flag=false;
    if(Json->HasTypedField<EJson::Number>(TEXT("sensitivity"))&&Json->TryGetNumberField(TEXT("sensitivity"),Sensitivity)&&FMath::IsFinite(Sensitivity)&&Sensitivity>=.1&&Sensitivity<=3)Out.Sensitivity=Sensitivity;
    else Restored.Add(TEXT("độ nhạy"));
    if(Json->HasTypedField<EJson::Boolean>(TEXT("invertY"))&&Json->TryGetBoolField(TEXT("invertY"),Flag))Out.bInvertY=Flag;else Restored.Add(TEXT("đảo Y"));
    if(Json->HasTypedField<EJson::Boolean>(TEXT("rightShoulder"))&&Json->TryGetBoolField(TEXT("rightShoulder"),Flag))Out.bRightShoulder=Flag;else Restored.Add(TEXT("vai mặc định"));
    const TSharedPtr<FJsonObject>* Bindings=nullptr;Json->TryGetObjectField(TEXT("bindings"),Bindings);
    bool Recover[ControlCount]={};FPreferences Defaults;
    for(int I=0;I<ControlCount;++I)
    {
        FString Name,Why;
        if(!Bindings||!Bindings->IsValid()||!(*Bindings)->HasTypedField<EJson::String>(Names[I])||!(*Bindings)->TryGetStringField(Names[I],Name)||!AllowedBinding(FKey(*Name),Why))Recover[I]=true;
        else Out.Keys[I]=CanonicalKey(FKey(*Name));
    }
    bool InitiallyValid[ControlCount];for(int I=0;I<ControlCount;++I)InitiallyValid[I]=!Recover[I];
    for(int I=0;I<ControlCount;++I)for(int J=I+1;J<ControlCount;++J)
        if(InitiallyValid[I]&&InitiallyValid[J]&&Out.Keys[I]==Out.Keys[J]){Recover[I]=Recover[J]=true;}
    // Recover the entire conflict closure when a valid binding occupies the
    // default of a damaged binding. Never introduce a new duplicate by recovery.
    bool Changed;
    do{Changed=false;for(int I=0;I<ControlCount;++I)if(Recover[I])for(int J=0;J<ControlCount;++J)
        if(!Recover[J]&&Defaults.Keys[I]==Out.Keys[J]){Recover[J]=true;Changed=true;}}while(Changed);
    for(int I=0;I<ControlCount;++I)if(Recover[I]){Out.Keys[I]=Defaults.Keys[I];Restored.Add(Names[I]);}
    return Restored.Num()?TEXT("Đã khôi phục: ")+FString::Join(Restored,TEXT(", "))+TEXT(". Phần hợp lệ được giữ; chưa ghi đè file."):FString();
}
bool ReadPreferences(const FString& Slot,int32 User,FPreferences& Out,FString& Message)
{
    Out=FPreferences();
    if(!UGameplayStatics::DoesSaveGameExist(Slot,User)){Message=TEXT("Chưa có file: dùng mặc định.");return true;}
    auto* Save=Cast<UU01ControlSave>(UGameplayStatics::LoadGameFromSlot(Slot,User));
    if(!Save){Message=TEXT("Không đọc được file thiết lập: dùng mặc định; chưa ghi đè file.");return false;}
    if(Save->Version!=1){Message=TEXT("Version SaveGame chưa hỗ trợ: dùng mặc định; chưa ghi đè file.");return false;}
    Message=DecodePreferences(Save->Payload,Out);return Message.IsEmpty();
}
bool WritePreferences(const FString& Slot,int32 User,const FPreferences& Data,FString& Message)
{
    auto* Save=NewObject<UU01ControlSave>();Save->Payload=EncodePreferences(Data);
    const bool Success=UGameplayStatics::SaveGameToSlot(Save,Slot,User);
    Message=Success?TEXT("Đã lưu thiết lập local."):TEXT("Lưu thất bại. Thiết lập đang dùng chưa được lưu; hãy thử Save lại.");return Success;
}
UInputMappingContext* MakeLocalMapping(UObject* Owner,const UInputMappingContext* Template,const FPreferences& Data,const TArray<const UInputAction*>& Actions)
{
    if(!Owner||!Template||Actions.Num()!=ControlCount)return nullptr;
    for(auto* Action:Actions)if(!Action)return nullptr;
    auto* Context=DuplicateObject<UInputMappingContext>(Template,Owner);
    for(int I=0;I<ControlCount;++I)
    {
        Context->UnmapAllKeysFromAction(Actions[I]);
        for(FKey Key:PhysicalKeys(Data.Keys[I]))Context->MapKey(Actions[I],Key);
    }
    return Context;
}
}

void UU01SettingsSubsystem::EnsureLoaded()
{
    if(bLoaded)return;bLoaded=true;
    AnimeMMORPG::U01::ReadPreferences(GetSlot(),0,Preferences,Status);bDirty=false;
}
FString UU01SettingsSubsystem::GetSlot() const
{
    return FString::Printf(TEXT("U01Controls_Player%d"),GetLocalPlayer()?FMath::Max(0,GetLocalPlayer()->GetControllerId()):0);
}
bool UU01SettingsSubsystem::Save(bool bExplicit)
{
    if(!bDirty&&!bExplicit)return true;
    const bool Success=AnimeMMORPG::U01::WritePreferences(GetSlot(),0,Preferences,Status);
    if(Success)bDirty=false;return Success;
}
bool UU01SettingsSubsystem::Bind(int32 Action,FKey Key,bool bChord)
{
    Status=AnimeMMORPG::U01::BindingError(Preferences,Action,Key,bChord);
    if(!Status.IsEmpty())return false;
    Key=AnimeMMORPG::U01::CanonicalKey(Key);
    if(Preferences.Keys[Action]!=Key){Preferences.Keys[Action]=Key;bDirty=true;}
    Status=TEXT("Đã áp dụng phím. Save hoặc Resume để lưu.");return true;
}
void UU01SettingsSubsystem::SetSensitivity(float Value)
{
    if(FMath::IsFinite(Value)&&Value>=.1f&&Value<=3.f&&Value!=Preferences.Sensitivity){Preferences.Sensitivity=Value;bDirty=true;Status=TEXT("Độ nhạy đã áp dụng; thả thanh để lưu.");}
}
void UU01SettingsSubsystem::SetInvertY(bool Value){if(Value!=Preferences.bInvertY){Preferences.bInvertY=Value;bDirty=true;Status=TEXT("Đã áp dụng đảo Y; Save hoặc Resume để lưu.");}}
void UU01SettingsSubsystem::SetRightShoulder(bool Value){if(Value!=Preferences.bRightShoulder){Preferences.bRightShoulder=Value;bDirty=true;Status=TEXT("Đã áp dụng vai mặc định; Save hoặc Resume để lưu.");}}
void UU01SettingsSubsystem::RestoreDefaults(){Preferences=AnimeMMORPG::U01::FPreferences();bDirty=true;Status=TEXT("Đã áp dụng mặc định; Save hoặc Resume để lưu.");}
