#include "U01PlayerController.h"
#include "U01Character.h"
#include "U01Menu.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Widgets/SViewport.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/FileManager.h"

DEFINE_LOG_CATEGORY_STATIC(LogU01Control, Log, All);

namespace
{
const FKey DirectionKeys[] = { EKeys::W, EKeys::S, EKeys::A, EKeys::D };
class FU01PhysicalObserver final : public IInputProcessor
{
public:
    explicit FU01PhysicalObserver(AU01PlayerController* InPC) : PC(InPC) {}
    virtual void Tick(float, FSlateApplication&, TSharedRef<ICursor>) override {}
    virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event) override
    {
        if (PC.IsValid()) PC->ObservePhysicalKey(Event.GetKey(), true);
        return false;
    }
    virtual bool HandleKeyUpEvent(FSlateApplication&, const FKeyEvent& Event) override
    {
        if (PC.IsValid()) PC->ObservePhysicalKey(Event.GetKey(), false);
        return false;
    }
private:
    TWeakObjectPtr<AU01PlayerController> PC;
};
}

void AU01PlayerController::BeginPlay()
{
    Super::BeginPlay();
    // Remote server controllers must not create a widget, touch Slate, capture a mouse or install a mapping.
    if (!IsLocalPlayerController() || GetNetMode() == NM_DedicatedServer) return;
    RunId = FGuid::NewGuid().ToString(EGuidFormats::Digits);
    bTrace = FParse::Param(FCommandLine::Get(), TEXT("U01Trace"));
    FParse::Value(FCommandLine::Get(), TEXT("U01ProbeSeconds="), ProbeSeconds);
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
        if (MappingContext) Subsystem->AddMappingContext(MappingContext, 0);
    if (MenuClass) MenuWidget = CreateWidget<UU01Menu>(this, MenuClass);
    if (FSlateApplication::IsInitialized())
    {
        PhysicalInputObserver = MakeShared<FU01PhysicalObserver>(this);
        FSlateApplication::Get().RegisterInputPreProcessor(PhysicalInputObserver, 0);
        ActivationHandle = FSlateApplication::Get().OnApplicationActivationStateChanged().AddUObject(this, &AU01PlayerController::ActivationChanged);
    }
    PlayerCameraManager->ViewPitchMin = -70;
    PlayerCameraManager->ViewPitchMax = 60;
    bWasWindowActive = IsGameWindowActive();
    ApplyPlayingInputMode();
    if (!bWasWindowActive) LockControls(EU01ControlState::AwaitingResume, TEXT("InitialWindowInactive"));
    UE_LOG(LogU01Control, Display, TEXT("Begin local PID=%u world=%s net=%d pawn=%s"),
        FPlatformProcess::GetCurrentProcessId(), *GetWorld()->GetPathName(), int32(GetNetMode()), *GetNameSafe(GetPawn()));
}

void AU01PlayerController::EndPlay(const EEndPlayReason::Type Reason)
{
    if (IsLocalPlayerController())
    {
        if (MenuWidget) { MenuWidget->RemoveFromParent(); MenuWidget = nullptr; }
        if (FSlateApplication::IsInitialized())
        {
            FSlateApplication::Get().UnregisterInputPreProcessor(PhysicalInputObserver);
            FSlateApplication::Get().OnApplicationActivationStateChanged().Remove(ActivationHandle);
        }
        PhysicalInputObserver.Reset();
        if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
            if (MappingContext) Subsystem->RemoveMappingContext(MappingContext);
    }
    Super::EndPlay(Reason);
}

void AU01PlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    if (auto* Input = Cast<UEnhancedInputComponent>(InputComponent))
    {
        for (int32 Index = 0; Index < FMath::Min(4, DirectionActions.Num()); ++Index)
            if (DirectionActions[Index]) Input->BindAction(DirectionActions[Index], ETriggerEvent::Triggered, this, &AU01PlayerController::MoveDirection, Index);
        if (MouseXAction) Input->BindAction(MouseXAction, ETriggerEvent::Triggered, this, &AU01PlayerController::MouseX);
        if (MouseYAction) Input->BindAction(MouseYAction, ETriggerEvent::Triggered, this, &AU01PlayerController::MouseY);
        if (JumpAction) Input->BindAction(JumpAction, ETriggerEvent::Started, this, &AU01PlayerController::JumpPressed);
        if (ShoulderAction) Input->BindAction(ShoulderAction, ETriggerEvent::Started, this, &AU01PlayerController::ShoulderPressed);
        if (MenuAction) Input->BindAction(MenuAction, ETriggerEvent::Started, this, &AU01PlayerController::MenuPressed);
    }
}

