#include "U01AnimationEditor.h"
#if WITH_EDITOR
#include "U01Character.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/SkeletalMesh.h"
#include "ImageUtils.h"
#include "RenderingThread.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/MemoryWriter.h"

FString UU01AnimationEditor::InspectDHand(const FString& OutputDirectory)
{
    FString Project=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()); Project.ReplaceInline(TEXT("\\"),TEXT("/"));
    if(!Project.Contains(TEXT("/Artifacts/U01/D/Source/"))) return TEXT("ERROR: clone only");
    auto* World=GEditor->GetEditorWorldContext().World();
    if(!World || World->WorldType!=EWorldType::Editor) return TEXT("ERROR: requires explicit Editor preview world");
    auto* Class=LoadClass<AU01Character>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Character.BP_U01Character_C"));
    FActorSpawnParameters Params; Params.ObjectFlags|=RF_Transient;
    auto* Pawn=World->SpawnActor<AU01Character>(Class,FVector(0,-4000,98),FRotator::ZeroRotator,Params);
    auto* Mesh=Pawn->GetMesh();
    Mesh->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Mesh->bEnableUpdateRateOptimizations=false;
    Mesh->InitAnim(true);
    auto* CameraActor=World->SpawnActor<AActor>(Params);
    auto* Capture=NewObject<USceneCaptureComponent2D>(CameraActor);
    CameraActor->SetRootComponent(Capture); Capture->RegisterComponent();
    auto* Target=NewObject<UTextureRenderTarget2D>();
    Target->RenderTargetFormat=RTF_RGBA8; Target->InitAutoFormat(1024,1024);
    Capture->TextureTarget=Target; Capture->CaptureSource=SCS_FinalColorLDR;
    Capture->bCaptureEveryFrame=false; Capture->bCaptureOnMovement=false; Capture->FOVAngle=35;
    IFileManager::Get().MakeDirectory(*OutputDirectory,true);
    auto Root=MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("method"),TEXT("Editor pose preview only; NOT gameplay measurement. Own BP/mesh/AnimBP, explicit velocity and mode for diagnostic pose sampling."));
    TArray<TSharedPtr<FJsonValue>> Poses;
    for(int Phase=0;Phase<3;++Phase)
    {
        auto* Motor=Pawn->GetU01Movement();
        if(Phase==2){Motor->SetMovementMode(MOVE_Falling);Motor->Velocity=FVector(0,0,-300);Mesh->TickAnimation(.1,false);Mesh->RefreshBoneTransforms();}
        Motor->SetMovementMode(MOVE_Walking); Motor->Velocity=Phase==1?FVector(600,0,0):FVector::ZeroVector;
        Mesh->TickAnimation(Phase==2?.016f:.4f,false); Mesh->RefreshBoneTransforms(); Mesh->UpdateComponentToWorld();
        auto Json=MakeShared<FJsonObject>();
        const FString Name=Phase==0?TEXT("Idle"):Phase==1?TEXT("Run"):TEXT("Land");
        Json->SetStringField(TEXT("pose"),Name);
        const FTransform Hand=Mesh->GetSocketTransform(TEXT("hand_r"),RTS_World);
        Json->SetStringField(TEXT("handWorld"),Hand.ToString());
        Json->SetStringField(TEXT("socketRelativeToHand"),Mesh->GetSocketTransform(TEXT("U01_Sword_R"),RTS_World).GetRelativeTransform(Hand).ToString());
        auto Bones=MakeShared<FJsonObject>();
        const auto& Ref=Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
        for(int I=0;I<Ref.GetNum();++I)
        {
            const FString Bone=Ref.GetBoneName(I).ToString();
            if(Bone.EndsWith(TEXT("_r")) && (Bone.Contains(TEXT("index"))||Bone.Contains(TEXT("middle"))||Bone.Contains(TEXT("ring"))||Bone.Contains(TEXT("pinky"))||Bone.Contains(TEXT("thumb"))))
                Bones->SetStringField(Bone,Mesh->GetSocketTransform(Ref.GetBoneName(I),RTS_World).GetRelativeTransform(Hand).ToString());
        }
        Json->SetObjectField(TEXT("bonesInHandSpace"),Bones);
        const FVector Aim=(Hand.GetLocation()+Mesh->GetSocketLocation(TEXT("middle_01_r")))*.5;
        const FVector Directions[]={FVector(1,0,0),FVector(0,1,0),FVector(0,0,1)};
        const TCHAR* Angles[]={TEXT("Front"),TEXT("Side"),TEXT("Top")};
        for(int View=0;View<3;++View)
        {
            Capture->SetWorldLocation(Aim+Directions[View]*42);
            Capture->SetWorldRotation((Aim-Capture->GetComponentLocation()).Rotation());
            Mesh->MarkRenderDynamicDataDirty(); World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
            Capture->CaptureScene(); FlushRenderingCommands();
            TArray64<uint8> Png; FMemoryWriter64 Writer(Png);
            if(!FImageUtils::ExportRenderTarget2DAsPNG(Target,Writer)||!FFileHelper::SaveArrayToFile(Png,*(OutputDirectory/(Name+TEXT("-")+Angles[View]+TEXT(".png")))))
                return TEXT("ERROR: capture export");
        }
        Poses.Add(MakeShared<FJsonValueObject>(Json));
    }
    Root->SetArrayField(TEXT("poses"),Poses);
    FString Text; FJsonSerializer::Serialize(Root.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    FFileHelper::SaveStringToFile(Text,*(OutputDirectory/TEXT("Hand.json")));
    World->DestroyActor(Pawn); World->DestroyActor(CameraActor);
    return TEXT("SUCCESS: nine hand closeups and hand-space diagnostic transforms");
}
#else
FString UU01AnimationEditor::InspectDHand(const FString&) { return TEXT("ERROR: editor only"); }
#endif
