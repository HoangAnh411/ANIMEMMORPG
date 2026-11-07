#include "U02VitalComponent.h"
#include "U02LabDummy.h"
#include "U02CombatComponent.h"
#include "U02CollisionWorld.h"
#include "U01/U01Character.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "Dom/JsonObject.h"
using namespace AnimeMMORPG::U02;
UU02VitalComponent::UU02VitalComponent() {SetIsReplicatedByDefault(true);}
void UU02VitalComponent::BeginPlay()
{
    Super::BeginPlay();if(!GetOwner()->HasAuthority())return;
    State.MaxHP=State.HP=Cast<AU02LabDummy>(GetOwner())?600:1000;Publish(GetWorld()->GetTimeSeconds());
}
void UU02VitalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(UU02VitalComponent,Snapshot);}
FLifeId UU02VitalComponent::GetLife() const
{
    if(const auto* C=Cast<AU01Character>(GetOwner()))return {C->NetworkPawnId,C->Combat->GetCombatSnapshot().LifeGeneration};
    if(const auto* D=Cast<AU02LabDummy>(GetOwner()))return {D->NetworkPawnId,D->LifeGeneration};return {};
}
bool UU02VitalComponent::IsAlive(FLifeId Life) const
{return GetOwner()->HasAuthority()&&!GetOwner()->IsActorBeingDestroyed()&&GetLife()==Life&&State.Generation==Life.Generation&&!State.bDead&&State.HP>0;}
FDamageResult UU02VitalComponent::ApplyResolved(const FHitCandidate& Hit,double Attack,double Roll)
{
    if(!IsAlive(Hit.Id.Target))return {};
    auto R=State.Apply(Hit.RawDamage,Attack,Roll,Hit.TimestampSeconds);
    if(!R.bApplied)return R;
    Publish(Hit.TimestampSeconds);
    if(R.bDied)
    {
        // Ledger invalidation happens synchronously BEFORE the next sorted event.
        GetWorld()->GetSubsystem<UU02CollisionWorld>()->MarkDead(Hit.Id.Target);
        if(auto* C=Cast<AU01Character>(GetOwner()))C->Combat->HandleDefeat(Hit.TimestampSeconds);
    }
    if(auto* C=Cast<AU01Character>(GetOwner()))if(R.Damage>0)C->GetU01Movement()->SetMotorLock(EU01MotorLock::Interacting,false);
    Publish(Hit.TimestampSeconds);return R;
}
void UU02VitalComponent::Publish(double Now)
{
    Snapshot.HP=State.HP;Snapshot.MaxHP=State.MaxHP;Snapshot.Shield=State.ShieldAt(Now);Snapshot.Generation=State.Generation;Snapshot.bDead=State.bDead;Snapshot.DeathCount=State.DeathCount;
    GetOwner()->ForceNetUpdate();
}
void UU02VitalComponent::Refresh(double Now)
{if(GetOwner()->HasAuthority()){State.Expire(Now);if(Snapshot.Shield!=State.ShieldAt(Now))Publish(Now);}}
bool UU02VitalComponent::ResetLabCombat(uint64 Generation)
{
    if(!GetOwner()->HasAuthority()||!State.Reset(Generation,State.MaxHP))return false;
    Publish(GetWorld()->GetTimeSeconds());
    if(auto* C=Cast<AU01Character>(GetOwner()))C->GetU01Movement()->SetMotorLock(EU01MotorLock::Defeated,false);return true;
}
bool UU02VitalComponent::AddFixtureShield(uint64 Source,int32 Capacity,double Deadline,double Now)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if(!GetOwner()->HasAuthority()||!State.AddShield(Source,Capacity,Deadline,Now))return false;Publish(Now);return true;
#endif
}
TSharedRef<FJsonObject> UU02VitalComponent::GetDiagnostics() const
{
    auto J=MakeShared<FJsonObject>();J->SetNumberField(TEXT("hp"),Snapshot.HP);J->SetNumberField(TEXT("maxHP"),Snapshot.MaxHP);J->SetNumberField(TEXT("shield"),Snapshot.Shield);J->SetNumberField(TEXT("lifeGeneration"),Snapshot.Generation);J->SetBoolField(TEXT("dead"),Snapshot.bDead);J->SetNumberField(TEXT("deathCount"),Snapshot.DeathCount);return J;
}

void UU02VitalComponent::OnRep_Snapshot()
{if(auto* C=Cast<AU01Character>(GetOwner()))C->GetU01Movement()->SetMotorLock(EU01MotorLock::Defeated,Snapshot.bDead);}