bool AU01PlayerController::IsGameWindowActive() const
{
    if (!FSlateApplication::IsInitialized() || !FSlateApplication::Get().IsActive()) return false;
    const ULocalPlayer* LP = GetLocalPlayer();
    if (!LP || !LP->ViewportClient) return false;
    const TSharedPtr<SViewport> ViewportWidget = LP->ViewportClient->GetGameViewportWidget();
    if (!ViewportWidget.IsValid()) return false;
    const auto Window = FSlateApplication::Get().FindWidgetWindow(ViewportWidget.ToSharedRef());
    return Window.IsValid() && Window->IsActive();
}

void AU01PlayerController::ActivationChanged(bool bActive)
{
    if (!bActive) LockControls(EU01ControlState::AwaitingResume, TEXT("ApplicationDeactivated"));
    // Activation alone never calls ResumePlaying.
}

void AU01PlayerController::PlayerTick(float DeltaTime)
{
    Super::PlayerTick(DeltaTime);
    if (!IsLocalPlayerController() || GetNetMode() == NM_DedicatedServer) return;
    const bool bActive = IsGameWindowActive();
    if (bWasWindowActive && !bActive) LockControls(EU01ControlState::AwaitingResume, TEXT("WindowDeactivated"));
    bWasWindowActive = bActive;
    if (auto* Character = Cast<AU01Character>(GetPawn())) Character->SetControlLocked(bMotorLocked);
    TraceElapsed += DeltaTime;
    if (bTrace && TraceElapsed >= .2f)
    {
        UE_LOG(LogU01Control, Display, TEXT("Metrics %s"), *GetMetricsJson());
        TraceElapsed = 0;
    }
#if !UE_BUILD_SHIPPING
    // Headless/load smoke fixture only; never counted as real mouse/focus input.
    if (ProbeSeconds > 0 && GetWorld()->GetTimeSeconds() >= ProbeSeconds)
    {
        U01Metrics();
        ProbeSeconds = 0;
        UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
    }
#endif
}

void AU01PlayerController::ObservePhysicalKey(FKey Key, bool bDown)
{
    if (!IsGameWindowActive()) return; // Do not interpret another window's releases as re-arming gameplay.
    if (bDown) ReleaseGate.Down(Key, ControlState != EU01ControlState::Playing);
    else
    {
        ReleaseGate.Up(Key);
        if (Key == EKeys::SpaceBar) if (auto* Character = Cast<AU01Character>(GetPawn())) Character->StopJumping();
        UE_LOG(LogU01Control, Verbose, TEXT("PhysicalRelease/Rearm key=%s"), *Key.ToString());
    }
}

bool AU01PlayerController::Accepts(FKey Key) const
{
    return ControlState == EU01ControlState::Playing && !bMotorLocked && ReleaseGate.Allows(Key) && IsGameWindowActive();
}

void AU01PlayerController::MoveDirection(const FInputActionValue& Value, int32 DirectionIndex)
{
    if (DirectionIndex < 0 || DirectionIndex > 3 || !Value.Get<bool>() || !Accepts(DirectionKeys[DirectionIndex])) return;
    if (auto* Character = Cast<AU01Character>(GetPawn()))
    {
        const FRotationMatrix Yaw(FRotator(0, GetControlRotation().Yaw, 0));
        const FVector Direction = Yaw.GetUnitAxis(DirectionIndex < 2 ? EAxis::X : EAxis::Y);
        Character->AddMovementInput(Direction, (DirectionIndex == 1 || DirectionIndex == 2) ? -1 : 1);
    }
}

