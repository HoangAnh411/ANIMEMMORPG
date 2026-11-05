#include "U02AnimationEditor.h"
#if WITH_EDITOR
#include "U01/U01AnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/PoseAsset.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMeshSocket.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_Slot.h"
#include "AnimGraphNode_LayeredBoneBlend.h"
#include "K2Node_VariableGet.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Misc/Paths.h"
#include "Misc/PackageName.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"

namespace
{
const FString CRoot=TEXT("/Game/AnimeMMORPG/U02/Animation");
bool SaveC(UObject* Obj)
{
    Obj->MarkPackageDirty();FSavePackageArgs A;A.TopLevelFlags=RF_Public|RF_Standalone;
    return UPackage::SavePackage(Obj->GetOutermost(),Obj,*FPackageName::LongPackageNameToFilename(Obj->GetOutermost()->GetName(),FPackageName::GetAssetPackageExtension()),A);
}
TArray<FTransform> PoseLocal(UPoseAsset* Asset)
{
    auto* Container=FindFProperty<FStructProperty>(UPoseAsset::StaticClass(),TEXT("PoseContainer"))->ContainerPtrToValuePtr<FPoseDataContainer>(Asset);
    auto* Array=FindFProperty<FArrayProperty>(FPoseDataContainer::StaticStruct(),TEXT("Poses"));
    FScriptArrayHelper H(Array,Array->ContainerPtrToValuePtr<void>(Container));check(H.Num()==1);
    return *FindFProperty<FArrayProperty>(FPoseData::StaticStruct(),TEXT("SourceLocalSpacePose"))->ContainerPtrToValuePtr<TArray<FTransform>>(H.GetRawPtr(0));
}
}
#endif

FString UU02AnimationEditor::AdjustCArmMask()
{
#if WITH_EDITOR
    FString Dir=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());Dir.ReplaceInline(TEXT("\\"),TEXT("/"));
    if(!Dir.Contains(TEXT("/Artifacts/U02/C/Source/")))return TEXT("ERROR: clone only");
    auto* BP=LoadObject<UAnimBlueprint>(nullptr,*(CRoot+TEXT("/ABP_U02")));if(!BP)return TEXT("ERROR: graph missing");
    int32 Count=0;
    for(auto G:BP->FunctionGraphs)for(auto N:TArray<TObjectPtr<UEdGraphNode>>(G->Nodes))if(auto* L=Cast<UAnimGraphNode_LayeredBoneBlend>(N))
        if(L->NodePosX==0&&L->Node.LayerSetup.Num()&&L->Node.LayerSetup[0].BranchFilters.Num()&&
            (L->Node.LayerSetup[0].BranchFilters[0].BoneName==TEXT("clavicle_r")||L->Node.LayerSetup[0].BranchFilters[0].BoneName==TEXT("upperarm_r")))
        {
            L->Node.LayerSetup[0].BranchFilters[0].BoneName=TEXT("upperarm_r");
            auto* Alpha=NewObject<UK2Node_VariableGet>(G);G->AddNode(Alpha,false,false);Alpha->CreateNewGuid();Alpha->VariableReference.SetSelfMember(TEXT("AttackBlendWeight"));Alpha->PostPlacedNewNode();Alpha->AllocateDefaultPins();
            if(!G->GetSchema()->TryCreateConnection(Alpha->FindPin(TEXT("AttackBlendWeight")),L->FindPin(TEXT("BlendWeights_0"))))return TEXT("ERROR: attack weight pin");
            ++Count;
        }
    if(Count!=1)return TEXT("ERROR: expected one attack mask");
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
    return BP->Status!=BS_Error&&SaveC(BP)?TEXT("SUCCESS: C arm mask adjusted"):TEXT("ERROR: compile/save");
#else
    return TEXT("ERROR: editor only");
#endif
}

