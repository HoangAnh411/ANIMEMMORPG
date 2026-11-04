#include "U01Menu.h"
#include "U01PlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Border.h"

TSharedRef<SWidget> UU01Menu::RebuildWidget()
{
    SetIsFocusable(true);
    if (WidgetTree->RootWidget) { UpdateFixtureStatus(); return Super::RebuildWidget(); }
    UBorder* Border = WidgetTree->ConstructWidget<UBorder>();
    Border->SetBrushColor(FLinearColor(.025f, .035f, .05f, .94f));
    Border->SetPadding(FMargin(32));
    Border->SetHorizontalAlignment(HAlign_Center);
    Border->SetVerticalAlignment(VAlign_Center);
    WidgetTree->RootWidget = Border;
    UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>();
    Border->SetContent(Box);
    auto Text = [this, Box](const TCHAR* Content)
    {
        UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>();
        Label->SetText(FText::FromString(Content));
        Box->AddChildToVerticalBox(Label)->SetPadding(FMargin(8));
    };
    Text(TEXT("U01 - Menu"));
    Text(TEXT("World continues. Choose Resume to play."));
    auto Button = [this, Box](const TCHAR* LabelText)
    {
        UButton* Result = WidgetTree->ConstructWidget<UButton>();
        UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>();
        Label->SetText(FText::FromString(LabelText));
        Result->SetContent(Label);
        Box->AddChildToVerticalBox(Result)->SetPadding(FMargin(8));
        return Result;
    };
    Button(TEXT("Resume"))->OnClicked.AddDynamic(this, &UU01Menu::ResumeClicked);
    Text(TEXT("WASD move | Ctrl sprint | Space jump | Mouse look | V shoulder"));
#if !UE_BUILD_SHIPPING
    if (const auto* PC = Cast<AU01PlayerController>(GetOwningPlayer()); PC && PC->HasTerrainFixtures())
    {
    Text(TEXT("Lab fixtures (test tools, not respawn)"));
    FixtureStatus = WidgetTree->ConstructWidget<UTextBlock>();
    Box->AddChildToVerticalBox(FixtureStatus)->SetPadding(FMargin(8));
    UpdateFixtureStatus();
    Button(TEXT("Fixture: reset runway"))->OnClicked.AddDynamic(this, &UU01Menu::ResetFixtureClicked);
    Button(TEXT("Fixture: next terrain station"))->OnClicked.AddDynamic(this, &UU01Menu::NextFixtureClicked);
    Button(TEXT("Fixture: toggle Interacting lock"))->OnClicked.AddDynamic(this, &UU01Menu::InteractingFixtureClicked);
    Button(TEXT("Fixture: toggle Defeated lock"))->OnClicked.AddDynamic(this, &UU01Menu::DefeatedFixtureClicked);
    }
#endif
    Button(TEXT("Back to Boot"))->OnClicked.AddDynamic(this, &UU01Menu::BootClicked);
    Button(TEXT("Quit"))->OnClicked.AddDynamic(this, &UU01Menu::QuitClicked);
    return Super::RebuildWidget();
}

FReply UU01Menu::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if (Event.GetKey() == EKeys::Escape) return FReply::Handled(); // Never resume via Escape.
    return Super::NativeOnKeyDown(Geometry, Event);
}

void UU01Menu::ResumeClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->ResumePlaying(); }
void UU01Menu::BootClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->ReturnToBoot(); }
void UU01Menu::QuitClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->QuitToDesktop(); }
void UU01Menu::UpdateFixtureStatus()
{
    if (FixtureStatus) if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) FixtureStatus->SetText(FText::FromString(PC->GetFixtureStatus()));
}
void UU01Menu::ResetFixtureClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->ResetRunwayFixture(); UpdateFixtureStatus(); }
void UU01Menu::NextFixtureClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->NextFixtureStation(); UpdateFixtureStatus(); }
void UU01Menu::InteractingFixtureClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->ToggleInteractingFixture(); UpdateFixtureStatus(); }
void UU01Menu::DefeatedFixtureClicked() { if (auto* PC = Cast<AU01PlayerController>(GetOwningPlayer())) PC->ToggleDefeatedFixture(); UpdateFixtureStatus(); }
