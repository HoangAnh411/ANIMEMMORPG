#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "U02LabDummy.generated.h"
class UU02HurtboxComponent;
class UU02VitalComponent;
class UStaticMeshComponent;
// Server-owned lab target; replicated identity/vital state, no product respawn.
UCLASS()
class ANIMEMMORPG_API AU02LabDummy : public AActor
{
    GENERATED_BODY()
public:
    AU02LabDummy();
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    bool ResetLabCombat();
    UPROPERTY(VisibleAnywhere) TObjectPtr<UU02HurtboxComponent> Body;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UU02HurtboxComponent> Head;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UU02VitalComponent> Vital;
    UPROPERTY(ReplicatedUsing=OnRep_Identity) FGuid NetworkPawnId;
    UPROPERTY(ReplicatedUsing=OnRep_Identity) uint64 LifeGeneration=1;
    UFUNCTION() void OnRep_Identity();
};
