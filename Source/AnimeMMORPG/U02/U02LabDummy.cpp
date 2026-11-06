#include "U02LabDummy.h"
#include "U02HurtboxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"
AU02LabDummy::AU02LabDummy()
{
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Body=CreateDefaultSubobject<UU02HurtboxComponent>(TEXT("Body"));Body->SetupAttachment(RootComponent);Body->SetRelativeLocation(FVector(0,0,70));Body->InitSphereRadius(35);Body->StableHurtboxId=1;
    Head=CreateDefaultSubobject<UU02HurtboxComponent>(TEXT("Head"));Head->SetupAttachment(RootComponent);Head->SetRelativeLocation(FVector(0,0,145));Head->InitSphereRadius(20);Head->StableHurtboxId=2;
    Visual=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));Visual->SetupAttachment(RootComponent);Visual->SetRelativeLocation(FVector(0,0,90));Visual->SetRelativeScale3D(FVector(.5,.5,1.8));Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Mesh(TEXT("/Engine/BasicShapes/Cube.Cube"));if(Mesh.Succeeded())Visual->SetStaticMesh(Mesh.Object);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);Visual->SetCollisionResponseToAllChannels(ECR_Ignore);
}
void AU02LabDummy::BeginPlay()
{
    if(HasAuthority())
    {
        if(!NetworkPawnId.IsValid())NetworkPawnId=FGuid::NewGuid();
        Body->SetFixtureSubject({NetworkPawnId,LifeGeneration});Head->SetFixtureSubject({NetworkPawnId,LifeGeneration});
    }
    Super::BeginPlay();
}
bool AU02LabDummy::ResetLabCombat()
{
    if(!HasAuthority())return false;++LifeGeneration;
    Body->SetFixtureSubject({NetworkPawnId,LifeGeneration});Head->SetFixtureSubject({NetworkPawnId,LifeGeneration});return true;
}
