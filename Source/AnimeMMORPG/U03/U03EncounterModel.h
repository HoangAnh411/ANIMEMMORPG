#pragma once
#include "CoreMinimal.h"

namespace AnimeMMORPG::U03
{
enum class EMonsterState : uint8 { Idle, Chase, Action, Return, Defeated };
enum class EEncounterResult : uint8 { Running, Won, Lost };

// Distances are cm, measured in 3D; inclusive admission/reset boundaries.
struct FMonsterObservation
{
    double TargetDistance=0, SpawnDistance=0;
    bool bTargetAlive=true, bMonsterAlive=true, bLineOfSight=true, bAction=false;
};
struct FMonsterDecision
{
    EMonsterState State=EMonsterState::Idle;
    bool bCancel=false, bReset=false, bAttack=false;
};
inline FMonsterDecision DecideMonster(EMonsterState State,const FMonsterObservation& O)
{
    if(!O.bMonsterAlive)return {EMonsterState::Defeated,true,false,false};
    if(State==EMonsterState::Defeated)return {State,false,false,false};
    if(State==EMonsterState::Return)
        return O.SpawnDistance<=50.?FMonsterDecision{EMonsterState::Idle,false,true,false}:FMonsterDecision{State,false,false,false};
    const bool HasTarget=O.bTargetAlive&&O.TargetDistance<=1000.&&O.bLineOfSight;
    if(O.SpawnDistance>1500. || (State!=EMonsterState::Idle&&!HasTarget))
        return {EMonsterState::Return,true,false,false};
    if(!HasTarget)return {EMonsterState::Idle,false,false,false};
    if(O.bAction)return {EMonsterState::Action,false,false,false};
    return O.TargetDistance<=200.?FMonsterDecision{EMonsterState::Action,false,false,true}:FMonsterDecision{EMonsterState::Chase,false,false,false};
}

// First resolver-confirmed lethal wins; no invented same-time draw.
struct FEncounterModel
{
    uint64 Revision=1, RetryWatermark=0;
    EEncounterResult Result=EEncounterResult::Running;
    bool bClosed=false;
    bool Defeat(bool bMonster)
    {
        if(bClosed||Result!=EEncounterResult::Running)return false;
        Result=bMonster?EEncounterResult::Won:EEncounterResult::Lost;return true;
    }
    bool AdmitRetry(uint64 ClaimedRevision,uint64 Sequence,bool bOwned)
    {
        if(!bOwned||bClosed||!Sequence||Sequence<=RetryWatermark)return false;
        RetryWatermark=Sequence;
        return ClaimedRevision==Revision&&Result!=EEncounterResult::Running;
    }
    void CommitRetry() {++Revision;Result=EEncounterResult::Running;}
};
}
