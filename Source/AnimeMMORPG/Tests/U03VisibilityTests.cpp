#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U03/U03InformationVisibility.h"
#include "U03/U03FeedbackWindow.h"
#include "U03/U03TelegraphComponent.h"
#include "U01/U01Character.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
using namespace AnimeMMORPG::U03;
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03R1WorldVisibility,"AnimeMMORPG.U03.DR1.EnvironmentOcclusionAndFeedback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03R1WorldVisibility::RunTest(const FString&)
{
    FTestWorldWrapper W;W.CreateTestWorld(EWorldType::Game);auto* World=W.GetTestWorld();
    auto* Wall=World->SpawnActor<AActor>();auto* Box=NewObject<UBoxComponent>(Wall);Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(10,100,150));Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);Box->SetCollisionResponseToAllChannels(ECR_Block);Box->RegisterComponent();Wall->SetActorLocation(FVector(0,0,150));
    const FVector Camera(-500,0,150),Subject(300,0,150),Revealed(300,400,150);
    TestFalse(TEXT("Opaque environment hides subject"),InformationEnvironmentClear(World,Camera,Subject));
    TestTrue(TEXT("Move outside wall silhouette reveals subject"),InformationEnvironmentClear(World,Camera,Revealed));
    TestTrue(TEXT("Other client camera visibility is independent"),InformationEnvironmentClear(World,FVector(500,0,150),Subject));
    uint64 Serial=0;
    const bool Hidden=InformationEnvironmentClear(World,Camera,Subject);
    TestFalse(TEXT("Fresh hidden authority event cannot sound"),FreshFeedbackAudio(ConsumeFeedback(7,Serial),true,Hidden,10,10.02));
    const bool Visible=InformationEnvironmentClear(World,Camera,Revealed);
    TestTrue(TEXT("Reveal retains only remaining visual lifetime"),Visible&&FeedbackRemaining(10,10.5)>0);
    TestFalse(TEXT("Reveal cannot replay already consumed sound"),FreshFeedbackAudio(ConsumeFeedback(7,Serial),true,Visible,10,10.05));
    TestEqual(TEXT("Reappearance after expiry remains expired"),FeedbackRemaining(10,11.21),0.);
    TestFalse(TEXT("Expired duplicate cannot sound"),FreshFeedbackAudio(ConsumeFeedback(7,Serial),true,Visible,10,11.21));
    Wall->Destroy();
    auto* Body=World->SpawnActor<APawn>();auto* BodyBox=NewObject<UBoxComponent>(Body);Body->SetRootComponent(BodyBox);
    BodyBox->SetBoxExtent(FVector(10,100,150));BodyBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);BodyBox->SetCollisionResponseToAllChannels(ECR_Block);BodyBox->RegisterComponent();Body->SetActorLocation(FVector(0,0,150));
    TestTrue(TEXT("C2 excludes combat bodies from environment occlusion"),InformationEnvironmentClear(World,Camera,Subject));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU03R1Geometry,"AnimeMMORPG.U03.DR1.WorldTelegraphGeometry",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FU03R1Geometry::RunTest(const FString&)
{
    const FVector Feet(20,40,60);const auto Segments=UU03TelegraphComponent::SwordSegments(Feet,90,3);
    TestEqual(TEXT("12 sword box edges plus direction and two arrow wings"),Segments.Num(),15);
    FBox Box(ForceInit);for(int I=0;I<12;++I){Box+=Segments[I].A;Box+=Segments[I].B;}
    TestTrue(TEXT("Exact rotated authority volume, without inflated hit extent"),Box.Min.Equals(Feet+FVector(-60,0,0),.001)&&Box.Max.Equals(Feet+FVector(60,200,180),.001));
    TestTrue(TEXT("Arrow follows confirmed yaw"),(Segments[12].B-Segments[12].A).Equals(FVector(0,180,0),.001));
    auto* C=NewObject<UU03TelegraphComponent>();C->SetSegments(Segments);
    TestEqual(TEXT("Visual component has no collision"),C->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
    TestFalse(TEXT("Visual component cannot change navigation"),C->CanEverAffectNavigation());
    const auto Bounds=C->CalcBounds(FTransform::Identity).GetBox();for(const auto& S:Segments)TestTrue(TEXT("Culling bounds include entire edge"),Bounds.IsInsideOrOn(S.A)&&Bounds.IsInsideOrOn(S.B));
    C->SetSegments({});TestEqual(TEXT("End/cancel clears all world geometry"),C->GetSegments().Num(),0);
    return true;
}
#endif
