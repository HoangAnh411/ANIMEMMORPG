#include "U02HurtboxComponent.h"
#include "U02CollisionWorld.h"
#include "U02CombatComponent.h"
#include "U01/U01Character.h"
#include "Engine/World.h"

UU02HurtboxComponent::UU02HurtboxComponent()
{
    InitSphereRadius(35);bWantsOnUpdateTransform=true;
    SetCollisionEnabled(ECollisionEnabled::QueryOnly);SetGenerateOverlapEvents(false);
    SetCollisionObjectType(ECC_GameTraceChannel1);SetCollisionResponseToAllChannels(ECR_Ignore);
    SetCollisionResponseToChannel(ECC_GameTraceChannel1,ECR_Overlap);
    SetCanEverAffectNavigation(false);
}
void UU02HurtboxComponent::BeginPlay()
{
    Super::BeginPlay();
    if(GetOwner()->HasAuthority())if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())W->RegisterHurtbox(this);
}
void UU02HurtboxComponent::EndPlay(EEndPlayReason::Type Reason)
{
    if(auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>())W->UnregisterHurtbox(this);
    Super::EndPlay(Reason);
}
void UU02HurtboxComponent::OnUpdateTransform(EUpdateTransformFlags Flags,ETeleportType Teleport)
{
    Super::OnUpdateTransform(Flags,Teleport);
    if(Teleport!=ETeleportType::None)++ContinuityEpoch;
}
AnimeMMORPG::U02::FLifeId UU02HurtboxComponent::GetSubject() const
{
    if(const auto* C=Cast<AU01Character>(GetOwner()))
        return {C->NetworkPawnId,C->Combat->GetCombatSnapshot().LifeGeneration};
    return FixtureSubject;
}
