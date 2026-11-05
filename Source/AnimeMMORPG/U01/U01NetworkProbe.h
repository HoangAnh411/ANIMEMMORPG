#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "U01NetworkProbe.generated.h"

// Development-only opt-in collector/ground fixture, never a gameplay network service.
UCLASS()
class ANIMEMMORPG_API UU01NetworkProbe : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual bool DoesSupportWorldType(EWorldType::Type Type) const override {return Type==EWorldType::Game||Type==EWorldType::PIE;}
    virtual void OnWorldBeginPlay(UWorld& World) override;
    virtual void Tick(float Dt) override;
    virtual TStatId GetStatId() const override {RETURN_QUICK_DECLARE_CYCLE_STAT(UU01NetworkProbe,STATGROUP_Tickables);}
private:
    float Elapsed=0;
    FString Run;
    bool Enabled=false;
};
