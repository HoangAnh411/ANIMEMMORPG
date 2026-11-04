#include "U01AnimationEditor.h"
#include "U01AnimInstance.h"
#include "U01Character.h"
#if WITH_EDITOR
#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace1D.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkeletalMeshSocket.h"
#include "Engine/StaticMesh.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Factories/AnimBlueprintFactory.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_SequencePlayer.h"
#include "AnimGraphNode_BlendSpacePlayer.h"
#include "AnimGraphNode_BlendListByInt.h"
#include "K2Node_VariableGet.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "Misc/Paths.h"
#include "Misc/PackageName.h"
#include "ControlRig.h"
#include "ControlRigObjectBinding.h"
#include "UObject/UObjectHash.h"
#include "Animation/PoseAsset.h"
#include "AnimGraphNode_PoseByName.h"
#include "AnimGraphNode_LayeredBoneBlend.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

namespace
{
const FString DRoot = TEXT("/Game/AnimeMMORPG/U01/Animation");
template<class T> T* DuplicateD(const TCHAR* Source, const TCHAR* Name)
{
    auto* Original = LoadObject<T>(nullptr, Source);
    check(Original);
    return CastChecked<T>(FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().DuplicateAsset(Name, DRoot, Original));
}
bool SaveD(UObject* Asset)
{
    Asset->MarkPackageDirty();
    FSavePackageArgs Args; Args.TopLevelFlags = RF_Public | RF_Standalone;
    return UPackage::SavePackage(Asset->GetOutermost(), Asset,
        *FPackageName::LongPackageNameToFilename(Asset->GetOutermost()->GetName(), FPackageName::GetAssetPackageExtension()), Args);
}
template<class T> T* Node(UEdGraph* Graph, int32 X, int32 Y)
{
    auto* Result = NewObject<T>(Graph);
    Graph->AddNode(Result, false, false);
    Result->CreateNewGuid(); Result->NodePosX=X; Result->NodePosY=Y;
    Result->PostPlacedNewNode(); Result->AllocateDefaultPins();
    return Result;
}
void Link(UEdGraph* Graph, UEdGraphNode* From, const TCHAR* Output, UEdGraphNode* To, const TCHAR* Input)
{
    auto* A=From->FindPin(Output); auto* B=To->FindPin(Input);
    checkf(A && B, TEXT("Missing anim pin %s -> %s"), Output, Input);
    check(Graph->GetSchema()->TryCreateConnection(A,B));
}
}
#endif

