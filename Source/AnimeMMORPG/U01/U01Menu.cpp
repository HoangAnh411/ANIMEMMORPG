#include "U01Menu.h"
#include "U01PlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Border.h"
#include "Components/WidgetSwitcher.h"
#include "Components/Slider.h"
#include "Components/CheckBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/ScrollBox.h"

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
    USizeBox* Size=WidgetTree->ConstructWidget<USizeBox>();Size->SetWidthOverride(720);Size->SetMaxDesiredHeight(440);
    Border->SetContent(Size);
    Pages=WidgetTree->ConstructWidget<UWidgetSwitcher>();Size->SetContent(Pages);
    UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>();
    Pages->AddChild(Box);
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
    Button(TEXT("Điều khiển / Controls"))->OnClicked.AddDynamic(this, &UU01Menu::ControlsClicked);
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
    // Reuse the builders with a second page; every binding belongs to this LocalPlayer.
    Box=WidgetTree->ConstructWidget<UVerticalBox>();auto* ControlsScroll=WidgetTree->ConstructWidget<UScrollBox>();ControlsScroll->AddChild(Box);Pages->AddChild(ControlsScroll);
    auto Label=[this](const TCHAR* Value)
    {
        auto* Result=WidgetTree->ConstructWidget<UTextBlock>();Result->SetText(FText::FromString(Value));
        auto Font=Result->GetFont();Font.Size=16;Result->SetFont(Font);return Result;
    };
    Box->AddChildToVerticalBox(Label(TEXT("Điều khiển — một phím/nút; Escape hủy nhận phím")));
    const TCHAR* Names[]={TEXT("Tiến"),TEXT("Lùi"),TEXT("Trái"),TEXT("Phải"),TEXT("Nhảy"),TEXT("Sprint (giữ)"),TEXT("Đổi vai"),TEXT("Tương tác (fixture)"),TEXT("Attack"),TEXT("Guard (unavailable)"),TEXT("Dodge (unavailable)"),TEXT("Escape CC (unavailable)"),TEXT("Q (unavailable)"),TEXT("E (unavailable)"),TEXT("Target (unavailable)")};
    for(int32 I=0;I<AnimeMMORPG::U01::ControlCount;++I)
    {
        auto* Row=WidgetTree->ConstructWidget<UHorizontalBox>();Box->AddChildToVerticalBox(Row)->SetPadding(FMargin(2));
        Row->AddChildToHorizontalBox(Label(Names[I]))->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* Bind=WidgetTree->ConstructWidget<UButton>();auto* Key=Label(TEXT(""));Bind->SetContent(Key);BindingLabels.Add(Key);
        auto* Width=WidgetTree->ConstructWidget<USizeBox>();Width->SetWidthOverride(280);Width->SetContent(Bind);Row->AddChildToHorizontalBox(Width);
        // AddDynamic needs a named member token for reflection.
        switch(I){case 0:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindForward);break;
        case 1:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindBackward);break;case 2:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindLeft);break;
        case 3:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindRight);break;case 4:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindJump);break;
        case 5:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindSprint);break;case 6:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindShoulder);break;
        case 7:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindInteract);break;case 8:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindAttack);break;case 9:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindGuard);break;case 10:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindDodge);break;case 11:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindEscapeCC);break;case 12:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindSkillQ);break;case 13:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindSkillE);break;case 14:Bind->OnClicked.AddDynamic(this,&UU01Menu::BindTarget);break;}
    }
    SensitivityLabel=Label(TEXT(""));Box->AddChildToVerticalBox(SensitivityLabel);
    Sensitivity=WidgetTree->ConstructWidget<USlider>();Sensitivity->SetMinValue(.1f);Sensitivity->SetMaxValue(3.f);
    Box->AddChildToVerticalBox(Sensitivity)->SetPadding(FMargin(4,8));
    Sensitivity->OnValueChanged.AddDynamic(this,&UU01Menu::SensitivityChanged);
    Sensitivity->OnMouseCaptureEnd.AddDynamic(this,&UU01Menu::SliderReleased);
    Sensitivity->OnControllerCaptureEnd.AddDynamic(this,&UU01Menu::SliderReleased);
    InvertY=WidgetTree->ConstructWidget<UCheckBox>();InvertY->SetContent(Label(TEXT("Đảo Y")));Box->AddChildToVerticalBox(InvertY);
    InvertY->OnCheckStateChanged.AddDynamic(this,&UU01Menu::InvertChanged);
    RightShoulder=WidgetTree->ConstructWidget<UCheckBox>();RightShoulder->SetContent(Label(TEXT("Vai phải mặc định (bỏ chọn = vai trái)")));Box->AddChildToVerticalBox(RightShoulder);
    RightShoulder->OnCheckStateChanged.AddDynamic(this,&UU01Menu::ShoulderChanged);
    auto ControlButton=[this,Box,Label](const TCHAR* Value)
    {
        auto* Result=WidgetTree->ConstructWidget<UButton>();Result->SetContent(Label(Value));Box->AddChildToVerticalBox(Result)->SetPadding(FMargin(2));return Result;
    };
    ControlButton(TEXT("Khôi phục mặc định"))->OnClicked.AddDynamic(this,&UU01Menu::DefaultsClicked);
    ControlButton(TEXT("Save"))->OnClicked.AddDynamic(this,&UU01Menu::SaveClicked);
    ControlButton(TEXT("Về menu"))->OnClicked.AddDynamic(this,&UU01Menu::BackClicked);
    SettingsStatus=Label(TEXT(""));SettingsStatus->SetAutoWrapText(true);
    // Shared status remains visible on both pages, including a failed Resume save.
    auto* Outer=WidgetTree->ConstructWidget<UVerticalBox>();Size->SetContent(Outer);
    Outer->AddChildToVerticalBox(Pages);Outer->AddChildToVerticalBox(SettingsStatus)->SetPadding(FMargin(4,8));
    RefreshSettings();
    return Super::RebuildWidget();
}

