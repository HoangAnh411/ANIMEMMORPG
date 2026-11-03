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
    if (WidgetTree->RootWidget) return Super::RebuildWidget();
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
    Text(TEXT("WASD move | Mouse look | Space jump | V shoulder | Esc menu"));
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
