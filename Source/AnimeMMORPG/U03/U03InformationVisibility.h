#pragma once
#include "CoreMinimal.h"
class AU01PlayerController;
class AActor;
class UWorld;
namespace AnimeMMORPG::U03
{
FVector InformationPoint(const AActor* Actor);
bool ProjectInformation(const AU01PlayerController* PC,const AActor* Actor,FVector2D& Screen,FVector2D& Center);
bool InformationEnvironmentClear(UWorld* World,FVector Camera,FVector Point);
bool InformationClear(const AU01PlayerController* PC,const AActor* Actor);
// World-attached Canvas glyphs require both the C2 subject visibility and their
// own anchor visibility. This query never selects a target or changes authority.
bool PresentationVisible(const AU01PlayerController* PC,const AActor* Actor,FVector Anchor,FVector2D& Screen);
}