FString UU01AnimationEditor::BuildDAssets()
{
#if WITH_EDITOR
    FString Dir = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
    Dir.ReplaceInline(TEXT("\\"),TEXT("/"));
    if (!Dir.Contains(TEXT("/Artifacts/U01/D/Source/"))) return TEXT("ERROR: requires isolated D source clone");
    if (FPackageName::DoesPackageExist(DRoot + TEXT("/SK_U01"))) return TEXT("ERROR: refuses overwrite of D assets");
    auto* Skeleton=DuplicateD<USkeleton>(TEXT("/Game/Characters/Mannequins/Meshes/SK_Mannequin"),TEXT("SK_U01"));
    auto* Mesh=DuplicateD<USkeletalMesh>(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"),TEXT("SKM_U01"));
    Mesh->SetSkeleton(Skeleton);
    Mesh->SetPostProcessAnimBlueprint(nullptr); // Own graph supplies all poses; no source-skeleton post-process.
    Skeleton->SetPreviewMesh(Mesh);
    if (Skeleton->GetReferenceSkeleton().FindBoneIndex(TEXT("hand_r")) == INDEX_NONE) return TEXT("ERROR: hand_r missing");
    auto* Socket=NewObject<USkeletalMeshSocket>(Skeleton);
    Socket->SocketName=TEXT("U01_Sword_R"); Socket->BoneName=TEXT("hand_r");
    Socket->RelativeRotation=FRotator(0,0,90);
    Skeleton->Sockets.Add(Socket);
    const TCHAR* Paths[]={TEXT("MM_Idle"),TEXT("Walk/MF_Unarmed_Walk_Fwd"),TEXT("Jog/MF_Unarmed_Jog_Fwd"),TEXT("Jump/MM_Jump"),TEXT("Jump/MM_Fall_Loop"),TEXT("Jump/MM_Land")};
    const TCHAR* Names[]={TEXT("A_U01_Idle"),TEXT("A_U01_Walk"),TEXT("A_U01_Jog"),TEXT("A_U01_Jump"),TEXT("A_U01_Fall"),TEXT("A_U01_Land")};
    TArray<UAnimSequence*> Clips;
    double WalkSpeed=0, JogSpeed=0;
    for(int32 I=0;I<6;++I)
    {
        const FString Source=FString(TEXT("/Game/Characters/Mannequins/Anims/Unarmed/"))+Paths[I];
        auto* Clip=DuplicateD<UAnimSequence>(*Source,Names[I]);
        const double Speed=Clip->ExtractRootMotionFromRange(0,Clip->GetPlayLength(),FAnimExtractContext()).GetTranslation().Size2D()/Clip->GetPlayLength();
        if(I==1) WalkSpeed=Speed; if(I==2) JogSpeed=Speed;
        UE_LOG(LogTemp,Display,TEXT("U01D_ASSET %s length=%.6f authoredRootSpeed=%.6f cm/s"),*Source,Clip->GetPlayLength(),Speed);
        // UE5.8's duplicated sequencer data model can keep its transient FK rig bound
        // to the old skeleton. Rebind only nested, duplicated rigs before validation.
        TArray<UObject*> Nested; GetObjectsWithOuter(Clip,Nested,EGetObjectsFlags::IncludeNestedObjects);
        for(auto* Object:Nested) if(auto* Rig=Cast<UControlRig>(Object))
        {
            Rig->SetObjectBinding(MakeShared<FControlRigObjectBinding>());
            Rig->GetObjectBinding()->BindToObject(Skeleton);
        }
        Clip->SetSkeleton(Skeleton);
        Clip->bEnableRootMotion=true; Clip->bForceRootLock=true;
        Clip->RootMotionRootLock=ERootMotionRootLock::AnimFirstFrame;
        Clip->PostEditChange(); Clips.Add(Clip);
    }
    if (WalkSpeed<50 || JogSpeed<100 || 700/JogSpeed>2.5) return TEXT("ERROR: authored speeds outside bounded calibration");
    auto* Blend=NewObject<UBlendSpace1D>(CreatePackage(*(DRoot+TEXT("/BS_U01_Locomotion"))),TEXT("BS_U01_Locomotion"),RF_Public|RF_Standalone);
    Blend->SetSkeleton(Skeleton);
    // Editor axis/sample fields have no setter; edit reflected asset data, never source assets.
    auto* Axes=FindFProperty<FStructProperty>(UBlendSpace::StaticClass(),TEXT("BlendParameters")); check(Axes);
    auto* Axis=Axes->ContainerPtrToValuePtr<FBlendParameter>(Blend,0);
    Axis->DisplayName=TEXT("GroundSpeed"); Axis->Min=0; Axis->Max=700; Axis->GridNum=7;
    Blend->AddSample(Clips[0],FVector::ZeroVector);
    Blend->AddSample(Clips[1],FVector(WalkSpeed,0,0));
    Blend->AddSample(Clips[2],FVector(500,0,0));
    Blend->AddSample(Clips[2],FVector(700,0,0));
    auto* Samples=FindFProperty<FArrayProperty>(UBlendSpace::StaticClass(),TEXT("SampleData")); check(Samples);
    FScriptArrayHelper Helper(Samples,Samples->ContainerPtrToValuePtr<void>(Blend));
    reinterpret_cast<FBlendSample*>(Helper.GetRawPtr(2))->RateScale=500/JogSpeed;
    reinterpret_cast<FBlendSample*>(Helper.GetRawPtr(3))->RateScale=700/JogSpeed;
    Blend->ValidateSampleData(); Blend->ResampleData(); Blend->PostEditChange();
    FAssetRegistryModule::AssetCreated(Blend);
    auto* Factory=NewObject<UAnimBlueprintFactory>();
    Factory->ParentClass=UU01AnimInstance::StaticClass(); Factory->TargetSkeleton=Skeleton; Factory->PreviewSkeletalMesh=Mesh;
    auto* BP=CastChecked<UAnimBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().CreateAsset(TEXT("ABP_U01"),DRoot,UAnimBlueprint::StaticClass(),Factory));
    UEdGraph* Graph=nullptr; UAnimGraphNode_Root* Root=nullptr;
    for(auto G:BP->FunctionGraphs) for(auto N:G->Nodes) if(auto* R=Cast<UAnimGraphNode_Root>(N)) { Graph=G; Root=R; }
    if (!Graph || !Root) return TEXT("ERROR: missing AnimGraph root");
    auto* Select=Node<UAnimGraphNode_BlendListByInt>(Graph,-350,0);
    for(int32 I=0;I<3;++I) Select->Node.AddPose(); // Constructor + PostPlacedNewNode supply the first two.
    auto* Mode=FindFProperty<FEnumProperty>(FAnimNode_BlendListBase::StaticStruct(),TEXT("ChildUpateMode")); check(Mode);
    Mode->GetUnderlyingProperty()->SetIntPropertyValue(Mode->ContainerPtrToValuePtr<void>(&Select->Node),int64(EBlendListChildUpdateMode::ResetChildOnActivate));
    Select->ReconstructNode();
    auto* Phase=Node<UK2Node_VariableGet>(Graph,-650,-220);
    Phase->VariableReference.SetSelfMember(TEXT("PoseIndex")); Phase->ReconstructNode();
    Link(Graph,Phase,TEXT("PoseIndex"),Select,TEXT("ActiveChildIndex"));
    for(int32 I=0;I<5;++I)
    {
        UEdGraphNode* Player=nullptr;
        if(I==1)
        {
            auto* P=Node<UAnimGraphNode_BlendSpacePlayer>(Graph,-900,I*200);
            P->Node.SetBlendSpace(Blend); P->ReconstructNode(); Player=P;
            auto* Speed=Node<UK2Node_VariableGet>(Graph,-1200,I*200);
            Speed->VariableReference.SetSelfMember(TEXT("GroundSpeed")); Speed->ReconstructNode();
            Link(Graph,Speed,TEXT("GroundSpeed"),P,TEXT("X"));
        }
        else
        {
            auto* P=Node<UAnimGraphNode_SequencePlayer>(Graph,-900,I*200);
            P->Node.SetSequence(Clips[I==0 ? 0 : I+1]);
            P->Node.SetLoopAnimation(I==0 || I==3); P->ReconstructNode(); Player=P;
        }
        Link(Graph,Player,TEXT("Pose"),Select,*FString::Printf(TEXT("BlendPose_%d"),I));
    }
    Link(Graph,Select,TEXT("Pose"),Root,TEXT("Result"));
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
    FKismetEditorUtilities::CompileBlueprint(BP);
    if(BP->Status==BS_Error) return TEXT("ERROR: AnimBP compile failed");
    auto* CharacterBP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Character"));
    auto* Defaults=CastChecked<AU01Character>(CharacterBP->GeneratedClass->GetDefaultObject());
    Defaults->GetMesh()->SetSkeletalMeshAsset(Mesh);
    Defaults->GetMesh()->SetAnimInstanceClass(BP->GeneratedClass);
    auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    for(auto* Part:{Defaults->SwordBlade.Get(),Defaults->SwordGuard.Get(),Defaults->SwordGrip.Get()}) Part->SetStaticMesh(Cube);
    FKismetEditorUtilities::CompileBlueprint(CharacterBP);
    bool Saved=SaveD(Skeleton)&&SaveD(Mesh)&&SaveD(Blend)&&SaveD(BP)&&SaveD(CharacterBP);
    for(auto* Clip:Clips) Saved=SaveD(Clip)&&Saved;
    return Saved ? FString::Printf(TEXT("SUCCESS walk=%.6f jog=%.6f jogRates=%.6f/%.6f"),WalkSpeed,JogSpeed,500/JogSpeed,700/JogSpeed) : TEXT("ERROR: saving assets");
#else
    return TEXT("ERROR: editor only");
#endif
}

