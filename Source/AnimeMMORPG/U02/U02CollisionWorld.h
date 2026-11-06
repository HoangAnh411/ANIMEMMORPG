#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "U02ActionModel.h"
#include "U02CollisionGeometry.h"
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
    FU02GeometryConfirmed OnGeometryConfirmed;
    TArray<AnimeMMORPG::U02::FHitCandidate> Confirmed;
    uint64 Queries=0,Blocked=0,Discontinuities=0;
    uint32 UnsupportedObstructions=0;
    bool bCharacterFixtureTargets=false; // Native test fixture only; normal lab attacks dummies.
private:
    friend struct FU02CollisionTestAccess;
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
        FBox Bounds=FBox(ForceInit);
    };
    TArray<FSource> Sources;
    TArray<FHurt> Hurts;
    TArray<FPending> Pending;
    TArray<FEnvironment> Environment;
    TArray<AnimeMMORPG::U02::FTriangle> Triangles;
    AnimeMMORPG::U02::FResolveLedger Ledger;
    FDelegateHandle TickHandle;
    double PreviousTime=0,CurrentTime=-1;
    bool bDraining=false;
    void PreActorTick(UWorld* World,ELevelTick Type,float Dt);
    void Capture(double Now);
    void CaptureEnvironment();
    void CollectHitCandidates(const FPending& Interval,TArray<AnimeMMORPG::U02::FHitCandidate>& Out);
    bool ResolveHit(const AnimeMMORPG::U02::FHitCandidate& Candidate);
    bool Unobstructed(FVector Origin,FVector Center,double Radius) const;
};