void UU01Menu::NativeTick(const FGeometry& Geometry,float DeltaSeconds)
{
    Super::NativeTick(Geometry,DeltaSeconds);RefreshSettings();UpdateFixtureStatus();
}
void UU01Menu::ShowMainMenu(){if(Pages)Pages->SetActiveWidgetIndex(0);}
void UU01Menu::ShowControls(){if(Pages)Pages->SetActiveWidgetIndex(1);RefreshSettings();}
void UU01Menu::RefreshSettings()
{
    auto* PC=Cast<AU01PlayerController>(GetOwningPlayer());if(!PC)return;
    const auto& Data=PC->GetPreferences();
    for(int32 I=0;I<BindingLabels.Num();++I)
        BindingLabels[I]->SetText(FText::FromString(PC->GetPendingRebind()==I?TEXT("Nhấn phím… (Esc hủy)"):
            Data.Keys[I]==EKeys::LeftControl?TEXT("Ctrl (trái / phải)"):Data.Keys[I].GetDisplayName().ToString()));
    if(SettingsStatus)SettingsStatus->SetText(FText::FromString(PC->GetSettingsStatus()));
    if(Sensitivity){Sensitivity->SetValue(Data.Sensitivity);SensitivityLabel->SetText(FText::FromString(FString::Printf(TEXT("Độ nhạy chuột: %.2f (0.10–3.00)"),Data.Sensitivity)));}
    if(InvertY)InvertY->SetIsChecked(Data.bInvertY);
    if(RightShoulder)RightShoulder->SetIsChecked(Data.bRightShoulder);
}
void UU01Menu::ControlsClicked(){ShowControls();}
void UU01Menu::BackClicked(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->CancelRebind();ShowMainMenu();}
void UU01Menu::SaveClicked(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->SaveSettings(true);}
void UU01Menu::DefaultsClicked(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->RestoreControlDefaults();RefreshSettings();}
void UU01Menu::SensitivityChanged(float Value){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->ChangeSensitivity(Value);}
void UU01Menu::SliderReleased(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->SaveSettings();}
void UU01Menu::InvertChanged(bool Value){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->ChangeInvertY(Value);}
void UU01Menu::ShoulderChanged(bool Value){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->ChangeRightShoulder(Value);}
void UU01Menu::BindForward(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(0);}
void UU01Menu::BindBackward(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(1);}
void UU01Menu::BindLeft(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(2);}
void UU01Menu::BindRight(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(3);}
void UU01Menu::BindJump(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(4);}
void UU01Menu::BindSprint(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(5);}
void UU01Menu::BindShoulder(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(6);}
void UU01Menu::BindInteract(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(7);}

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

void UU01Menu::BindAttack(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(8);}
void UU01Menu::BindGuard(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(9);}
void UU01Menu::BindDodge(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(10);}
void UU01Menu::BindEscapeCC(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(11);}
void UU01Menu::BindSkillQ(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(12);}
void UU01Menu::BindSkillE(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(13);}
void UU01Menu::BindTarget(){if(auto* PC=Cast<AU01PlayerController>(GetOwningPlayer()))PC->BeginRebind(14);}
