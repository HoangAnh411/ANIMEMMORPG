#include "U03AnimationEditor.h"
#if WITH_EDITOR
#include "U03Encounter.h"
#include "FileHelpers.h"
#include "Builders/CubeBuilder.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "EngineUtils.h"
#endif
FString UU03AnimationEditor::BuildC2Lab()
{
#if WITH_EDITOR
    // Isolated commandlet only. Never author into the user's running Editor world.
    if(!IsRunningCommandlet())return TEXT("ERROR: C2 authoring requires isolated commandlet");
    for(const FString Map:{TEXT("L_CharacterCombatLab"),TEXT("L_NetworkLab")})
    {
        const FString Path=TEXT("/Game/AnimeMMORPG/Maps/")+Map;
        auto* W=UEditorLoadingAndSavingUtils::LoadMap(Path);if(!W)return TEXT("ERROR: load ")+Map;
        for(TActorIterator<AActor> A(W);A;++A)if(A->ActorHasTag(TEXT("U03C2Authored")))return TEXT("ERROR: C2 content already exists; no blind overwrite");
        W->GetWorldSettings()->DefaultGameMode=AU03EncounterGameMode::StaticClass();
        auto Box=[&](FVector Position,FVector Half)
        {
            auto* A=W->SpawnActor<AStaticMeshActor>(Position,FRotator::ZeroRotator);A->Tags.Add(TEXT("U03C2Authored"));
            auto* C=A->GetStaticMeshComponent();C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
            A->SetActorScale3D(Half*.02);C->SetCollisionProfileName(TEXT("BlockAll"));C->SetCanEverAffectNavigation(true);return A;
        };
        for(int Station=0;Station<4;++Station)
        {
            const FVector Base(15000,Station*5000,0);
            Box(Base+FVector(0,0,-50),FVector(2400,2400,50));
            // Off-center solid obstacle leaves a valid path on both sides and back to spawn.
            Box(Base+FVector(900,400,140),FVector(30,300,140));
            auto* V=W->SpawnActor<ANavMeshBoundsVolume>(Base+FVector(0,0,300),FRotator::ZeroRotator);V->Tags.Add(TEXT("U03C2Authored"));
            auto* Builder=NewObject<UCubeBuilder>(V);Builder->X=4800;Builder->Y=4800;Builder->Z=1000;
            if(!Builder->Build(W,V))return TEXT("ERROR: navigation bounds brush");
            if(auto* Nav=UNavigationSystemV1::GetCurrent(W))Nav->OnNavigationBoundsUpdated(V);
        }
        if(auto* Nav=UNavigationSystemV1::GetCurrent(W))
        {Nav->Build();for(TActorIterator<ANavigationData> Data(W);Data;++Data)Data->EnsureBuildCompletion();}
        else return TEXT("ERROR: missing lab navigation system");
        if(!UEditorLoadingAndSavingUtils::SaveMap(W,Path))return TEXT("ERROR: save ")+Map;
    }
    return TEXT("SUCCESS: C2 GameMode, four separated lab platforms, solid obstacles and built navigation; regression stations preserved");
#else
    return TEXT("ERROR: editor only");
#endif
}
