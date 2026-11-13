#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "U02ActionModel.h"
#include "U02CollisionGeometry.h"
#include "U02VitalModel.h"
#include "U03/U03ActionModel.h"
#include "U02CollisionWorld.generated.h"

class UU02CombatComponent;
class UU02HurtboxComponent;
class UPrimitiveComponent;
class AU01Character;
DECLARE_MULTICAST_DELEGATE_OneParam(FU02GeometryConfirmed,const AnimeMMORPG::U02::FHitCandidate&);

// One server Game/PIE world scheduler. No HP, RNG, damage or overlap-callback resolution.
UCLASS()
class ANIMEMMORPG_API UU02CollisionWorld : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual bool DoesSupportWorldType(EWorldType::Type Type) const override;
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    void RegisterCombat(UU02CombatComponent* Combat);
    void UnregisterCombat(UU02CombatComponent* Combat);
    void RegisterHurtbox(UU02HurtboxComponent* Hurtbox);
    void UnregisterHurtbox(UU02HurtboxComponent* Hurtbox);
    void ObserveCombat(UU02CombatComponent* Combat);
    void DrainAt(double Now);
    bool ApplyLifecycle(UU02CombatComponent* Combat,double At,AnimeMMORPG::U03::ECutoff Reason,bool bLanding);
    bool FixtureSpend(UU02CombatComponent* Combat,AnimeMMORPG::U03::EAction Skill);

    void MarkDead(AnimeMMORPG::U02::FLifeId Life);
    void RebaseResetSubject(AActor* Subject); // after authority reset drained the old batch
    bool SelectDebugAction(uint64 Sequence); // lab diagnostics only, 0 selects next local action
    void DrawSelectedAction();
    FU02GeometryConfirmed OnGeometryConfirmed;
    TArray<AnimeMMORPG::U02::FHitCandidate> Confirmed;
    struct FConfirmedDamage { AnimeMMORPG::U02::FHitCandidate Hit;AnimeMMORPG::U02::FDamageResult Result;double Roll=0; bool bInterrupted=false; uint64 InterruptedAction=0; };
    TArray<FConfirmedDamage> DamageResults;
    uint64 CritRolls=0;
    double FixtureCritRoll=-1; // native fixture only, -1 production server roll
    bool SetLabCritRoll(double Roll);
    void ResetLabDummies();
    uint64 Queries=0,Blocked=0,Discontinuities=0;
    uint32 UnsupportedObstructions=0;
    bool bCharacterFixtureTargets=false; // Native test fixture only; normal lab attacks dummies.
    struct FDefenseFixtureHit
    {
        bool bBlockable=true,bParryable=true;
        AnimeMMORPG::U03::EHardCC Hard=AnimeMMORPG::U03::EHardCC::None;
        double Duration=0,Slow=0;
    };
    // Explicit labelled fixtures only; no product PvP or client outcome RPC.
    void StartDefenseFixture(const FString& Label);
    void TickDefenseFixture(double Now);
private:
    friend struct FU03B2Access;
    friend struct FU03B1Access;
    friend struct FU02CollisionTestAccess;
    friend struct FU02EVitalWorldAccess;
    friend struct FU03RuntimeAccess;
    struct FPose
    {
        FVector Position=FVector::ZeroVector;
        AnimeMMORPG::U02::FLifeId Life;
        uint64 Epoch=0;
        double Radius=0;
    };
    struct FSource
    {
        TWeakObjectPtr<UU02CombatComponent> Component;
        FDelegateHandle IntervalHandle;
        FPose Previous,Current;
        uint64 FeedbackAction=0,FeedbackLife=0;
    };
    struct FHurt
    {
        TWeakObjectPtr<UU02HurtboxComponent> Component;
        FPose Previous,Current;
        double AvailableFrom=0; // new life/pose cannot be collected into an earlier captured interval
    };
    struct FPending
    {
        TWeakObjectPtr<UU02CombatComponent> Component;
        AnimeMMORPG::U02::FActionId Action;
        AnimeMMORPG::U02::FActiveSlice Slice;
        double Yaw=0;
        uint8 DefinitionId=0; uint32 DefinitionVersion=1; int32 RawDamage=60;
        bool bBlockable=true,bParryable=true,bInterrupt=false;
    };
    struct FEnvironment
    {
        TWeakObjectPtr<UPrimitiveComponent> Component;
        bool bSupported=true;
        int32 FirstTriangle=0,TriangleCount=0;
        FBox Bounds=FBox(ForceInit);
    };
    TArray<FSource> Sources;
    TArray<FHurt> Hurts;
    TArray<FPending> Pending;
    TArray<FEnvironment> Environment;
    TArray<TWeakObjectPtr<UPrimitiveComponent>> IgnoredObstructionComponents;
    TArray<AnimeMMORPG::U02::FTriangle> Triangles;
    AnimeMMORPG::U02::FResolveLedger Ledger;
    FDelegateHandle TickHandle;
    double PreviousTime=0,CurrentTime=-1;
    bool bDraining=false;
    double SimulationTime=-1;
    struct FLifecycleEvent {TWeakObjectPtr<UU02CombatComponent> Combat;double At;AnimeMMORPG::U03::ECutoff Reason;bool Landing;uint64 Serial;};
    TArray<FLifecycleEvent> LifecycleEvents;
    uint64 NextLifecycle=0;
    TMap<uint64,bool> LifecycleResults;
    TArray<AnimeMMORPG::U02::FActionId> FixtureInterruptActions; // native fixtures, no client setter
    TMap<AnimeMMORPG::U02::FActionId,FDefenseFixtureHit> DefenseFixtureHits;
    struct FDefenseEnemy {TWeakObjectPtr<AU01Character> Actor;TWeakObjectPtr<AU01Character> Target;FString Label;double Next=0;};
    TArray<FDefenseEnemy> DefenseEnemies;
    void EmitInterval(UU02CombatComponent* Combat,const AnimeMMORPG::U03::FActiveInterval& Interval);
    void CollectCurrent(double Through,TArray<AnimeMMORPG::U02::FHitCandidate>& Out);

    TWeakObjectPtr<AActor> HUDTarget;
    void DrawVitalHUD();
    struct FDebugHurt
    {
        AnimeMMORPG::U02::FHitId Hit;
        uint32 Hurtbox=0;
        FVector Feet,Center,Origin,Nearest,BlockPoint;
        double Yaw=0,Radius=0,Time=0;
        FString Result,Wall;
        bool bHasBlock=false;
    };
    bool bSelectedDebug=false;
    AnimeMMORPG::U02::FActionId DebugAction;
    TArray<FDebugHurt> DebugHurts;
    void RecordSelected(const FPending& P,AnimeMMORPG::U02::FLifeId Target,uint32 Hurtbox,FVector Feet,FVector Center,double Radius,double Time,const FString& Result);
    void PreActorTick(UWorld* World,ELevelTick Type,float Dt);
    void Capture(double Now);
    void CaptureEnvironment();
    void CollectHitCandidates(const FPending& Interval,TArray<AnimeMMORPG::U02::FHitCandidate>& Out);
    bool ResolveHit(const AnimeMMORPG::U02::FHitCandidate& Candidate);
    bool Unobstructed(FVector Origin,FVector Center,double Radius) const;
};
