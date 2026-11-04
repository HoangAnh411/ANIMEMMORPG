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
#if PLATFORM_WINDOWS
#include "Windows/WindowsHWrapper.h"
#endif

DEFINE_LOG_CATEGORY_STATIC(LogU01Control, Log, All);

namespace
{
const FKey DirectionKeys[] = { EKeys::W, EKeys::S, EKeys::A, EKeys::D };
bool IsMotorKey(FKey Key)
{
    return Key == EKeys::W || Key == EKeys::S || Key == EKeys::A || Key == EKeys::D ||
        Key == EKeys::SpaceBar || Key == EKeys::LeftControl || Key == EKeys::RightControl;
}
const TCHAR* FixtureStations[] = { TEXT("Runway"), TEXT("Slope30"), TEXT("Slope44"), TEXT("Slope45"), TEXT("Slope46"), TEXT("Slope60"),
    TEXT("Step20"), TEXT("Step40"), TEXT("Step60"), TEXT("Ceiling180"), TEXT("Ceiling260"), TEXT("Ledge"), TEXT("Corridor120") };
class FU01PhysicalObserver final : public IInputProcessor
{
public:
    explicit FU01PhysicalObserver(AU01PlayerController* InPC) : PC(InPC) {}
    virtual void Tick(float, FSlateApplication&, TSharedRef<ICursor>) override {}
    virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event) override
    {
        if (PC.IsValid() && !Event.IsRepeat()) PC->ObservePhysicalKey(Event.GetKey(), true);
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
        if (SprintAction)
        {
            Input->BindAction(SprintAction, ETriggerEvent::Triggered, this, &AU01PlayerController::Sprint);
            Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &AU01PlayerController::SprintReleased);
            Input->BindAction(SprintAction, ETriggerEvent::Canceled, this, &AU01PlayerController::SprintReleased);
        }
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
    if (bActive) ReconcilePhysicalReleases();
    if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn())) ControlledCharacter->SetControlLocked(bMotorLocked);
}

void AU01PlayerController::UpdateCameraManager(float DeltaSeconds)
{
    Super::UpdateCameraManager(DeltaSeconds);
    if (!IsLocalPlayerController() || GetNetMode() == NM_DedicatedServer) return;
    // Sample after PCM has resolved this frame's view, never its previous-frame cache.
    TraceElapsed += DeltaSeconds;
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

void AU01PlayerController::ReconcilePhysicalReleases()
{
#if PLATFORM_WINDOWS
    // Enhanced Input/Slate may flush or miss KeyUp while inactive. Read the actual OS
    // high bit, never the flushed PlayerInput state. Returning focus alone is not a release.
    const TPair<FKey, int32> Keys[] = {
        {EKeys::W, 'W'}, {EKeys::S, 'S'}, {EKeys::A, 'A'}, {EKeys::D, 'D'},
        {EKeys::SpaceBar, VK_SPACE}, {EKeys::LeftControl, VK_LCONTROL},
        {EKeys::RightControl, VK_RCONTROL}, {EKeys::V, 'V'}, {EKeys::G, 'G'}, {EKeys::Escape, VK_ESCAPE}
    };
    for (const auto& Entry : Keys)
        if ((::GetAsyncKeyState(Entry.Value) & 0x8000) == 0)
        {
            ReleaseGate.Up(Entry.Key);
            if (Entry.Key == EKeys::SpaceBar) if (auto* MotorPawn = Cast<AU01Character>(GetPawn())) MotorPawn->StopJumping();
        }
#endif
}

void AU01PlayerController::ObservePhysicalKey(FKey Key, bool bDown)
{
    if (!IsGameWindowActive()) return; // Do not interpret another window's releases as re-arming gameplay.
    if (bDown)
    {
        const auto* MotorPawn = Cast<AU01Character>(GetPawn());
        const bool bFixtureBlocked = MotorPawn && MotorPawn->GetU01Movement()->IsMotorLocked() && IsMotorKey(Key);
        ReleaseGate.Down(Key, ControlState != EU01ControlState::Playing || bFixtureBlocked);
        UE_LOG(LogU01Control, Display, TEXT("PhysicalPress key=%s state=%d accepted=%d reason=%s"),
            *Key.ToString(), int32(ControlState), IsMotorKey(Key) ? Accepts(Key) : (ControlState == EU01ControlState::Playing && ReleaseGate.Allows(Key)),
            ControlState != EU01ControlState::Playing ? TEXT("ControlLocked") : bFixtureBlocked ? TEXT("MotorFixtureLocked") : (ReleaseGate.Allows(Key) ? TEXT("Ready") : TEXT("AwaitingPhysicalRelease")));
    }
    else
    {
        ReleaseGate.Up(Key);
        if (Key == EKeys::SpaceBar) if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn())) ControlledCharacter->StopJumping();
        UE_LOG(LogU01Control, Display, TEXT("PhysicalRelease/Rearm key=%s"), *Key.ToString());
    }
}

