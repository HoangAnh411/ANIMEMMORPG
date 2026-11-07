#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/LocalPlayerSubsystem.h"
#include "InputCoreTypes.h"
#include "U01Settings.generated.h"

class UInputMappingContext;
class UInputAction;

namespace AnimeMMORPG::U01
{
enum EControl : int32 { Forward, Backward, Left, Right, Jump, Sprint, Shoulder, Interact, Attack, Guard, Dodge, EscapeCC, SkillQ, SkillE, Target, ControlCount };
struct FPreferences
{
    FPreferences();
    TArray<FKey> Keys;
    float Sensitivity=1;
    bool bInvertY=false;
    bool bRightShoulder=true;
};
ANIMEMMORPG_API FKey CanonicalKey(FKey Key);
ANIMEMMORPG_API TArray<FKey> PhysicalKeys(FKey Binding);
ANIMEMMORPG_API bool AllowedBinding(FKey Key,FString& Reason);
ANIMEMMORPG_API FString BindingError(const FPreferences& Data,int32 Action,FKey Key,bool bChord=false);
ANIMEMMORPG_API FString EncodePreferences(const FPreferences& Data);
// Returns recovery messages; unsupported schema uses defaults, never writes storage.
ANIMEMMORPG_API FString DecodePreferences(const FString& Json,FPreferences& Out);
ANIMEMMORPG_API bool ReadPreferences(const FString& Slot,int32 User,FPreferences& Out,FString& Message);
ANIMEMMORPG_API bool WritePreferences(const FString& Slot,int32 User,const FPreferences& Data,FString& Message);
ANIMEMMORPG_API UInputMappingContext* MakeLocalMapping(UObject* Owner,const UInputMappingContext* Template,
    const FPreferences& Data,const TArray<const UInputAction*>& Actions);
}

UCLASS()
class ANIMEMMORPG_API UU01ControlSave : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(SaveGame) int32 Version=1;
    // Versioned JSON allows partial field/type recovery instead of discarding all preferences.
    UPROPERTY(SaveGame) FString Payload;
};

UCLASS()
class ANIMEMMORPG_API UU01SettingsSubsystem : public ULocalPlayerSubsystem
{
    GENERATED_BODY()
public:
    void EnsureLoaded();
    bool Save(bool bExplicit=false);
    const AnimeMMORPG::U01::FPreferences& Get() const {return Preferences;}
    bool Bind(int32 Action,FKey Key,bool bChord=false);
    void SetSensitivity(float Value);
    void SetInvertY(bool Value);
    void SetRightShoulder(bool Value);
    void RestoreDefaults();
    FString GetStatus() const {return Status;}
    void SetNotice(const FString& Text) {Status=Text;}
    bool IsDirty() const {return bDirty;}
    FString GetSlot() const;
private:
    AnimeMMORPG::U01::FPreferences Preferences;
    FString Status;
    bool bLoaded=false;
    bool bDirty=false;
};
