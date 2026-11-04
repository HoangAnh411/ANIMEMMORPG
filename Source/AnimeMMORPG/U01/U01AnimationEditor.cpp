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
        TArray<UObject*> Nested; GetObjectsWithOuter(Clip,Nested,true);
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
    Blend->ValidateSampleData(); Blend->PostEditChange();
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
