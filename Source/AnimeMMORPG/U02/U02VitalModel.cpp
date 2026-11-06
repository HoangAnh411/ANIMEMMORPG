#include "U02VitalModel.h"
namespace AnimeMMORPG::U02
{
void FVitalModel::Expire(double Now) {Shields.RemoveAll([&](const FShield& S){return S.Deadline<=Now||S.Capacity<=0;});}
int32 FVitalModel::ShieldAt(double Now) const
{
    int64 Sum=0;for(const auto& S:Shields)if(S.Deadline>Now)Sum+=S.Capacity;return int32(FMath::Min<int64>(Sum,MAX_int32));
}
bool FVitalModel::AddShield(uint64 Source,int32 Capacity,double Deadline,double Now)
{
    if(bDead||!Source||Capacity<0||!FMath::IsFinite(Now)||!FMath::IsFinite(Deadline)||Deadline<=Now)return false;
    Expire(Now);Shields.RemoveAll([&](const FShield& S){return S.Source==Source;});
    if(Capacity>0)Shields.Add({Source,Capacity,Deadline});return true;
}
bool FVitalModel::Reset(uint64 NewGeneration,int32 NewMaxHP)
{
    if(NewGeneration<=Generation||NewMaxHP<=0)return false;
    Generation=NewGeneration;MaxHP=HP=NewMaxHP;bDead=false;DeathCount=0;Shields.Empty();return true;
}
int32 FVitalModel::Calculate(double Raw,double Attack,double Def,bool Crit,double Block)
{
    if(!FMath::IsFinite(Raw)||!FMath::IsFinite(Attack)||!FMath::IsFinite(Def)||!FMath::IsFinite(Block)||Raw<0||Attack<0||Def<0||Block<0||Block>1)return -1;
    const double Value=Raw*Attack*(100./(100.+Def))*(Crit?1.5:1.)*Block;
    if(!FMath::IsFinite(Value)||Value>MAX_int32-.5)return -1;
    return int32(FMath::FloorToDouble(Value+.5));
}
FDamageResult FVitalModel::Apply(double Raw,double Attack,double Roll,double Now,double Block)
{
    FDamageResult R;if(bDead||HP<=0||!FMath::IsFinite(Now)||!FMath::IsFinite(Roll)||Roll<0||Roll>=1)return R;
    const int32 Damage=Calculate(Raw,Attack,Defense,Roll<.05,Block);if(Damage<0)return R;
    Expire(Now);Shields.Sort([](const FShield& A,const FShield& B){return A.Deadline==B.Deadline?A.Source<B.Source:A.Deadline<B.Deadline;});
    R.bApplied=true;R.bCrit=Roll<.05;R.Damage=Damage;R.BeforeHP=HP;int32 Remaining=Damage;
    for(auto& S:Shields)
    {
        if(!Remaining)break;const int32 Take=FMath::Min(Remaining,S.Capacity);if(!Take)continue;
        S.Capacity-=Take;Remaining-=Take;R.Absorbed+=Take;R.ShieldOrder.Add(S.Source);
    }
    R.HPDamage=FMath::Min(HP,Remaining);HP-=R.HPDamage;R.AfterHP=HP;Expire(Now);
    if(HP==0){bDead=true;++DeathCount;R.bDied=true;}return R;
}
}
