#pragma once
#include "CoreMinimal.h"
#include "Components/SphereComponent.h"
#include "U02ActionModel.h"
#include "U02HurtboxComponent.generated.h"

UCLASS(ClassGroup=(Combat))
class ANIMEMMORPG_API UU02HurtboxComponent : public USphereComponent
{
    GENERATED_BODY()
public:
    UU02HurtboxComponent();
    UPROPERTY(EditDefaultsOnly,Category="U02") uint32 StableHurtboxId=1;
    virtual void BeginPlay() override;
    virtual void EndPlay(EEndPlayReason::Type Reason) override;
    virtual void OnUpdateTransform(EUpdateTransformFlags Flags,ETeleportType Teleport) override;
    AnimeMMORPG::U02::FLifeId GetSubject() const;
    void SetFixtureSubject(AnimeMMORPG::U02::FLifeId Life) { FixtureSubject=Life;++ContinuityEpoch; }
    void MarkDiscontinuous() { ++ContinuityEpoch; }
    uint64 ContinuityEpoch=1;
private:
    AnimeMMORPG::U02::FLifeId FixtureSubject;
};
