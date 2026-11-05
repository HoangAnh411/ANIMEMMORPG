#include "U01Character.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"

class FSavedMove_U01 final : public FSavedMove_Character
{
public:
    bool Sprint=false,Held=false,Locked=false,PreviousNetworkHeld=false;
    uint8 SavedLocks=0;
    double Clock=0;
    AnimeMMORPG::U01::FJumpWindow Window;
    virtual void Clear() override
    {
        Super::Clear();Sprint=Held=Locked=PreviousNetworkHeld=false;SavedLocks=0;Clock=0;Window.ResetSession();
    }
    virtual uint8 GetCompressedFlags() const override
    {
        return (Super::GetCompressedFlags()&~FLAG_JumpPressed)|(Sprint?FLAG_Custom_0:0)|(Held?FLAG_Custom_1:0)|(Locked?FLAG_Custom_2:0);
    }
    virtual bool CanCombineWith(const FSavedMovePtr& Other,ACharacter* InCharacter,float MaxDelta) const override
    {
        const auto* Move=static_cast<const FSavedMove_U01*>(Other.Get());
        return Sprint==Move->Sprint&&Held==Move->Held&&Locked==Move->Locked&&Super::CanCombineWith(Other,InCharacter,MaxDelta);
    }
    virtual void SetMoveFor(ACharacter* InCharacter,float Dt,FVector const& NewAccel,FNetworkPredictionData_Client_Character& Data) override
    {
        Super::SetMoveFor(InCharacter,Dt,NewAccel,Data);
        auto* Motor=CastChecked<AU01Character>(InCharacter)->GetU01Movement();
        Sprint=Motor->bSprintRequested;Held=Motor->JumpWindow.IsHeld();Locked=(Motor->LockMask&1)!=0;
        SavedLocks=Motor->LockMask;Clock=Motor->SimulationSeconds;Window=Motor->JumpWindow;PreviousNetworkHeld=Motor->bNetworkJumpHeld;
    }
    virtual void PrepMoveFor(ACharacter* InCharacter) override
    {
        Super::PrepMoveFor(InCharacter);
        auto* Motor=CastChecked<AU01Character>(InCharacter)->GetU01Movement();
        Motor->bSprintRequested=Sprint;Motor->LockMask=SavedLocks;Motor->SimulationSeconds=Clock;
        Motor->JumpWindow=Window;Motor->bNetworkJumpHeld=PreviousNetworkHeld;
    }
};
class FPredictionData_U01 final : public FNetworkPredictionData_Client_Character
{
public:
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
    const bool Result=Super::ClientUpdatePositionAfterServerUpdate();
    if(Result)++CorrectionCount;
    return Result;
}
void AU01Character::BeginPlay()
{
    Super::BeginPlay();
    if(HasAuthority())NetworkPawnId=FGuid::NewGuid();
}
void AU01Character::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const
{
    Super::GetLifetimeReplicatedProps(Out);
    DOREPLIFETIME(AU01Character,NetworkPawnId);
    DOREPLIFETIME_CONDITION(AU01Character,bNetSprinting,COND_SimulatedOnly);
}
