#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "U02CollisionWorld.h"
#include "U02NetworkState.generated.h"
USTRUCT()
struct FU02ConfirmedResult
{
    GENERATED_BODY()
    UPROPERTY() uint64 Serial=0;
    UPROPERTY() FGuid Source;
    UPROPERTY() FGuid Target;
    UPROPERTY() uint64 SourceLife=0;
    UPROPERTY() uint64 Action=0;
    UPROPERTY() uint64 TargetLife=0;
    UPROPERTY() uint32 Hurtbox=0;
    UPROPERTY() double Timestamp=0;
    UPROPERTY() uint8 DefinitionId=0;
    UPROPERTY() int32 RawDamage=60;
    UPROPERTY() int32 Damage=0;
    UPROPERTY() int32 Absorbed=0;
    UPROPERTY() int32 HP=0;
    UPROPERTY() bool Crit=false;
    UPROPERTY() bool Death=false;
    UPROPERTY() uint8 Defense=0;
};
// Bounded authoritative event history for presentation/diagnostics; never mutates client HP.
UCLASS()
class ANIMEMMORPG_API AU02NetworkState : public AActor
{
    GENERATED_BODY()
public:
    AU02NetworkState();
    virtual void Tick(float Dt) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    void Confirm(const UU02CollisionWorld::FConfirmedDamage& Result);
    UPROPERTY(Replicated) int32 CritMode=0; // 0 production5%,1 fixture off,2 fixture forced
    UPROPERTY(ReplicatedUsing=OnRep_Results) TArray<FU02ConfirmedResult> Results;
private:
    UFUNCTION() void OnRep_Results();
    uint64 NextSerial=0,LastSeenSerial=0;
    float ProbeElapsed=0;
    FString LastFixtureCommand;
    void ProcessFixture();
    void EmitState();
};