bool AU01PlayerController::Accepts(FKey Key) const
{
    const auto* MotorPawn = Cast<AU01Character>(GetPawn());
    return ControlState == EU01ControlState::Playing && !bMotorLocked && ReleaseGate.Allows(Key) && IsGameWindowActive()
        && MotorPawn && !MotorPawn->GetU01Movement()->IsMotorLocked();
}

void AU01PlayerController::MoveDirection(const FInputActionValue& Value, int32 DirectionIndex)
{
    if (DirectionIndex < 0 || DirectionIndex > 3 || !Value.Get<bool>() || !Accepts(DirectionKeys[DirectionIndex])) return;
    if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn()))
    {
        const FRotationMatrix Yaw(FRotator(0, GetControlRotation().Yaw, 0));
        const FVector Direction = Yaw.GetUnitAxis(DirectionIndex < 2 ? EAxis::X : EAxis::Y);
        ControlledCharacter->AddMovementInput(Direction, (DirectionIndex == 1 || DirectionIndex == 2) ? -1 : 1);
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
    if (Accepts(EKeys::SpaceBar)) if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn())) ControlledCharacter->Jump();
}
void AU01PlayerController::Sprint(const FInputActionValue& Value)
{
    if (auto* MotorPawn = Cast<AU01Character>(GetPawn()))
        MotorPawn->GetU01Movement()->SetSprintRequested(Value.Get<bool>() &&
            ((IsInputKeyDown(EKeys::LeftControl) && Accepts(EKeys::LeftControl)) || (IsInputKeyDown(EKeys::RightControl) && Accepts(EKeys::RightControl))));
}
void AU01PlayerController::SprintReleased()
{
    if (auto* MotorPawn = Cast<AU01Character>(GetPawn())) MotorPawn->GetU01Movement()->SetSprintRequested(false);
}
void AU01PlayerController::ShoulderPressed()
{
    if (ControlState == EU01ControlState::Playing && ReleaseGate.Allows(EKeys::V) && IsGameWindowActive())
        if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn())) ControlledCharacter->ToggleShoulder();
}
void AU01PlayerController::MenuPressed() { LockControls(EU01ControlState::Menu, TEXT("Escape")); }

void AU01PlayerController::LockControls(EU01ControlState NewState, const TCHAR* Reason)
{
    if (!IsLocalPlayerController()) return;
    ReleaseGate.Lock();
    ControlState = NewState;
    bMotorLocked = true;
    if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn())) ControlledCharacter->SetControlLocked(true);
    FlushPressedKeys();
    bShowMouseCursor = true;
    if (MenuWidget)
    {
        if (!MenuWidget->IsInViewport()) MenuWidget->AddToPlayerScreen(100);
        SetInputMode(FInputModeUIOnly().SetWidgetToFocus(MenuWidget->TakeWidget()).SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock));
    }
    if (auto* LP = GetLocalPlayer()) if (UGameViewportClient* Viewport = LP->ViewportClient.Get())
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
    if (auto* LP = GetLocalPlayer()) if (UGameViewportClient* Viewport = LP->ViewportClient.Get())
    {
        Viewport->SetMouseCaptureMode(EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown);
        Viewport->SetMouseLockMode(EMouseLockMode::LockOnCapture);
        Viewport->SetHideCursorDuringCapture(true);
    }
}

