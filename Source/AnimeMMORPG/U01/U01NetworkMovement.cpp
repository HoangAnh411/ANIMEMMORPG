#include "U01Character.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "U02/U02CombatComponent.h"

class FSavedMove_U01 final : public FSavedMove_Character
{
public:
    using Super=FSavedMove_Character;
    bool Sprint=false,Held=false,Locked=false,PreviousNetworkHeld=false;
    uint8 SavedLocks=0;
    bool CombatLocked=false;
    uint64 CombatAction=0,CombatLife=0;
    double Clock=0;
    AnimeMMORPG::U01::FJumpWindow Window;
    virtual void Clear() override
    {
        Super::Clear();Sprint=Held=Locked=PreviousNetworkHeld=false;SavedLocks=0;Clock=0;Window.ResetSession();
        CombatLocked=false;CombatAction=CombatLife=0;
    }
    virtual uint8 GetCompressedFlags() const override
    {
        return (Super::GetCompressedFlags()&~FLAG_JumpPressed)|(Sprint?FLAG_Custom_0:0)|(Held?FLAG_Custom_1:0)|(Locked?FLAG_Custom_2:0);
    }
    virtual bool CanCombineWith(const FSavedMovePtr& Other,ACharacter* InCharacter,float MaxDelta) const override
    {
        const auto* Move=static_cast<const FSavedMove_U01*>(Other.Get());
        return Sprint==Move->Sprint&&Held==Move->Held&&Locked==Move->Locked&&CombatLocked==Move->CombatLocked
            &&CombatAction==Move->CombatAction&&CombatLife==Move->CombatLife&&Super::CanCombineWith(Other,InCharacter,MaxDelta);
    }
    virtual void SetMoveFor(ACharacter* InCharacter,float Dt,FVector const& NewAccel,FNetworkPredictionData_Client_Character& Data) override
    {
        Super::SetMoveFor(InCharacter,Dt,NewAccel,Data);
        auto* Motor=CastChecked<AU01Character>(InCharacter)->GetU01Movement();
        Sprint=Motor->bSprintRequested;Held=Motor->JumpWindow.IsHeld();Locked=(Motor->LockMask&1)!=0;
        SavedLocks=Motor->LockMask;Clock=Motor->SimulationSeconds;Window=Motor->JumpWindow;PreviousNetworkHeld=Motor->bNetworkJumpHeld;
        CombatLocked=Motor->bCombatAuthorityLocked;
        if(auto* Combat=CastChecked<AU01Character>(InCharacter)->Combat.Get())
        { CombatAction=Combat->GetCombatSnapshot().ActionSequence;CombatLife=Combat->GetCombatSnapshot().LifeGeneration; }
    }
    virtual void PrepMoveFor(ACharacter* InCharacter) override
    {
        Super::PrepMoveFor(InCharacter);
        auto* Motor=CastChecked<AU01Character>(InCharacter)->GetU01Movement();
        // Saved local Control may replay; authority Interacting/Defeated/Combat cannot be cleared or resurrected.
        const uint8 AuthorityLocks=Motor->LockMask & ~uint8(EU01MotorLock::Control);
        Motor->bSprintRequested=Sprint;Motor->LockMask=(SavedLocks & uint8(EU01MotorLock::Control))|AuthorityLocks;Motor->SimulationSeconds=Clock;
        Motor->JumpWindow=Window;Motor->bNetworkJumpHeld=PreviousNetworkHeld;
        Motor->SetControlLocked(Locked); // Clears replayed jump/sprint under ANY remaining authority lock.
    }
};
class FPredictionData_U01 final : public FNetworkPredictionData_Client_Character
{
public:
    using Super=FNetworkPredictionData_Client_Character;
    explicit FPredictionData_U01(const UCharacterMovementComponent& Motor):Super(Motor){}
    virtual FSavedMovePtr AllocateNewMove() override{return FSavedMovePtr(new FSavedMove_U01());}
};
FNetworkPredictionData_Client* UU01CharacterMovement::GetPredictionData_Client() const
{
    if(!ClientPredictionData)const_cast<UU01CharacterMovement*>(this)->ClientPredictionData=new FPredictionData_U01(*this);
    return ClientPredictionData;
}
void UU01CharacterMovement::UpdateFromCompressedFlags(uint8 Flags)
{
    // Engine JumpPressed is intentionally not an alternate path around our edge/window policy.
    Super::UpdateFromCompressedFlags(Flags&~FSavedMove_Character::FLAG_JumpPressed);
    SetControlLocked((Flags&FSavedMove_Character::FLAG_Custom_2)!=0);
    SetSprintRequested((Flags&FSavedMove_Character::FLAG_Custom_0)!=0);
    const bool Held=(Flags&FSavedMove_Character::FLAG_Custom_1)!=0;
    if(CharacterOwner&&CharacterOwner->HasAuthority())
    {
        if(Held&&!bNetworkJumpHeld)PressJump(SimulationSeconds);
        if(!Held)ReleaseJump();
    }
    bNetworkJumpHeld=Held;
}
bool UU01CharacterMovement::ClientUpdatePositionAfterServerUpdate()
{
    const auto* Data=GetPredictionData_Client_Character();
    const bool HadAdjustment=Data&&Data->bUpdatePosition;
    const bool Result=Super::ClientUpdatePositionAfterServerUpdate();
    if(HadAdjustment)++CorrectionCount;
    return Result;
}
void AU01Character::BeginPlay()
{
    // Components begin during Super; give the combat model its server identity first.
    if(HasAuthority()&&!NetworkPawnId.IsValid())NetworkPawnId=FGuid::NewGuid();
    Super::BeginPlay();
}
void AU01Character::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AU01Character,NetworkPawnId);
    DOREPLIFETIME_CONDITION(AU01Character,bNetSprinting,COND_SimulatedOnly);
}
