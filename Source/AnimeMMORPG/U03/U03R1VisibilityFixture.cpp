#include "U03R1VisibilityFixture.h"
#include "U03Encounter.h"
#include "U01/U01PlayerController.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
AU03R1VisibilityWall::AU03R1VisibilityWall()
{
    bReplicates=true;bAlwaysRelevant=true;PrimaryActorTick.bCanEverTick=true;
    GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
    GetStaticMeshComponent()->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    GetStaticMeshComponent()->SetCollisionProfileName(TEXT("BlockAll"));GetStaticMeshComponent()->SetCanEverAffectNavigation(false);
}
void AU03R1VisibilityWall::Configure(FVector InOrigin,bool Partial){Origin=InOrigin;bPartial=Partial;Apply();ForceNetUpdate();}
void AU03R1VisibilityWall::Apply()
{SetActorLocation(Origin+FVector(-200,bPartial?20:0,140));SetActorScale3D(FVector(.2,bPartial?.3:2,2.8));}
void AU03R1VisibilityWall::Tick(float Dt){Super::Tick(Dt);if(HasAuthority()&&!IsValid(GetOwner()))Destroy();}
void AU03R1VisibilityWall::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const
{Super::GetLifetimeReplicatedProps(Out);DOREPLIFETIME(AU03R1VisibilityWall,Origin);DOREPLIFETIME(AU03R1VisibilityWall,bPartial);}
void AU01PlayerController::U03R1Scene(){if(FParse::Param(FCommandLine::Get(),TEXT("U03R1VisibilityProbe")))ServerU03R1Scene(false);}
void AU01PlayerController::U03R1Partial(){if(FParse::Param(FCommandLine::Get(),TEXT("U03R1VisibilityProbe")))ServerU03R1Scene(true);}
void AU01PlayerController::ServerU03R1Scene_Implementation(bool Partial)
{
    if(!FParse::Param(FCommandLine::Get(),TEXT("U03R1VisibilityProbe"))||!GetWorld()->GetMapName().Contains(TEXT("L_NetworkLab")))return;
    auto* E=AU03Encounter::ForSubject(GetPawn());if(!E||E->GetOwner()!=this)return;
    if(!R1Wall){FActorSpawnParameters P;P.Owner=this;R1Wall=GetWorld()->SpawnActor<AU03R1VisibilityWall>(P);}
    R1Wall->Configure(FVector(15000,E->GetSnapshot().Station*5000,0),Partial);ClientU03R1Camera();
}
void AU01PlayerController::ClientU03R1Camera_Implementation()
{
    if(!FParse::Param(FCommandLine::Get(),TEXT("U03R1VisibilityProbe"))||!GetPawn())return;
    if(!R1Camera)R1Camera=GetWorld()->SpawnActor<ACameraActor>();
    R1Camera->AttachToActor(GetPawn(),FAttachmentTransformRules::KeepRelativeTransform);
    R1Camera->SetActorRelativeLocation(FVector(-600,0,120));R1Camera->SetActorRotation(FRotator(-9,0,0));SetViewTarget(R1Camera);
}
