#include "U03AnimationEditor.h"
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
const FString U03Root=TEXT("/Game/AnimeMMORPG/U03/Animation");
bool U03Save(UObject* Obj)
{
    Obj->MarkPackageDirty();FSavePackageArgs A;A.TopLevelFlags=RF_Public|RF_Standalone;
    return UPackage::SavePackage(Obj->GetOutermost(),Obj,*FPackageName::LongPackageNameToFilename(Obj->GetOutermost()->GetName(),FPackageName::GetAssetPackageExtension()),A);
}
TArray<FTransform> U03PoseLocal(UPoseAsset* Asset)
{
    auto* Container=FindFProperty<FStructProperty>(UPoseAsset::StaticClass(),TEXT("PoseContainer"))->ContainerPtrToValuePtr<FPoseDataContainer>(Asset);
    auto* Array=FindFProperty<FArrayProperty>(FPoseDataContainer::StaticStruct(),TEXT("Poses"));
    FScriptArrayHelper H(Array,Array->ContainerPtrToValuePtr<void>(Container));check(H.Num()==1);
    return *FindFProperty<FArrayProperty>(FPoseData::StaticStruct(),TEXT("SourceLocalSpacePose"))->ContainerPtrToValuePtr<TArray<FTransform>>(H.GetRawPtr(0));
}
}
#endif

