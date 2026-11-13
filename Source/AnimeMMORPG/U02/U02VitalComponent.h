#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "U02VitalModel.h"
#include "U02ActionModel.h"
#include "U02VitalComponent.generated.h"
class FJsonObject;
USTRUCT()
struct FU02RepVital
{
    GENERATED_BODY()
    UPROPERTY() int32 HP=1000;
    UPROPERTY() int32 MaxHP=1000;
    UPROPERTY() int32 Shield=0;
    UPROPERTY() uint64 Generation=1;
    UPROPERTY() uint32 DeathCount=0;
    UPROPERTY() bool bDead=false;
};
UCLASS(ClassGroup=(Combat))
class ANIMEMMORPG_API UU02VitalComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UU02VitalComponent();
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    const FU02RepVital& GetSnapshot() const {return Snapshot;}
    AnimeMMORPG::U02::FLifeId GetLife() const;
    bool IsAlive(AnimeMMORPG::U02::FLifeId Life) const;
    double GetAttackFactor() const {return State.AttackFactor;}
    AnimeMMORPG::U02::FDamageResult ApplyResolved(const AnimeMMORPG::U02::FHitCandidate& Hit,double Attack,double Roll,double BlockFactor=1);
    bool ResetLabCombat(uint64 Generation);
    bool AddFixtureShield(uint64 Source,int32 Capacity,double Deadline,double Now);
    void Refresh(double GameplayNow);
    TSharedRef<FJsonObject> GetDiagnostics() const;
private:
    friend struct FU03B1Access;
    friend struct FU03B2Access;
    friend struct FU02VitalTestAccess;
    friend struct FU03RuntimeAccess;
    AnimeMMORPG::U02::FVitalModel State;
    UPROPERTY(ReplicatedUsing=OnRep_Snapshot) FU02RepVital Snapshot;
    UFUNCTION() void OnRep_Snapshot();
    void Publish(double Now);
};