FString UU01AnimationEditor::FinalizeDBlendSpace()
{
#if WITH_EDITOR
    FString Dir=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()); Dir.ReplaceInline(TEXT("\\"),TEXT("/"));
    if(!Dir.Contains(TEXT("/Artifacts/U01/D/Source/"))) return TEXT("ERROR: requires isolated D source clone");
    auto* Blend=LoadObject<UBlendSpace1D>(nullptr,*(DRoot+TEXT("/BS_U01_Locomotion")));
    if(!Blend) return TEXT("ERROR: missing own D BlendSpace");
    Blend->ValidateSampleData(); Blend->ResampleData(); Blend->PostEditChange();
    return SaveD(Blend)?TEXT("SUCCESS: serialized D BlendSpace interpolation rebuilt"):TEXT("ERROR: save failed");
#else
    return TEXT("ERROR: editor only");
#endif
}

FString UU01AnimationEditor::ReviseDAssets(const FString& ConfigFile)
{
#if WITH_EDITOR
    FString Dir=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()); Dir.ReplaceInline(TEXT("\\"),TEXT("/"));
    if(!Dir.Contains(TEXT("/Artifacts/U01/D/Source/"))) return TEXT("ERROR: clone only");
    auto* BP=LoadObject<UAnimBlueprint>(nullptr,*(DRoot+TEXT("/ABP_U01")));
    UEdGraph* Graph=nullptr; UAnimGraphNode_Root* Root=nullptr; UAnimGraphNode_BlendListByInt* Select=nullptr;
    UAnimGraphNode_LayeredBoneBlend* Layer=nullptr;
    for(auto G:BP->FunctionGraphs) for(auto N:G->Nodes)
    {
        if(auto* R=Cast<UAnimGraphNode_Root>(N)){Graph=G;Root=R;}
        if(auto* S=Cast<UAnimGraphNode_BlendListByInt>(N))Select=S;
        if(auto* L=Cast<UAnimGraphNode_LayeredBoneBlend>(N))Layer=L;
    }
    if(!Root||!Select)return TEXT("ERROR: missing own pose selector");
    auto* Times=FindFProperty<FArrayProperty>(FAnimNode_BlendListBase::StaticStruct(),TEXT("BlendTime"));
    FScriptArrayHelper TimeValues(Times,Times->ContainerPtrToValuePtr<void>(&Select->Node));
    if(TimeValues.Num()!=5)return TEXT("ERROR: expected five poses");
    for(int I=0;I<5;++I)*reinterpret_cast<float*>(TimeValues.GetRawPtr(I))=.10f;
    Select->ReconstructNode();
    for(auto* Pin:Select->Pins)if(Pin->PinName.ToString().StartsWith(TEXT("BlendTime_")))Pin->DefaultValue=TEXT("0.100000");
    if(!ConfigFile.IsEmpty())
    {
        FString Text;TSharedPtr<FJsonObject> Config;
        if(!FFileHelper::LoadFileToString(Text,*ConfigFile)||!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Config))return TEXT("ERROR: grip config");
        auto* Skeleton=LoadObject<USkeleton>(nullptr,*(DRoot+TEXT("/SK_U01")));
        auto* Socket=Skeleton->FindSocket(TEXT("U01_Sword_R"));
        const auto& Loc=Config->GetArrayField(TEXT("socketLocation"));const auto& Rot=Config->GetArrayField(TEXT("socketRotation"));
        Socket->RelativeLocation=FVector(Loc[0]->AsNumber(),Loc[1]->AsNumber(),Loc[2]->AsNumber());
        Socket->RelativeRotation=FRotator(Rot[0]->AsNumber(),Rot[1]->AsNumber(),Rot[2]->AsNumber());
        const auto& Ref=Skeleton->GetReferenceSkeleton();TArray<FTransform> Pose=Ref.GetRefBonePose();
        const auto& Fingers=Config->GetArrayField(TEXT("fingers"));
        if(Fingers.Num()!=15)return TEXT("ERROR: expected 15 finger joints only");
        for(auto Value:Fingers)
        {
            const auto J=Value->AsObject();const FString Bone=J->GetStringField(TEXT("bone"));
            if(!Bone.EndsWith(TEXT("_r"))||!(Bone.StartsWith(TEXT("index_0"))||Bone.StartsWith(TEXT("middle_0"))||Bone.StartsWith(TEXT("ring_0"))||Bone.StartsWith(TEXT("pinky_0"))||Bone.StartsWith(TEXT("thumb_0"))))return TEXT("ERROR: non-finger change");
            const int Index=Ref.FindBoneIndex(*Bone);if(Index==INDEX_NONE)return TEXT("ERROR: finger missing");
            const auto& R=J->GetArrayField(TEXT("rotation"));
            Pose[Index].SetRotation((Pose[Index].GetRotation()*FRotator(R[0]->AsNumber(),R[1]->AsNumber(),R[2]->AsNumber()).Quaternion()).GetNormalized());
        }
        auto* Grip=LoadObject<UPoseAsset>(nullptr,*(DRoot+TEXT("/PA_U01_RightGrip")));
        if(!Grip){Grip=NewObject<UPoseAsset>(CreatePackage(*(DRoot+TEXT("/PA_U01_RightGrip"))),TEXT("PA_U01_RightGrip"),RF_Public|RF_Standalone);Grip->SetSkeleton(Skeleton);FAssetRegistryModule::AssetCreated(Grip);}
        Grip->AddReferencePose(TEXT("RightGrip"),Ref);
        auto* Container=FindFProperty<FStructProperty>(UPoseAsset::StaticClass(),TEXT("PoseContainer"))->ContainerPtrToValuePtr<FPoseDataContainer>(Grip);
        Container->FindPoseData(TEXT("RightGrip"))->SourceLocalSpacePose=Pose;
        Grip->ConvertSpace(false,INDEX_NONE);
        if(!Layer)
        {
            auto* GripNode=Node<UAnimGraphNode_PoseByName>(Graph,-200,1000);
            GripNode->Node.SetPoseAsset(Grip);GripNode->Node.PoseName=TEXT("RightGrip");GripNode->ReconstructNode();
            Layer=Node<UAnimGraphNode_LayeredBoneBlend>(Graph,100,0);
            Layer->Node.LayerSetup.SetNum(1);Layer->Node.BlendWeights.SetNum(1);Layer->Node.BlendWeights[0]=1;
            for(const TCHAR* Bone:{TEXT("thumb_01_r"),TEXT("index_01_r"),TEXT("middle_01_r"),TEXT("ring_01_r"),TEXT("pinky_01_r")})
            {FBranchFilter Filter;Filter.BoneName=Bone;Filter.BlendDepth=0;Layer->Node.LayerSetup[0].BranchFilters.Add(Filter);}
            Layer->ReconstructNode();
            Root->FindPin(TEXT("Result"))->BreakAllPinLinks();
            Link(Graph,Select,TEXT("Pose"),Layer,TEXT("BasePose"));
            Link(Graph,GripNode,TEXT("Pose"),Layer,TEXT("BlendPoses_0"));
            Link(Graph,Layer,TEXT("Pose"),Root,TEXT("Result"));
        }
        if(!SaveD(Grip)||!SaveD(Skeleton))return TEXT("ERROR: grip/socket save");
    }
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
    if(BP->Status==BS_Error||!SaveD(BP))return TEXT("ERROR: revised AnimBP compile/save");
    return TEXT("SUCCESS: explicit 0.100s pose blends; optional finger-only grip/socket revision");
#else
    return TEXT("ERROR: editor only");
#endif
}