void AU01PlayerController::MouseX(const FInputActionValue& Value)
{
    if (ControlState == EU01ControlState::Playing && IsGameWindowActive())
        SetControlRotation(AnimeMMORPG::U01::ApplyMouse(GetControlRotation(), Value.Get<float>(), 0, 1));
}
void AU01PlayerController::MouseY(const FInputActionValue& Value)
{
    if (ControlState == EU01ControlState::Playing && IsGameWindowActive())
        SetControlRotation(AnimeMMORPG::U01::ApplyMouse(GetControlRotation(), 0, Value.Get<float>(), 1));
}
void AU01PlayerController::JumpPressed()
{
    if (Accepts(EKeys::SpaceBar)) if (auto* Character = Cast<AU01Character>(GetPawn())) Character->Jump();
}
void AU01PlayerController::ShoulderPressed()
{
    if (Accepts(EKeys::V)) if (auto* Character = Cast<AU01Character>(GetPawn())) Character->ToggleShoulder();
}
void AU01PlayerController::MenuPressed() { LockControls(EU01ControlState::Menu, TEXT("Escape")); }

void AU01PlayerController::LockControls(EU01ControlState NewState, const TCHAR* Reason)
{
    if (!IsLocalPlayerController()) return;
    ReleaseGate.Lock();
    ControlState = NewState;
    bMotorLocked = true;
    if (auto* Character = Cast<AU01Character>(GetPawn())) Character->SetControlLocked(true);
    FlushPressedKeys();
    bShowMouseCursor = true;
    if (MenuWidget)
    {
        if (!MenuWidget->IsInViewport()) MenuWidget->AddToPlayerScreen(100);
        SetInputMode(FInputModeUIOnly().SetWidgetToFocus(MenuWidget->TakeWidget()).SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock));
    }
    if (auto* LP = GetLocalPlayer()) if (auto* Viewport = LP->ViewportClient)
    {
        Viewport->SetMouseCaptureMode(EMouseCaptureMode::NoCapture);
        Viewport->SetMouseLockMode(EMouseLockMode::DoNotLock);
    }
    UE_LOG(LogU01Control, Display, TEXT("ControlLock state=%d reason=%s PID=%u pawn=%s world=%s"),
        int32(ControlState), Reason, FPlatformProcess::GetCurrentProcessId(), *GetNameSafe(GetPawn()), *GetWorld()->GetPathName());
}

void AU01PlayerController::ApplyPlayingInputMode()
{
    bShowMouseCursor = false;
    SetInputMode(FInputModeGameOnly().SetConsumeCaptureMouseDown(false));
    if (auto* LP = GetLocalPlayer()) if (auto* Viewport = LP->ViewportClient)
    {
        Viewport->SetMouseCaptureMode(EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown);
        Viewport->SetMouseLockMode(EMouseLockMode::LockOnCapture);
        Viewport->SetHideCursorDuringCapture(true);
    }
}

void AU01PlayerController::ResumePlaying()
{
    if (!IsLocalPlayerController() || !IsGameWindowActive()) return;
    if (MenuWidget) MenuWidget->RemoveFromParent();
    FlushPressedKeys();
    ControlState = EU01ControlState::Playing;
    bMotorLocked = false;
    if (auto* Character = Cast<AU01Character>(GetPawn())) Character->SetControlLocked(false);
    ApplyPlayingInputMode();
    UE_LOG(LogU01Control, Display, TEXT("Resume PID=%u world=%s held keys remain quarantined"), FPlatformProcess::GetCurrentProcessId(), *GetWorld()->GetPathName());
}
void AU01PlayerController::ReturnToBoot()
{
    if (IsLocalPlayerController()) UGameplayStatics::OpenLevel(this, TEXT("/Game/AnimeMMORPG/Maps/L_Boot"));
}
void AU01PlayerController::QuitToDesktop()
{
    if (IsLocalPlayerController()) UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}

