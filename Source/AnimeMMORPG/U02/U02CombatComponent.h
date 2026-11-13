#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "U02ActionModel.h"
#include "U02StartupTurn.h"
#include "U03/U03ActionModel.h"
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
    UPROPERTY() double TurnFromYaw = 0;
    UPROPERTY() double TurnStartSeconds = 0;
    UPROPERTY() uint64 LastCommand = 0;
    UPROPERTY() uint64 Accepted = 0;
    UPROPERTY() uint64 Rejected = 0;
    UPROPERTY() uint8 RejectReason = 0;
    UPROPERTY() uint8 DefinitionId = 0;
    UPROPERTY() uint32 DefinitionVersion = 1;
    UPROPERTY() int32 RawDamage = 60;
    UPROPERTY() double ActiveStart = .16;
    UPROPERTY() double ActiveEnd = .22;
    UPROPERTY() double Duration = .40;
    UPROPERTY() double Energy = 100;
    UPROPERTY() double QReadyAt = 0;
    UPROPERTY() double EReadyAt = 0;
    UPROPERTY() double FeintLockEnd=0;
    UPROPERTY() double FeintLastSuccess=-1;
    UPROPERTY() uint64 FeintSequence=0;
    UPROPERTY() uint64 FeintAction=0;
    UPROPERTY() uint64 InterruptSequence=0;
    UPROPERTY() uint64 InterruptedAction=0;
    UPROPERTY() double InterruptTime=0;
    UPROPERTY() bool bLocked = false;
    UPROPERTY() bool bYawLocked = false;
    UPROPERTY() uint64 DodgeSequence=0;
    UPROPERTY() int32 DodgeCharges=2;
    UPROPERTY() double DodgeStart=0;
    UPROPERTY() double DodgeMotionEnd=0;
    UPROPERTY() double DodgeLockEnd=0;
    UPROPERTY() double DodgeNextStart=0;
    UPROPERTY() double DodgeRestoreAt=0;
    UPROPERTY() FVector DodgeDirection=FVector::ZeroVector;
    UPROPERTY() FVector DodgeOrigin=FVector::ZeroVector;
    UPROPERTY() bool bGuard=false;
    UPROPERTY() uint64 GuardSequence=0;
    UPROPERTY() double GuardYaw=0;
    UPROPERTY() double Posture=100;
    UPROPERTY() bool bParryOpen=false;
    UPROPERTY() double ParryStart=0;
    UPROPERTY() double ParryEnd=0;
    UPROPERTY() double ParryReadyAt=0;
    UPROPERTY() uint8 HardCC=0;
    UPROPERTY() double HardEnd=0;
    UPROPERTY() double LockedBudget=0;
    UPROPERTY() double ImmuneEnd=0;
    UPROPERTY() double SlowFraction=0;
    UPROPERTY() double XReadyAt=0;
    UPROPERTY() uint64 DefenseEvent=0;
    UPROPERTY() uint8 DefenseResult=0;
    UPROPERTY() double DefenseEventTime=0;
    UPROPERTY() uint64 ParryFeedbackSequence=0;
    UPROPERTY() double ParryFeedbackTime=0;
};

USTRUCT()
struct FU03OwnerAdmission
{
    GENERATED_BODY()
    UPROPERTY() uint64 Command=0;
    UPROPERTY() uint8 Admission=0;
    UPROPERTY() uint64 PendingCommand=0;
    UPROPERTY() double PendingExpires=0;
    UPROPERTY() uint32 Revision=0;
};

