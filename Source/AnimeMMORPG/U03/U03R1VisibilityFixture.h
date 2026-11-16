#pragma once
#include "CoreMinimal.h"
#include "Engine/StaticMeshActor.h"
#include "U03R1VisibilityFixture.generated.h"

// Explicit opt-in capture fixture; never spawned by ordinary play or launchers.
UCLASS(NotBlueprintable)
class ANIMEMMORPG_API AU03R1VisibilityWall : public AStaticMeshActor
{
    GENERATED_BODY()
public:
    AU03R1VisibilityWall();
    void Configure(FVector InOrigin,bool Partial);
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
private:
    UPROPERTY(ReplicatedUsing=Apply) FVector Origin;
    UPROPERTY(ReplicatedUsing=Apply) bool bPartial=false;
    UFUNCTION() void Apply();
};
