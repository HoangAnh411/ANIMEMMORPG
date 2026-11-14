#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "U03EncounterModel.h"
#include "U03MonsterStateComponent.generated.h"

// Server-owned FSM. The encounter/world barrier supplies observations and applies
// decisions at their resolver timestamps; this component never ticks or deals damage.
UCLASS(ClassGroup=(Combat))
class ANIMEMMORPG_API UU03MonsterStateComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UU03MonsterStateComponent();
    AnimeMMORPG::U03::FMonsterDecision DecideServer(const AnimeMMORPG::U03::FMonsterObservation& Observation);
    void SetServerState(AnimeMMORPG::U03::EMonsterState State);
    void ResetServer() {SetServerState(AnimeMMORPG::U03::EMonsterState::Idle);}
    AnimeMMORPG::U03::EMonsterState GetServerState() const {return ServerState;}
private:
    AnimeMMORPG::U03::EMonsterState ServerState=AnimeMMORPG::U03::EMonsterState::Idle;
};