FString AU01PlayerController::GetMetricsJson() const
{
    const AU01Character* Character = Cast<AU01Character>(GetPawn());
    const UWorld* World = Character ? Character->GetWorld() : nullptr;
    if (!World || (World->WorldType != EWorldType::Game && World->WorldType != EWorldType::PIE) || Character->GetController() != this)
        return TEXT("{\"error\":\"No unambiguous owned Game/PIE U01 pawn\"}");
    auto Json = MakeShared<FJsonObject>();
    FString SourceSHA;
    FParse::Value(FCommandLine::Get(), TEXT("U01SourceSHA="), SourceSHA);
    Json->SetStringField(TEXT("sourceSHA"), SourceSHA.IsEmpty() ? TEXT("UNSPECIFIED") : SourceSHA);
    Json->SetStringField(TEXT("runID"), RunId);
    Json->SetStringField(TEXT("utc"), FDateTime::UtcNow().ToIso8601());
    Json->SetNumberField(TEXT("pid"), FPlatformProcess::GetCurrentProcessId());
    Json->SetStringField(TEXT("project"), FPaths::ConvertRelativePathToFull(FPaths::GetProjectFilePath()));
    Json->SetStringField(TEXT("world"), World->GetPathName());
    Json->SetStringField(TEXT("map"), World->GetOutermost()->GetName());
    Json->SetNumberField(TEXT("worldType"), int32(World->WorldType));
    Json->SetNumberField(TEXT("netMode"), int32(World->GetNetMode()));
    if (const FWorldContext* Context = GEngine->GetWorldContextFromWorld(World)) Json->SetStringField(TEXT("worldContext"), Context->ContextHandle.ToString());
    Json->SetNumberField(TEXT("worldSeconds"), World->GetTimeSeconds());
    Json->SetStringField(TEXT("pawn"), Character->GetPathName());
    Json->SetStringField(TEXT("controller"), GetPathName());
    Json->SetStringField(TEXT("owner"), GetPathNameSafe(Character->GetOwner()));
    Json->SetNumberField(TEXT("localRole"), int32(Character->GetLocalRole()));
    Json->SetNumberField(TEXT("remoteRole"), int32(Character->GetRemoteRole()));
    Json->SetBoolField(TEXT("locallyControlled"), Character->IsLocallyControlled());
    Json->SetNumberField(TEXT("localPlayers"), GetGameInstance()->GetNumLocalPlayers());
    Json->SetStringField(TEXT("capsuleCenterWorldCm"), Character->GetActorLocation().ToString());
    Json->SetStringField(TEXT("velocityCmPerSec"), Character->GetVelocity().ToString());
    Json->SetStringField(TEXT("accelerationCmPerSec2"), Character->GetCharacterMovement()->GetCurrentAcceleration().ToString());
    Json->SetStringField(TEXT("pivotWorldCm"), Character->CameraPivot.ToString());
    Json->SetStringField(TEXT("desiredCameraWorldCm"), Character->DesiredCamera.ToString());
    Json->SetStringField(TEXT("resolvedCameraWorldCm"), PlayerCameraManager->GetCameraLocation().ToString());
    Json->SetStringField(TEXT("aimDirectionWorld"), PlayerCameraManager->GetCameraRotation().Vector().ToString());
    Json->SetStringField(TEXT("aimYawPitchDegrees"), GetControlRotation().ToString());
    Json->SetNumberField(TEXT("cameraPivotDistanceCm"), Character->CameraDistance);
    Json->SetNumberField(TEXT("shoulderOffsetCm"), Character->ShoulderOffset);
    Json->SetBoolField(TEXT("cameraHit"), Character->bCameraHit);
    Json->SetBoolField(TEXT("ownerMeshHidden"), Character->bOwnerMeshHidden);
    Json->SetBoolField(TEXT("windowActive"), IsGameWindowActive());
    Json->SetBoolField(TEXT("cursorVisible"), bShowMouseCursor);
    Json->SetBoolField(TEXT("motorLocked"), bMotorLocked);
    Json->SetNumberField(TEXT("controlState"), int32(ControlState));
    FString Result;
    FJsonSerializer::Serialize(Json, TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Result));
    return Result;
}

void AU01PlayerController::U01Metrics()
{
    const FString Json = GetMetricsJson();
    const FString Directory = FPaths::ProjectSavedDir() / TEXT("U01");
    IFileManager::Get().MakeDirectory(*Directory, true);
    const FString Path = Directory / (TEXT("Metrics-") + RunId + TEXT(".json"));
    if (!FFileHelper::SaveStringToFile(Json, *Path)) UE_LOG(LogU01Control, Error, TEXT("Metrics write failed: %s"), *Path);
    UE_LOG(LogU01Control, Display, TEXT("Metrics %s"), *Json);
}
