#include "U03InformationVisibility.h"
#include "U01/U01PlayerController.h"
#include "U01/U01Character.h"
#include "U02/U02VitalComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "SceneView.h"
namespace AnimeMMORPG::U03
{
FVector InformationPoint(const AActor* A)
{const auto* C=Cast<AU01Character>(A);return A->GetActorLocation()+FVector(0,0,90-(C?C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight():0));}
namespace {
bool ProjectPoint(const AU01PlayerController* PC,FVector Point,FVector2D& Screen,FVector2D& Center)
{
    auto* LP=PC?PC->GetLocalPlayer():nullptr;if(!LP||!LP->ViewportClient||!LP->ViewportClient->Viewport)return false;
    FSceneViewProjectionData Data;if(!LP->GetProjectionData(LP->ViewportClient->Viewport,Data))return false;
    const FIntRect Rect=Data.GetConstrainedViewRect();Center=FVector2D(Rect.Width(),Rect.Height())*.5;
    if(!FSceneView::ProjectWorldToScreen(Point,Rect,Data.ComputeViewProjectionMatrix(),Screen))return false;
    Screen-=FVector2D(Rect.Min.X,Rect.Min.Y);
    return Screen.X>=0&&Screen.Y>=0&&Screen.X<Rect.Width()&&Screen.Y<Rect.Height();
}
}
bool ProjectInformation(const AU01PlayerController* PC,const AActor* A,FVector2D& Screen,FVector2D& Center)
{return A&&ProjectPoint(PC,InformationPoint(A),Screen,Center);}
bool InformationEnvironmentClear(UWorld* World,FVector Camera,FVector Point)
{
    if(!World)return false;FCollisionQueryParams Q(SCENE_QUERY_STAT(U03TabLOS),false);
    for(TActorIterator<AActor> It(World);It;++It)if(It->IsA<APawn>()||It->FindComponentByClass<UU02VitalComponent>())Q.AddIgnoredActor(*It);
    return !World->LineTraceTestByChannel(Camera,Point,ECC_GameTraceChannel2,Q);
}
bool InformationClear(const AU01PlayerController* PC,const AActor* A)
{
    if(!PC||!A)return false;FVector Camera;FRotator Rotation;PC->GetPlayerViewPoint(Camera,Rotation);
    return InformationEnvironmentClear(PC->GetWorld(),Camera,InformationPoint(A));
}
bool PresentationVisible(const AU01PlayerController* PC,const AActor* A,FVector Anchor,FVector2D& Screen)
{
    FVector2D SubjectScreen,Center;if(!ProjectInformation(PC,A,SubjectScreen,Center)||!InformationClear(PC,A))return false;
    FVector Camera;FRotator Rotation;PC->GetPlayerViewPoint(Camera,Rotation);
    return ProjectPoint(PC,Anchor,Screen,Center)&&InformationEnvironmentClear(PC->GetWorld(),Camera,Anchor);
}
}