FString UU02AnimationEditor::BuildCAssets()
{
#if WITH_EDITOR
    FString Dir=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());Dir.ReplaceInline(TEXT("\\"),TEXT("/"));
    if(!Dir.Contains(TEXT("/Artifacts/U02/C/Source/")))return TEXT("ERROR: isolated C clone only");
    if(FPackageName::DoesPackageExist(CRoot+TEXT("/A_U02_Attack1")))return TEXT("ERROR: refuses overwrite of authored C asset");
    auto* Skeleton=LoadObject<USkeleton>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/SK_U01"));
    auto* Carry=LoadObject<UPoseAsset>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/PA_U01_RightCarry"));
    auto* Grip=LoadObject<UPoseAsset>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/PA_U01_RightGrip"));
    auto* OriginalBP=LoadObject<UAnimBlueprint>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/ABP_U01"));
    if(!Skeleton||!Carry||!Grip||!OriginalBP)return TEXT("ERROR: accepted U01 assets missing");
    auto* BP=CastChecked<UAnimBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().DuplicateAsset(TEXT("ABP_U02"),CRoot,OriginalBP));
    const auto& Ref=Skeleton->GetReferenceSkeleton();
    TArray<FTransform> Base=PoseLocal(Carry),Fingers=PoseLocal(Grip);
    if(Base.Num()!=Ref.GetNum()||Fingers.Num()!=Ref.GetNum())return TEXT("ERROR: pose skeleton mismatch");
    for(int32 I=0;I<Ref.GetNum();++I)
    {
        const FString Name=Ref.GetBoneName(I).ToString();
        if(Name.EndsWith(TEXT("_r")) && (Name.StartsWith(TEXT("thumb_"))||Name.StartsWith(TEXT("index_"))||Name.StartsWith(TEXT("middle_"))||Name.StartsWith(TEXT("ring_"))||Name.StartsWith(TEXT("pinky_"))))Base[I]=Fingers[I];
    }
    const int32 Upper=Ref.FindBoneIndex(TEXT("upperarm_r")),Lower=Ref.FindBoneIndex(TEXT("lowerarm_r")),Hand=Ref.FindBoneIndex(TEXT("hand_r"));
    if(Upper<0||Lower<0||Hand<0)return TEXT("ERROR: arm chain missing");
    // Mesh component axes inherited U01: right=-X, forward=+Y, up=+Z.
    // Hand/blade key poses authored here, no third-party attack clip.
    const double Times[]={0,.16,.22,.40};
    const FVector Wrists[]={FVector(-42,12,112),FVector(-42,0,151),FVector(-5,32,127),FVector(-42,12,112)};
    const FVector Blades[]={FVector(-.25,.65,.72),FVector(-.65,-.1,.75),FVector(.75,.55,-.35),FVector(-.25,.65,.72)};
    TArray<TArray<FTransform>> Keys;
    for(int32 K=0;K<4;++K)
    {
        auto Local=Base;TArray<FTransform> CS;CS.SetNum(Local.Num());
        auto Recompute=[&](){for(int32 I=0;I<Local.Num();++I){int32 P=Ref.GetParentIndex(I);CS[I]=P<0?Local[I]:Local[I]*CS[P];}};
        Recompute();
        const FVector Shoulder=CS[Upper].GetLocation(),Goal=Wrists[K],Pole(-65,-15,135);
        const double A=FVector::Distance(CS[Upper].GetLocation(),CS[Lower].GetLocation()),B=FVector::Distance(CS[Lower].GetLocation(),CS[Hand].GetLocation());
        const double D=FVector::Distance(Shoulder,Goal);
        if(D>=A+B-.01||D<=FMath::Abs(A-B)+.01)return FString::Printf(TEXT("ERROR: wrist key%d unreachable distance%.3f lengths%.3f/%.3f"),K,D,A,B);
        const FVector Axis=(Goal-Shoulder)/D;
        const FVector Perp=((Pole-Shoulder)-Axis*FVector::DotProduct(Pole-Shoulder,Axis)).GetSafeNormal();
        const double Along=(A*A-B*B+D*D)/(2*D);
        const FVector Elbow=Shoulder+Axis*Along+Perp*FMath::Sqrt(FMath::Max(0.,A*A-Along*Along));
        auto Aim=[&](int32 Bone,int32 Child,FVector Target)
        {
            FQuat Q=FQuat::FindBetweenNormals((CS[Child].GetLocation()-CS[Bone].GetLocation()).GetSafeNormal(),(Target-CS[Bone].GetLocation()).GetSafeNormal())*CS[Bone].GetRotation();
            Local[Bone].SetRotation((CS[Ref.GetParentIndex(Bone)].GetRotation().Inverse()*Q).GetNormalized());Recompute();
        };
        Aim(Upper,Lower,Elbow);Aim(Lower,Hand,Goal);
        // Use the actual accepted socket rotation: blade local +X transformed through it.
        auto* Socket=Skeleton->FindSocket(TEXT("U01_Sword_R"));if(!Socket)return TEXT("ERROR: socket missing");
        const FQuat BladeFrame=FRotationMatrix::MakeFromXZ(Blades[K],FVector(0,0,1)).ToQuat();
        const FQuat HandCS=BladeFrame*Socket->RelativeRotation.Quaternion().Inverse();
        Local[Hand].SetRotation((CS[Lower].GetRotation().Inverse()*HandCS).GetNormalized());Recompute();
        Keys.Add(Local);
    }
    auto* Sequence=NewObject<UAnimSequence>(CreatePackage(*(CRoot+TEXT("/A_U02_Attack1"))),TEXT("A_U02_Attack1"),RF_Public|RF_Standalone);
    Sequence->SetSkeleton(Skeleton);Sequence->bEnableRootMotion=false;Sequence->bForceRootLock=true;
    auto& Controller=Sequence->GetController();Controller.InitializeModel();Controller.OpenBracket(FText::FromString(TEXT("U02 authored blockout")),false);
    Controller.SetFrameRate(FFrameRate(100,1),false);Controller.SetNumberOfFrames(FFrameNumber(40),false);
    for(int32 Bone=0;Bone<Ref.GetNum();++Bone)
    {
        TArray<FVector3f> P,S;TArray<FQuat4f> R;
        for(int32 Frame=0;Frame<=40;++Frame)
        {
            const double T=Frame/100.;int32 K=T<.16?0:T<.22?1:2;
            const double Alpha=FMath::Clamp((T-Times[K])/(Times[K+1]-Times[K]),0.,1.);
            FTransform Transform;Transform.Blend(Keys[K][Bone],Keys[K+1][Bone],Alpha);
            if(Bone==0)Transform=Ref.GetRefBonePose()[0];
            P.Add(FVector3f(Transform.GetTranslation()));R.Add(FQuat4f(Transform.GetRotation()));S.Add(FVector3f(Transform.GetScale3D()));
        }
        if(!Controller.AddBoneCurve(Ref.GetBoneName(Bone),false)||!Controller.SetBoneTrackKeys(Ref.GetBoneName(Bone),P,R,S,false))return TEXT("ERROR: writing authored bone keys");
    }
    Controller.NotifyPopulated();Controller.CloseBracket(false);Sequence->PostEditChange();
    auto* Montage=NewObject<UAnimMontage>(CreatePackage(*(CRoot+TEXT("/AM_U02_Attack1"))),TEXT("AM_U02_Attack1"),RF_Public|RF_Standalone);
    Montage->SetSkeleton(Skeleton);Montage->SlotAnimTracks.SetNum(1);Montage->SlotAnimTracks[0].SlotName=TEXT("DefaultSlot");
    FAnimSegment Segment;Segment.SetAnimReference(Sequence);Segment.AnimStartTime=0;Segment.AnimEndTime=.4f;Segment.AnimPlayRate=1;Segment.LoopingCount=1;
    Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.Add(Segment);Montage->SetCompositeLength(.4f);
    Montage->AddAnimCompositeSection(TEXT("Startup"),0);Montage->AddAnimCompositeSection(TEXT("Active"),.16f);Montage->AddAnimCompositeSection(TEXT("Recovery"),.22f);
    Montage->BlendIn.SetBlendTime(.02f);Montage->BlendOut.SetBlendTime(.04f);Montage->BlendOutTriggerTime=0;
    Montage->PostEditChange();
    // Insert slot BEFORE finger grip but AFTER carry: attack wins the shoulder, fingers remain gripped.
    UAnimGraphNode_LayeredBoneBlend* GripNode=nullptr;UEdGraph* Graph=nullptr;
    for(auto G:BP->FunctionGraphs)for(auto N:G->Nodes)if(auto* L=Cast<UAnimGraphNode_LayeredBoneBlend>(N))
        if(L->Node.LayerSetup.Num()&&L->Node.LayerSetup[0].BranchFilters.Num()&&L->Node.LayerSetup[0].BranchFilters[0].BoneName==TEXT("thumb_01_r")){GripNode=L;Graph=G;}
    if(!GripNode||!Graph)return TEXT("ERROR: finger grip graph missing");
    auto* Input=GripNode->FindPin(TEXT("BasePose"));if(!Input||Input->LinkedTo.Num()!=1)return TEXT("ERROR: expected accepted carry link");
    auto* Previous=Input->LinkedTo[0];Input->BreakAllPinLinks();
    auto* Slot=NewObject<UAnimGraphNode_Slot>(Graph);Graph->AddNode(Slot,false,false);Slot->CreateNewGuid();Slot->Node.SlotName=TEXT("DefaultSlot");Slot->PostPlacedNewNode();Slot->AllocateDefaultPins();
    auto* Arm=NewObject<UAnimGraphNode_LayeredBoneBlend>(Graph);Graph->AddNode(Arm,false,false);Arm->CreateNewGuid();
    Arm->Node.LayerSetup.SetNum(1);Arm->Node.BlendWeights.SetNum(1);Arm->Node.BlendWeights[0]=1;
    FBranchFilter ArmFilter;ArmFilter.BoneName=TEXT("upperarm_r");ArmFilter.BlendDepth=0;Arm->Node.LayerSetup[0].BranchFilters.Add(ArmFilter);
    Arm->Node.bMeshSpaceRotationBlend=true;Arm->PostPlacedNewNode();Arm->AllocateDefaultPins();
    auto* Alpha=NewObject<UK2Node_VariableGet>(Graph);Graph->AddNode(Alpha,false,false);Alpha->CreateNewGuid();Alpha->VariableReference.SetSelfMember(TEXT("AttackBlendWeight"));Alpha->PostPlacedNewNode();Alpha->AllocateDefaultPins();
    if(!Graph->GetSchema()->TryCreateConnection(Alpha->FindPin(TEXT("AttackBlendWeight")),Arm->FindPin(TEXT("BlendWeights_0"))))return TEXT("ERROR: attack weight pin");
    if(!Graph->GetSchema()->TryCreateConnection(Previous,Slot->FindPin(TEXT("Source")))
        ||!Graph->GetSchema()->TryCreateConnection(Previous,Arm->FindPin(TEXT("BasePose")))
        ||!Graph->GetSchema()->TryCreateConnection(Slot->FindPin(TEXT("Pose")),Arm->FindPin(TEXT("BlendPoses_0")))
        ||!Graph->GetSchema()->TryCreateConnection(Arm->FindPin(TEXT("Pose")),Input))return TEXT("ERROR: slot/arm graph connection");
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
    if(BP->Status==BS_Error)return TEXT("ERROR: AnimBP compile");
    CastChecked<UU01AnimInstance>(BP->GeneratedClass->GetDefaultObject())->AttackMontage=Montage;
    FAssetRegistryModule::AssetCreated(Sequence);FAssetRegistryModule::AssetCreated(Montage);
    if(!SaveC(Sequence)||!SaveC(Montage)||!SaveC(BP))return TEXT("ERROR: save C assets");
    return TEXT("SUCCESS: authored 41 samples at100Hz, 0.40s, Startup/Active/Recovery, slot before grip after carry, root fixed");
#else
    return TEXT("ERROR: editor only");
#endif
}