DECLARE_MULTICAST_DELEGATE_TwoParams(FU02ActiveIntervalDelegate, const AnimeMMORPG::U02::FActionId&, const AnimeMMORPG::U02::FActiveSlice&);
DECLARE_DELEGATE_OneParam(FU02BeforeActionMutation, double);

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
    void DiscardPendingInputs(); // authority control/interaction locks, not an action cancel
    void SubmitCombatIntent(AnimeMMORPG::U03::ECommand Command, uint64 Sequence, double LocalSeconds, double Yaw,FVector2D Direction=FVector2D::ZeroVector);
    void Landed();
    const FU03OwnerAdmission& GetAdmission() const { return OwnerAdmission; }
    void SendNetworkFixtureProbe(const FString& Kind); // opt-in lab only
    uint64 GetLastCommand() const {return LastCommand;}
    bool CancelAction(AnimeMMORPG::U02::ECancel Reason);
    bool ResetLabCombat();
    void LostGround();
    void HandleDefeat(double GameplayTime);
    const FU02RepCombatSnapshot& GetCombatSnapshot() const { return Snapshot; }
    TSharedRef<FJsonObject> GetDiagnostics() const;
    FU02ActiveIntervalDelegate OnActiveInterval;
    // D binds the Game-world scheduler here: drain ALL sources/resolve old batch before mutation.
    // Unbound in B because there are no hit candidates/vital results yet.
    FU02BeforeActionMutation BeforeActionMutation;
    uint64 AcceptedCount = 0, RejectedCount = 0, IntervalCount = 0;
private:
    friend struct FU02CombatTestAccess;
    friend struct FU02FTestAccess;
    friend struct FU03RuntimeAccess;
    friend struct FU03B1Access;
    friend struct FU03B2Access;
    friend class UU02CollisionWorld;
    UPROPERTY(ReplicatedUsing=OnRep_Snapshot) FU02RepCombatSnapshot Snapshot;
    UFUNCTION() void OnRep_Snapshot();
    UFUNCTION(Server, Reliable) void ServerAttack(uint64 Sequence, double LocalInputSeconds, double Yaw, FGuid Pawn, uint64 Life);
    UFUNCTION(Server, Reliable) void ServerControlPlaying(bool bPlaying);
    UFUNCTION(Server, Unreliable) void ServerAim(double Yaw, FGuid Pawn, uint64 Life, uint64 Action);
    UFUNCTION(Server, Unreliable) void ServerGuardAim(double Yaw,FGuid Pawn,uint64 Life,uint64 Guard);
    TUniquePtr<AnimeMMORPG::U03::FTimelineModel> Model;
    UPROPERTY(Replicated) FU03OwnerAdmission OwnerAdmission;
    UFUNCTION(Server,Reliable) void ServerCombat(uint8 Command,uint64 Sequence,double LocalSeconds,double Yaw,FGuid Pawn,uint64 Life,FVector2D Direction);
    struct FQueuedIntent { AnimeMMORPG::U03::FCombatIntent Intent; double LocalSeconds=0,Receive=0; };
    TArray<FQueuedIntent> QueuedIntents;
    struct FQueuedAim {double Yaw;FGuid Pawn;uint64 Life,Action;uint64 Guard=0;};
    TArray<FQueuedAim> QueuedAim;
    void ProcessQueuedIntents(double Now);
    void RememberCurrent(double Now);
    void ReceiveIntent(AnimeMMORPG::U03::ECommand Command,uint64 Sequence,double LocalSeconds,double Yaw,FGuid Pawn,uint64 Life,FVector2D Direction=FVector2D::ZeroVector);
    uint64 QueuedCount=0,ReplacedCount=0,AdmissionWatermark=0;
    bool bApplyingWorldDeath=false;
    AU01Character* Character() const;
    bool bAuthorityPlaying = true;
    AnimeMMORPG::U02::FStartupTurn StartupTurn;
    double LastAimSend = -1;
    uint64 LastCommand = 0;
    uint64 PresentedDefenseEvent=0,PresentedDefenseLife=0;
    UPROPERTY(Transient) TObjectPtr<class USoundWaveProcedural> ParryTone;
    uint64 LastSentCommand=0,LastSentLife=0;
    AnimeMMORPG::U02::EReject LastReject = AnimeMMORPG::U02::EReject::None;
    AnimeMMORPG::U02::FActiveSlice LastInterval;
    void HandleAttack(uint64 Sequence, double LocalInputSeconds, double Yaw, double Now);
    bool AdvanceAuthority(double Now, bool bExcludeEnd = false);
    bool CancelAt(AnimeMMORPG::U02::ECancel Reason, double Now);
    void Publish(double Now, bool bForce = false);
    void ApplyMotorSnapshot();
    void Trace(const TCHAR* Event, double GameplaySeconds, const FString& Detail = FString()) const;
};
