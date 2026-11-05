#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "U02ActionModel.h"
#include "U02CombatComponent.generated.h"

class AU01Character;
class FJsonObject;

USTRUCT()
struct FU02RepCombatSnapshot
{
    GENERATED_BODY()
    UPROPERTY() FGuid PawnId;
    UPROPERTY() uint64 LifeGeneration = 1;
    UPROPERTY() uint64 ActionSequence = 0;
    UPROPERTY() uint32 Revision = 0;
    UPROPERTY() uint8 Phase = 0;
    UPROPERTY() double StartSeconds = 0;
    UPROPERTY() double ServerSeconds = 0;
    UPROPERTY() double AimYawDegrees = 0;
    UPROPERTY() bool bLocked = false;
    UPROPERTY() bool bYawLocked = false;
};

DECLARE_MULTICAST_DELEGATE_TwoParams(FU02ActiveIntervalDelegate, const AnimeMMORPG::U02::FActionId&, const AnimeMMORPG::U02::FActiveSlice&);

// Server-owned action adapter only. D will subscribe the world collector; no hit/damage here.
UCLASS(ClassGroup=(Combat))
class ANIMEMMORPG_API UU02CombatComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UU02CombatComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    void SubmitAttackIntent(uint64 CommandSequence, double LocalInputSeconds, double AimYawDegrees);
    void SetControlPlaying(bool bPlaying);
    bool CancelAction(AnimeMMORPG::U02::ECancel Reason);
    bool ResetLabCombat();
    void LostGround();
    const FU02RepCombatSnapshot& GetCombatSnapshot() const { return Snapshot; }
    TSharedRef<FJsonObject> GetDiagnostics() const;
    FU02ActiveIntervalDelegate OnActiveInterval;
    uint64 AcceptedCount = 0, RejectedCount = 0, IntervalCount = 0;
private:
    friend struct FU02CombatTestAccess;
    UPROPERTY(ReplicatedUsing=OnRep_Snapshot) FU02RepCombatSnapshot Snapshot;
    UFUNCTION() void OnRep_Snapshot();
    UFUNCTION(Server, Reliable) void ServerAttack(uint64 Sequence, double LocalInputSeconds, double Yaw);
    UFUNCTION(Server, Reliable) void ServerControlPlaying(bool bPlaying);
    UFUNCTION(Server, Unreliable) void ServerAim(double Yaw);
    TUniquePtr<AnimeMMORPG::U02::FActionModel> Model;
    AU01Character* Character() const;
    bool bAuthorityPlaying = true;
    double LastAimSend = -1;
    uint64 LastCommand = 0;
    AnimeMMORPG::U02::EReject LastReject = AnimeMMORPG::U02::EReject::None;
    AnimeMMORPG::U02::FActiveSlice LastInterval;
    void HandleAttack(uint64 Sequence, double LocalInputSeconds, double Yaw, double Now);
    bool AdvanceAuthority(double Now, bool bExcludeEnd = false);
    bool CancelAt(AnimeMMORPG::U02::ECancel Reason, double Now);
    void Publish(double Now, bool bForce = false);
    void ApplyMotorSnapshot();
    void Trace(const TCHAR* Event, double GameplaySeconds, const FString& Detail = FString()) const;
};
