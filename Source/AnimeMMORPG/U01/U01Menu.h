#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "U01Menu.generated.h"

UCLASS()
class ANIMEMMORPG_API UU01Menu : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
    virtual void NativeTick(const FGeometry& Geometry,float DeltaSeconds) override;
    void ShowMainMenu();
    void ShowControls();
private:
    UPROPERTY(Transient) TObjectPtr<class UWidgetSwitcher> Pages;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> SettingsStatus;
    UPROPERTY(Transient) TArray<TObjectPtr<class UTextBlock>> BindingLabels;
    UPROPERTY(Transient) TObjectPtr<class USlider> Sensitivity;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> SensitivityLabel;
    UPROPERTY(Transient) TObjectPtr<class UCheckBox> InvertY;
    UPROPERTY(Transient) TObjectPtr<class UCheckBox> RightShoulder;
    void RefreshSettings();
    UFUNCTION() void ControlsClicked();
    UFUNCTION() void BackClicked();
    UFUNCTION() void SaveClicked();
    UFUNCTION() void DefaultsClicked();
    UFUNCTION() void SensitivityChanged(float Value);
    UFUNCTION() void SliderReleased();
    UFUNCTION() void InvertChanged(bool Value);
    UFUNCTION() void ShoulderChanged(bool Value);
    UFUNCTION() void BindForward();
    UFUNCTION() void BindBackward();
    UFUNCTION() void BindLeft();
    UFUNCTION() void BindRight();
    UFUNCTION() void BindJump();
    UFUNCTION() void BindSprint();
    UFUNCTION() void BindShoulder();
    UFUNCTION() void BindInteract();
    UFUNCTION() void BindAttack();
    UFUNCTION() void BindGuard();
    UFUNCTION() void BindDodge();
    UFUNCTION() void BindEscapeCC();
    UFUNCTION() void BindSkillQ();
    UFUNCTION() void BindSkillE();
    UFUNCTION() void BindTarget();
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> FixtureStatus;
    void UpdateFixtureStatus();
    UFUNCTION() void ResetFixtureClicked();
    UFUNCTION() void NextFixtureClicked();
    UFUNCTION() void InteractingFixtureClicked();
    UFUNCTION() void DefeatedFixtureClicked();
    UFUNCTION() void ResumeClicked();
    UFUNCTION() void BootClicked();
    UFUNCTION() void QuitClicked();
};
