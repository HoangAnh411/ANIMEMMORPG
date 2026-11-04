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
private:
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
