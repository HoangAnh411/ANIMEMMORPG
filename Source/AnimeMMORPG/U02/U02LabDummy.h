#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "U02LabDummy.generated.h"
class UU02HurtboxComponent;
class UStaticMeshComponent;
// Technical lab target only. No vital state / damage / product respawn.
UCLASS()
class ANIMEMMORPG_API AU02LabDummy : public AActor
{
    GENERATED_BODY()
public:
    AU02LabDummy();
    virtual void BeginPlay() override;
    bool ResetLabCombat();
    UPROPERTY(VisibleAnywhere) TObjectPtr<UU02HurtboxComponent> Body;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UU02HurtboxComponent> Head;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Visual;
    FGuid NetworkPawnId;
    uint64 LifeGeneration=1;
};
