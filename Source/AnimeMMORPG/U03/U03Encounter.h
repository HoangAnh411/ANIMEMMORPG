#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "U01/U01Character.h"
#include "U03EncounterModel.h"
#include "U02/U02CollisionGeometry.h"
#include "U03Encounter.generated.h"

class AU01PlayerController;
class UU02CollisionWorld;

USTRUCT()
struct FU03EncounterSnapshot
{
    GENERATED_BODY()
    UPROPERTY() FGuid Id;
    UPROPERTY() uint64 Revision=1;
    UPROPERTY() uint8 Result=0;
    UPROPERTY() uint8 AI=0;
    UPROPERTY() TObjectPtr<AU01Character> Player;
    UPROPERTY() TObjectPtr<AU01Character> Monster;
    UPROPERTY() FString OwnerLabel;
    UPROPERTY() int32 Station=0;
    UPROPERTY() bool bClosed=false;
};

UCLASS()
class ANIMEMMORPG_API AU03Monster : public AU01Character
{
    GENERATED_BODY()
public:
    AU03Monster(const FObjectInitializer& Initializer);
    virtual void Tick(float Dt) override;
};

UCLASS()
class ANIMEMMORPG_API AU03Encounter : public AActor
{
    GENERATED_BODY()
public:
    AU03Encounter();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    const FU03EncounterSnapshot& GetSnapshot() const {return Snapshot;}
    void Initialize(AU01PlayerController* OwnerController,AU01Character* Player,const FTransform& PlayerSpawn,const FTransform& MonsterSpawn,int32 Station=0);
    void Close(double At);
    bool Retry(AU01PlayerController* Requester,FGuid Id,uint64 Revision,uint64 Sequence);
    void ConfirmDefeat(AActor* Subject,double At);
    static AU03Encounter* ForSubject(const AActor* Subject);
    static bool CanDamage(const AActor* Source,const AActor* Target);
    // Called only by the shared world scheduler. Pose sampling is owned by that scheduler.
    double NextBoundary(double From,double Through,const TFunction<FVector(AActor*,double)>& Feet,const TArray<AnimeMMORPG::U02::FTriangle>& Triangles) const;
    void BeforeContacts(double At,const TFunction<FVector(AActor*,double)>& Feet);
    void AfterBarrier(double At);
private:
    friend struct FU03C2Access;
    UPROPERTY(Replicated) FU03EncounterSnapshot Snapshot;
    AnimeMMORPG::U03::FEncounterModel Model;
    FTransform PlayerSpawn,MonsterSpawn;
    bool bResetOnBarrier=false,bResetting=false;
    uint64 MonsterCommand=0;
    double LastDecision=-1;
    AnimeMMORPG::U03::FMonsterObservation Observe(double At,const TFunction<FVector(AActor*,double)>& Feet) const;
    bool EnvironmentClear(FVector A,FVector B) const;
    void ResetSubjects(double At,bool Both);
    void Publish();
};

UCLASS()
class ANIMEMMORPG_API AU03EncounterGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AU03EncounterGameMode();
    virtual void RestartPlayer(AController* Player) override;
    virtual void PreLogin(const FString& Options,const FString& Address,const FUniqueNetIdRepl& UniqueId,FString& ErrorMessage) override;
    virtual void Logout(AController* Exiting) override;
private:
    bool IsRegression() const;
};

UCLASS()
class ANIMEMMORPG_API AU03EncounterHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};