FString UU03AnimationEditor::BuildA1Assets()
{
#if WITH_EDITOR
    FString Dir=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());Dir.ReplaceInline(TEXT("\\"),TEXT("/"));
    if(!Dir.Contains(TEXT("/Artifacts/U03/A1/Source/")))return TEXT("ERROR: isolated A1 clone only");
    if(FPackageName::DoesPackageExist(U03Root+TEXT("/ABP_U03")))return TEXT("ERROR: refuses overwrite of A1 assets");
    auto* Original=LoadObject<UAnimBlueprint>(nullptr,TEXT("/Game/AnimeMMORPG/U02/Animation/ABP_U02"));
    if(!Original)return TEXT("ERROR: accepted U02 graph missing");
    auto* BP=CastChecked<UAnimBlueprint>(FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().DuplicateAsset(TEXT("ABP_U03"),U03Root,Original));
    for(int32 Number=2;Number<=3;++Number)
    {
    auto* Skeleton=LoadObject<USkeleton>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/SK_U01"));
    auto* Carry=LoadObject<UPoseAsset>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/PA_U01_RightCarry"));
    auto* Grip=LoadObject<UPoseAsset>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/PA_U01_RightGrip"));
    auto* OriginalBP=LoadObject<UAnimBlueprint>(nullptr,TEXT("/Game/AnimeMMORPG/U02/Animation/ABP_U02"));
    if(!Skeleton||!Carry||!Grip||!OriginalBP)return TEXT("ERROR: accepted U01 assets missing");

    const auto& Ref=Skeleton->GetReferenceSkeleton();
    TArray<FTransform> Base=U03PoseLocal(Carry),Fingers=U03PoseLocal(Grip);
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
    const double ActiveStart=Number==2?.18:.26, ActiveEnd=Number==2?.25:.36, Duration=Number==2?.45:.60;
    const int32 Frames=Number==2?45:60;
    const double Times[]={0,ActiveStart,ActiveEnd,Duration};
    const FVector Wrists[]={FVector(-42,12,112),Number==2?FVector(-5,32,127):FVector(-42,0,151),Number==2?FVector(-42,0,151):FVector(-42,12,112),FVector(-42,12,112)};
    const FVector Blades[]={FVector(-.25,.65,.72),Number==2?FVector(.75,.55,-.35):FVector(0,.15,.99),Number==2?FVector(-.65,-.1,.75):FVector(0,.5,-.86),FVector(-.25,.65,.72)};
    TArray<TArray<FTransform>> Keys;
    for(int32 K=0;K<4;++K)
    {
        auto Local=Base;
        // Small preparation/counter-rotation, authored only for attack 1. Root stays fixed.
        const double Twist[]={0.,Number==2?12.:-6.,Number==2?-12.:2.,0.};
        const double Crouch[]={0.,7.,4.,0.};
        auto RotateLocal=[&](const TCHAR* Name,FRotator Rotation)
        {
            const int32 I=Ref.FindBoneIndex(Name);
            if(I!=INDEX_NONE)Local[I].SetRotation((Local[I].GetRotation()*Rotation.Quaternion()).GetNormalized());
        };
        RotateLocal(TEXT("spine_01"),FRotator(0,Twist[K]*.35,0));
        RotateLocal(TEXT("spine_02"),FRotator(0,Twist[K]*.35,0));
        RotateLocal(TEXT("spine_03"),FRotator(0,Twist[K]*.30,0));
        RotateLocal(TEXT("clavicle_l"),FRotator(0,-Twist[K]*.25,0));
        RotateLocal(TEXT("thigh_l"),FRotator(Crouch[K],0,-Crouch[K]*.3));
        RotateLocal(TEXT("thigh_r"),FRotator(-Crouch[K],0,Crouch[K]*.3));
        RotateLocal(TEXT("calf_l"),FRotator(-Crouch[K]*.5,0,0));
        RotateLocal(TEXT("calf_r"),FRotator(Crouch[K]*.5,0,0));
        TArray<FTransform> CS;CS.SetNum(Local.Num());
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
    auto* Sequence=NewObject<UAnimSequence>(CreatePackage(*(U03Root+FString::Printf(TEXT("/A_U03_Attack%d"),Number))),*FString::Printf(TEXT("A_U03_Attack%d"),Number),RF_Public|RF_Standalone);
    Sequence->SetSkeleton(Skeleton);Sequence->bEnableRootMotion=false;Sequence->bForceRootLock=true;
    auto& Controller=Sequence->GetController();Controller.InitializeModel();Controller.OpenBracket(FText::FromString(TEXT("U03 A1 authored blockout")),false);
    Controller.SetFrameRate(FFrameRate(100,1),false);Controller.SetNumberOfFrames(FFrameNumber(Frames),false);
    for(int32 Bone=0;Bone<Ref.GetNum();++Bone)
    {
        TArray<FVector3f> P,S;TArray<FQuat4f> R;
        for(int32 Frame=0;Frame<=Frames;++Frame)
        {
            const double T=Frame/100.;int32 K=T<ActiveStart?0:T<ActiveEnd?1:2;
            const double Alpha=FMath::Clamp((T-Times[K])/(Times[K+1]-Times[K]),0.,1.);
            FTransform Transform;Transform.Blend(Keys[K][Bone],Keys[K+1][Bone],Alpha);
            if(Bone==0)Transform=Ref.GetRefBonePose()[0];
            P.Add(FVector3f(Transform.GetTranslation()));R.Add(FQuat4f(Transform.GetRotation()));S.Add(FVector3f(Transform.GetScale3D()));
        }
        if(!Controller.AddBoneCurve(Ref.GetBoneName(Bone),false)||!Controller.SetBoneTrackKeys(Ref.GetBoneName(Bone),P,R,S,false))return TEXT("ERROR: writing authored bone keys");
    }
    Controller.NotifyPopulated();Controller.CloseBracket(false);Sequence->PostEditChange();
    auto* Montage=NewObject<UAnimMontage>(CreatePackage(*(U03Root+FString::Printf(TEXT("/AM_U03_Attack%d"),Number))),*FString::Printf(TEXT("AM_U03_Attack%d"),Number),RF_Public|RF_Standalone);
    Montage->SetSkeleton(Skeleton);Montage->SlotAnimTracks.SetNum(1);Montage->SlotAnimTracks[0].SlotName=TEXT("DefaultSlot");
    FAnimSegment Segment;Segment.SetAnimReference(Sequence);Segment.AnimStartTime=0;Segment.AnimEndTime=float(Duration);Segment.AnimPlayRate=1;Segment.LoopingCount=1;
    Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.Add(Segment);Montage->SetCompositeLength(float(Duration));
    Montage->AddAnimCompositeSection(TEXT("Startup"),0);Montage->AddAnimCompositeSection(TEXT("Active"),float(ActiveStart));Montage->AddAnimCompositeSection(TEXT("Recovery"),float(ActiveEnd));
    Montage->BlendIn.SetBlendTime(.02f);Montage->BlendOut.SetBlendTime(.04f);Montage->BlendOutTriggerTime=0;
    Montage->PostEditChange();

        FAssetRegistryModule::AssetCreated(Sequence);FAssetRegistryModule::AssetCreated(Montage);
        if(!U03Save(Sequence)||!U03Save(Montage))return TEXT("ERROR: save A1 animation");
        auto* Defaults=CastChecked<UU01AnimInstance>(BP->GeneratedClass->GetDefaultObject());
        if(Number==2)Defaults->Attack2Montage=Montage;else Defaults->Attack3Montage=Montage;
    }
    if(!U03Save(BP))return TEXT("ERROR: save A1 graph");
    return TEXT("SUCCESS: A1 Attack2 diagonal reverse .45s, Attack3 overhead .60s; shared accepted Attack1 .40s; fixed roots, no gameplay notifies");
#else
    return TEXT("ERROR: editor only");
#endif
}
