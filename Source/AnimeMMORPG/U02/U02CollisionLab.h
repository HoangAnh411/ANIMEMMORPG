#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "U02CollisionLab.generated.h"
UCLASS()
class ANIMEMMORPG_API AU02CollisionLab : public AActor
{
    GENERATED_BODY()
public:
    AU02CollisionLab();
    virtual void BeginPlay() override;
};
