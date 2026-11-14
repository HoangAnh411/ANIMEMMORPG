#include "U03MonsterStateComponent.h"
#include "GameFramework/Actor.h"
UU03MonsterStateComponent::UU03MonsterStateComponent()
{PrimaryComponentTick.bCanEverTick=false;SetIsReplicatedByDefault(false);}
AnimeMMORPG::U03::FMonsterDecision UU03MonsterStateComponent::DecideServer(const AnimeMMORPG::U03::FMonsterObservation& O)
{
    if(!GetOwner()||!GetOwner()->HasAuthority())return {ServerState,false,false,false};
    const auto D=AnimeMMORPG::U03::DecideMonster(ServerState,O);ServerState=D.State;return D;
}
void UU03MonsterStateComponent::SetServerState(AnimeMMORPG::U03::EMonsterState State)
{if(GetOwner()&&GetOwner()->HasAuthority())ServerState=State;}
