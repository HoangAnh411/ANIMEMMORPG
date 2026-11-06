#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "U02ActionModel.h"
#include "U02CollisionGeometry.h"
#include "U02VitalModel.h"
#include "U02CollisionWorld.generated.h"

class UU02CombatComponent;
class UU02HurtboxComponent;
class UPrimitiveComponent;
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
    void MarkDead(AnimeMMORPG::U02::FLifeId Life);
    bool SelectDebugAction(uint64 Sequence); // lab diagnostics only, 0 selects next local action
    void DrawSelectedAction();
    FU02GeometryConfirmed OnGeometryConfirmed;
    TArray<AnimeMMORPG::U02::FHitCandidate> Confirmed;
    struct FConfirmedDamage { AnimeMMORPG::U02::FHitCandidate Hit;AnimeMMORPG::U02::FDamageResult Result;double Roll=0; };
    TArray<FConfirmedDamage> DamageResults;
    uint64 CritRolls=0;
    double FixtureCritRoll=-1; // native fixture only, -1 production server roll
    bool SetLabCritRoll(double Roll);
    void ResetLabDummies();
    uint64 Queries=0,Blocked=0,Discontinuities=0;
    uint32 UnsupportedObstructions=0;
    bool bCharacterFixtureTargets=false; // Native test fixture only; normal lab attacks dummies.
private:
    friend struct FU02CollisionTestAccess;
    friend struct FU02EVitalWorldAccess;
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
    };
    struct FPending
    {
        TWeakObjectPtr<UU02CombatComponent> Component;
        AnimeMMORPG::U02::FActionId Action;
        AnimeMMORPG::U02::FActiveSlice Slice;
        double Yaw=0;
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
