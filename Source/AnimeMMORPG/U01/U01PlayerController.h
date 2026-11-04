#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "U01ControlPolicy.h"
#include "U01Settings.h"
#include "U01PlayerController.generated.h"

class UInputAction;
class UInputMappingContext;
class UU01Menu;
class IInputProcessor;
struct FInputActionValue;

UENUM(BlueprintType)
enum class EU01ControlState : uint8 { Playing, Menu, AwaitingResume };

UCLASS()
class ANIMEMMORPG_API AU01PlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void SetupInputComponent() override;
    virtual void PlayerTick(float DeltaTime) override;
    virtual void UpdateCameraManager(float DeltaSeconds) override;

    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputMappingContext> MappingContext;
    // W,S,A,D order; one action per direction leaves rebind local to E.
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TArray<TObjectPtr<UInputAction>> DirectionActions;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> MouseXAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> MouseYAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> JumpAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> SprintAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> ShoulderAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> MenuAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|Input") TObjectPtr<UInputAction> InteractAction;
    UPROPERTY(EditDefaultsOnly, Category="U01|UI") TSubclassOf<UU01Menu> MenuClass;
    UPROPERTY(BlueprintReadOnly, Category="U01") EU01ControlState ControlState = EU01ControlState::Playing;

    UFUNCTION(BlueprintCallable, Category="U01") void ResumePlaying();
    UFUNCTION(BlueprintCallable, Category="U01") void ReturnToBoot();
    UFUNCTION(BlueprintCallable, Category="U01") void QuitToDesktop();
    UFUNCTION(Exec) void U01Metrics();
    UFUNCTION(Exec) void U01FixtureReset(const FString& Station);
    UFUNCTION(Exec) void U01FixtureLock(const FString& Reason, bool bEnabled);
    UFUNCTION(BlueprintCallable, Category="U01|Lab") void ResetRunwayFixture();
    UFUNCTION(BlueprintCallable, Category="U01|Lab") void NextFixtureStation();
    UFUNCTION(BlueprintCallable, Category="U01|Lab") void ToggleInteractingFixture();
    UFUNCTION(BlueprintCallable, Category="U01|Lab") void ToggleDefeatedFixture();
    FString GetFixtureStatus() const;
    bool HasTerrainFixtures() const;
    FString GetMetricsJson() const;
    bool ObservePhysicalKey(FKey Key, bool bDown, bool bChord=false);
    bool IsGameWindowActive() const;
    const AnimeMMORPG::U01::FPreferences& GetPreferences() const;
    void BeginRebind(int32 Action);
    void CancelRebind();
    int32 GetPendingRebind() const {return PendingRebind;}
    FString GetSettingsStatus() const;
    bool SaveSettings(bool bExplicit=false);
    void ChangeSensitivity(float Value);
    void ChangeInvertY(bool Value);
    void ChangeRightShoulder(bool Value);
    void RestoreControlDefaults();
    void OpenControls();
private:
    UPROPERTY(Transient) TObjectPtr<UU01Menu> MenuWidget;
    UPROPERTY(Transient) TObjectPtr<UU01SettingsSubsystem> Settings;
    UPROPERTY(Transient) TObjectPtr<UInputMappingContext> LocalMapping;
    TWeakObjectPtr<APawn> PresentationPawn;
    TSet<FKey> ObservedKeys;
    int32 PendingRebind=INDEX_NONE;
    TSharedPtr<IInputProcessor> PhysicalInputObserver;
    AnimeMMORPG::U01::FReleaseGate ReleaseGate;
    AnimeMMORPG::U01::FSingleKeyCapture KeyCapture;
    FDelegateHandle ActivationHandle;
    bool bWasWindowActive = true;
    bool bMotorLocked = false;
    bool bTrace = false;
    float TraceElapsed = 0;
    float ProbeSeconds = 0;
    FString RunId;
    void ActivationChanged(bool bActive);
    void ReconcilePhysicalReleases();
    void QuarantineHeldKeys();
    bool RebuildLocalMapping();
    void ApplyPreferences();
    FKey ControlKey(int32 Action) const;
    bool AcceptsAction(int32 Action,bool bRequireMotor=true) const;
    bool IsMotorKey(FKey Key) const;
    void LockControls(EU01ControlState NewState, const TCHAR* Reason);
    void ApplyPlayingInputMode();
    void MoveDirection(const FInputActionValue& Value, int32 DirectionIndex);
    void MouseX(const FInputActionValue& Value);
    void MouseY(const FInputActionValue& Value);
    void JumpPressed();
    void Sprint(const FInputActionValue& Value);
    void SprintReleased();
    void ShoulderPressed();
    void MenuPressed();
    void InteractPressed();
    bool Accepts(FKey Key) const;
    bool FixtureAllowed() const;
    int32 FixtureStationIndex = 0;
    FString FixtureStation = TEXT("Runway");
};