void AU01PlayerController::ResumePlaying()
{
    if (!IsLocalPlayerController() || !IsGameWindowActive()) return;
    ReconcilePhysicalReleases();
    if (MenuWidget) MenuWidget->RemoveFromParent();
    FlushPressedKeys();
    ControlState = EU01ControlState::Playing;
    bMotorLocked = false;
    if (auto* ControlledCharacter = Cast<AU01Character>(GetPawn())) ControlledCharacter->SetControlLocked(false);
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
    const AU01Character* ControlledCharacter = Cast<AU01Character>(GetPawn());
    const UWorld* World = ControlledCharacter ? ControlledCharacter->GetWorld() : nullptr;
    if (!World || (World->WorldType != EWorldType::Game && World->WorldType != EWorldType::PIE) || ControlledCharacter->GetController() != this)
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
    Json->SetStringField(TEXT("pawn"), ControlledCharacter->GetPathName());
    Json->SetStringField(TEXT("controller"), GetPathName());
    Json->SetStringField(TEXT("owner"), GetPathNameSafe(ControlledCharacter->GetOwner()));
    Json->SetNumberField(TEXT("localRole"), int32(ControlledCharacter->GetLocalRole()));
    Json->SetNumberField(TEXT("remoteRole"), int32(ControlledCharacter->GetRemoteRole()));
    Json->SetBoolField(TEXT("locallyControlled"), ControlledCharacter->IsLocallyControlled());
    Json->SetNumberField(TEXT("localPlayers"), GetGameInstance()->GetNumLocalPlayers());
    Json->SetStringField(TEXT("capsuleCenterWorldCm"), ControlledCharacter->GetActorLocation().ToString());
    Json->SetStringField(TEXT("velocityCmPerSec"), ControlledCharacter->GetVelocity().ToString());
    Json->SetStringField(TEXT("accelerationCmPerSec2"), ControlledCharacter->GetCharacterMovement()->GetCurrentAcceleration().ToString());
    Json->SetStringField(TEXT("feetWorldCm"), ControlledCharacter->GetU01Movement()->GetActorFeetLocation().ToString());
    Json->SetNumberField(TEXT("movementMode"), int32(ControlledCharacter->GetCharacterMovement()->MovementMode));
    Json->SetBoolField(TEXT("sprinting"), ControlledCharacter->GetU01Movement()->IsSprinting());
    Json->SetNumberField(TEXT("maxSpeedCmPerSec"), ControlledCharacter->GetU01Movement()->GetMaxSpeed());
    Json->SetNumberField(TEXT("jumpCount"), ControlledCharacter->JumpCurrentCount);
    Json->SetNumberField(TEXT("gravityCmPerSec2"), ControlledCharacter->GetU01Movement()->GetGravityZ());
    Json->SetNumberField(TEXT("jumpZVelocityCmPerSec"), ControlledCharacter->GetU01Movement()->JumpZVelocity);
    Json->SetNumberField(TEXT("motorLockMask"), ControlledCharacter->GetU01Movement()->GetLockMask());
    Json->SetNumberField(TEXT("motorTimeSeconds"), ControlledCharacter->GetU01Movement()->GetMotorTimeSeconds());
    Json->SetBoolField(TEXT("bufferedJump"), ControlledCharacter->GetU01Movement()->HasBufferedJump(ControlledCharacter->GetU01Movement()->GetMotorTimeSeconds()));
    Json->SetStringField(TEXT("pivotWorldCm"), ControlledCharacter->CameraPivot.ToString());
    Json->SetStringField(TEXT("desiredCameraWorldCm"), ControlledCharacter->DesiredCamera.ToString());
    Json->SetStringField(TEXT("resolvedCameraWorldCm"), PlayerCameraManager->GetCameraLocation().ToString());
    Json->SetStringField(TEXT("aimDirectionWorld"), PlayerCameraManager->GetCameraRotation().Vector().ToString());
    Json->SetStringField(TEXT("aimYawPitchDegrees"), GetControlRotation().ToString());
    Json->SetNumberField(TEXT("fovDegrees"), PlayerCameraManager->GetFOVAngle());
    Json->SetNumberField(TEXT("sweepRadiusCm"), 12);
    if (const auto* LP = GetLocalPlayer()) if (const UGameViewportClient* Viewport = LP->ViewportClient.Get())
        Json->SetNumberField(TEXT("mouseCaptureMode"), int32(Viewport->GetMouseCaptureMode()));
    Json->SetNumberField(TEXT("cameraPivotDistanceCm"), ControlledCharacter->CameraDistance);
    Json->SetNumberField(TEXT("shoulderOffsetCm"), ControlledCharacter->ShoulderOffset);
    Json->SetBoolField(TEXT("cameraHit"), ControlledCharacter->bCameraHit);
    Json->SetBoolField(TEXT("ownerMeshHidden"), ControlledCharacter->bOwnerMeshHidden);
    Json->SetBoolField(TEXT("windowActive"), IsGameWindowActive());
    Json->SetBoolField(TEXT("cursorVisible"), bShowMouseCursor);
    Json->SetBoolField(TEXT("motorLocked"), ControlledCharacter->GetU01Movement()->IsMotorLocked());
    Json->SetNumberField(TEXT("controlState"), int32(ControlState));
    FString Result;
    FJsonSerializer::Serialize(Json, TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Result));
    return Result;
}

