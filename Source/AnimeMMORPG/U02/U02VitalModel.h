#pragma once
#include "CoreMinimal.h"
namespace AnimeMMORPG::U02
{
struct FShield { uint64 Source=0; int32 Capacity=0; double Deadline=0; };
struct FDamageResult
{
    bool bApplied=false,bCrit=false,bDied=false;
    int32 Damage=0,Absorbed=0,HPDamage=0,BeforeHP=0,AfterHP=0;
    TArray<uint64> ShieldOrder;
};
struct FVitalModel
{
    int32 MaxHP=1000,HP=1000;
    uint64 Generation=1;
    uint32 DeathCount=0;
    double AttackFactor=1,Defense=0;
    TArray<FShield> Shields;
    bool bDead=false;
    bool AddShield(uint64 Source,int32 Capacity,double Deadline,double Now);
    int32 ShieldAt(double Now) const;
    void Expire(double Now);
    bool Reset(uint64 NewGeneration,int32 NewMaxHP);
    static int32 Calculate(double Raw,double Attack,double Defense,bool Crit,double BlockFactor=1);
    FDamageResult Apply(double Raw,double Attack,double Roll,double Now,double BlockFactor=1);
};
}
