#include "U02CollisionLab.h"
#include "U02LabDummy.h"
#include "U02NetworkState.h"
#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/TargetPoint.h"
#include "Engine/World.h"
AU02CollisionLab::AU02CollisionLab()
{RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));}
void AU02CollisionLab::BeginPlay()
{
    Super::BeginPlay();
    const FString Map=GetWorld()->GetMapName();if(!Map.EndsWith(TEXT("L_CharacterCombatLab"))&&!Map.EndsWith(TEXT("L_NetworkLab")))return;
    if(HasAuthority()&&Map.EndsWith(TEXT("L_NetworkLab")))GetWorld()->SpawnActor<AU02NetworkState>();
    auto Box=[&](FVector P,FVector Half)
    {
        auto* Shape=NewObject<UBoxComponent>(this,FName(*FString::Printf(TEXT("CombatBox_%d_%d_%d"),FMath::RoundToInt(P.X),FMath::RoundToInt(P.Y),FMath::RoundToInt(P.Z))));Shape->SetNetAddressable();Shape->SetMobility(EComponentMobility::Static);Shape->SetBoxExtent(Half);Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Shape->SetCollisionResponseToAllChannels(ECR_Block);Shape->SetCollisionResponseToChannel(ECC_GameTraceChannel1,ECR_Ignore);
        Shape->SetupAttachment(RootComponent);Shape->SetRelativeLocation(P);Shape->RegisterComponent();Shape->SetHiddenInGame(false);Shape->ShapeColor=FColor::Cyan;
        auto* Visual=NewObject<UStaticMeshComponent>(this);Visual->SetupAttachment(RootComponent);
        Visual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
        Visual->SetRelativeLocation(P);Visual->SetRelativeScale3D(Half*.02);Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);Visual->RegisterComponent();
    };
    for(int Lane=0;Lane<4;++Lane)
    {
        const FVector Base=GetActorLocation()+FVector(0,-1000*Lane,0);
        Box(Base-GetActorLocation()+FVector(300,0,-50),FVector(600,300,50));
        if(HasAuthority()) { auto* Point=GetWorld()->SpawnActor<ATargetPoint>(Base+FVector(0,0,110),FRotator::ZeroRotator);
        Point->Tags.Add(FName(*FString::Printf(TEXT("U01C_Reset_CombatD%d"),Lane+1))); }
        auto* Label=NewObject<UTextRenderComponent>(this);Label->SetupAttachment(RootComponent);Label->SetRelativeLocation(Base-GetActorLocation()+FVector(250,0,220));
        Label->SetText(FText::FromString(FString::Printf(TEXT("U02-E %d | confirmed damage / lab dummy"),Lane+1)));Label->SetWorldSize(24);Label->SetRelativeRotation(FRotator(0,180,0));Label->RegisterComponent();
        if(HasAuthority())GetWorld()->SpawnActor<AU02LabDummy>(Base+FVector(150,Lane==0?-35:0,0),FRotator::ZeroRotator);
        if(HasAuthority()&&Lane==0)GetWorld()->SpawnActor<AU02LabDummy>(Base+FVector(150,35,0),FRotator::ZeroRotator);
        if(Lane==1)Box(Base-GetActorLocation()+FVector(75,0,110),FVector(10,200,110));
        if(Lane==2)Box(Base-GetActorLocation()+FVector(75,0,50),FVector(10,200,50));
        if(Lane==3){Box(Base-GetActorLocation()+FVector(75,-60,110),FVector(10,80,110));Box(Base-GetActorLocation()+FVector(110,-130,110),FVector(45,10,110));}
    }
}