bool AU01PlayerController::FixtureAllowed() const
{
#if UE_BUILD_SHIPPING
    return false;
#else
    return IsLocalPlayerController() && GetNetMode() == NM_Standalone && GetPawn() &&
        (GetWorld()->GetMapName().EndsWith(TEXT("L_CharacterCombatLab")) || GetWorld()->GetMapName().EndsWith(TEXT("L_NetworkLab")));
#endif
}

bool AU01PlayerController::HasTerrainFixtures() const
{
    return GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_CharacterCombatLab"));
}

void AU01PlayerController::U01FixtureReset(const FString& Station)
{
    if (!FixtureAllowed()) return;
    const FName Tag(*(TEXT("U01C_Reset_") + Station));
    TArray<AActor*> Points;
    UGameplayStatics::GetAllActorsWithTag(this, Tag, Points);
    auto* MotorPawn = Cast<AU01Character>(GetPawn());
    if (Points.Num() != 1 || !MotorPawn)
    {
        UE_LOG(LogU01Control, Warning, TEXT("Fixture reset rejected station=%s points=%d"), *Station, Points.Num());
        return;
    }
    ReleaseGate.Lock();
    FlushPressedKeys();
    MotorPawn->GetU01Movement()->ResetFixtureState();
    MotorPawn->SetActorLocation(Points[0]->GetActorLocation(), false, nullptr, ETeleportType::TeleportPhysics);
    MotorPawn->SetActorRotation(FRotator::ZeroRotator);
    MotorPawn->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    SetControlRotation(FRotator::ZeroRotator);
    FixtureStation = Station;
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(FixtureStations); ++Index)
        if (Station.Equals(FixtureStations[Index], ESearchCase::IgnoreCase))
        {
            FixtureStationIndex = Index;
            FixtureStation = FixtureStations[Index];
            break;
        }
    UE_LOG(LogU01Control, Display, TEXT("LabFixtureReset station=%s PID=%u world=%s pawn=%s positionCm=%s"),
        *Station, FPlatformProcess::GetCurrentProcessId(), *GetWorld()->GetPathName(), *MotorPawn->GetPathName(), *MotorPawn->GetActorLocation().ToString());
}

void AU01PlayerController::U01FixtureLock(const FString& Reason, bool bEnabled)
{
    if (!FixtureAllowed()) return;
    auto* MotorPawn = Cast<AU01Character>(GetPawn());
    if (!MotorPawn || (Reason != TEXT("Interacting") && Reason != TEXT("Defeated"))) return;
    ReleaseGate.Lock();
    FlushPressedKeys();
    MotorPawn->GetU01Movement()->SetMotorLock(Reason == TEXT("Interacting") ? EU01MotorLock::Interacting : EU01MotorLock::Defeated, bEnabled);
    UE_LOG(LogU01Control, Display, TEXT("LabFixtureLock reason=%s enabled=%d mask=%d world=%s pawn=%s"),
        *Reason, bEnabled, MotorPawn->GetU01Movement()->GetLockMask(), *GetWorld()->GetPathName(), *MotorPawn->GetPathName());
}
void AU01PlayerController::ResetRunwayFixture() { U01FixtureReset(TEXT("Runway")); }
void AU01PlayerController::NextFixtureStation()
{
    FixtureStationIndex = (FixtureStationIndex + 1) % UE_ARRAY_COUNT(FixtureStations);
    U01FixtureReset(FixtureStations[FixtureStationIndex]);
}
void AU01PlayerController::ToggleInteractingFixture()
{
    if (auto* MotorPawn = Cast<AU01Character>(GetPawn()))
        U01FixtureLock(TEXT("Interacting"), (MotorPawn->GetU01Movement()->GetLockMask() & uint8(EU01MotorLock::Interacting)) == 0);
}
void AU01PlayerController::ToggleDefeatedFixture()
{
    if (auto* MotorPawn = Cast<AU01Character>(GetPawn()))
        U01FixtureLock(TEXT("Defeated"), (MotorPawn->GetU01Movement()->GetLockMask() & uint8(EU01MotorLock::Defeated)) == 0);
}
FString AU01PlayerController::GetFixtureStatus() const
{
    const auto* MotorPawn = Cast<AU01Character>(GetPawn());
    return FString::Printf(TEXT("Lab fixture: %s | Interacting=%d Defeated=%d"), *FixtureStation,
        MotorPawn ? bool(MotorPawn->GetU01Movement()->GetLockMask() & uint8(EU01MotorLock::Interacting)) : false,
        MotorPawn ? bool(MotorPawn->GetU01Movement()->GetLockMask() & uint8(EU01MotorLock::Defeated)) : false);
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
