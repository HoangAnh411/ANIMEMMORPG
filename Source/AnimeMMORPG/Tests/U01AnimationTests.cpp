#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "U01/U01Character.h"
#include "U01/U01AnimInstance.h"
#include "Tests/AutomationCommon.h"
#include "AIController.h"
#include "Components/BoxComponent.h"
#include "Camera/CameraTypes.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace1D.h"
#include "Animation/Skeleton.h"
#include "Animation/AnimClassInterface.h"
#include "Animation/PoseAsset.h"
#include "AnimNodes/AnimNode_BlendListByInt.h"
#include "AnimNodes/AnimNode_LayeredBoneBlend.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UnrealType.h"

namespace
{
constexpr auto DFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
template<class T> T* AnimNode(UAnimInstance* Anim)
{
    auto* Interface=IAnimClassInterface::GetFromClass(Anim->GetClass());
    for(auto* Property:Interface->GetAnimNodeProperties())
        if(Property->Struct==T::StaticStruct())return Property->ContainerPtrToValuePtr<T>(Anim);
    return nullptr;
}
FAnimNode_LayeredBoneBlend* ArmLayer(UAnimInstance* Anim,bool Carry)
{
    auto* Interface=IAnimClassInterface::GetFromClass(Anim->GetClass());
    for(auto* Property:Interface->GetAnimNodeProperties())if(Property->Struct==FAnimNode_LayeredBoneBlend::StaticStruct())
    {
        auto* Node=Property->ContainerPtrToValuePtr<FAnimNode_LayeredBoneBlend>(Anim);
        if(Node->LayerSetup.Num()&&Node->LayerSetup[0].BranchFilters.Num())
        {
            const bool IsCarry=Node->LayerSetup[0].BranchFilters[0].BoneName==TEXT("clavicle_r");
            const bool IsGrip=Node->LayerSetup[0].BranchFilters[0].BoneName==TEXT("thumb_01_r");
            if((Carry&&IsCarry)||(!Carry&&IsGrip))return Node;
        }
    }
    return nullptr;
}
float ActiveBlendWeight(UAnimInstance* Anim)
{
    auto* Node=AnimNode<FAnimNode_BlendListByInt>(Anim);if(!Node)return -1;
    FNodeDebugData Debug(Anim);Node->GatherDebugData(Debug);
    for(auto& Item:Debug.GetFlattenedDebugData())
    {
        FString Tail;
        if(Item.DebugLine.Split(TEXT(" Weight: "),nullptr,&Tail))return FCString::Atof(*Tail)/100;
    }
    return -1;
}
class FAnimatedFixture : public FTestWorldWrapper
{
public:
    explicit FAnimatedFixture(FAutomationTestBase& InTest):Test(InTest) {}
    ~FAnimatedFixture(){ ForwardErrorMessages(&Test); }
    bool Start(bool bShortFloor=false)
    {
        if(!CreateTestWorld(EWorldType::Game)) return false;
        auto* World=GetTestWorld();
        World->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
        auto* Floor=World->SpawnActor<AActor>();
        auto* Box=NewObject<UBoxComponent>(Floor); Floor->SetRootComponent(Box);
        Box->SetBoxExtent(bShortFloor?FVector(150,1000,50):FVector(30000,1000,50));
        Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Box->SetCollisionObjectType(ECC_WorldStatic); Box->SetCollisionResponseToAllChannels(ECR_Block);
        Floor->SetActorLocation(FVector(0,0,-50)); Box->RegisterComponent();
        if(bShortFloor)
        {
            auto* Landing=World->SpawnActor<AActor>();auto* Shape=NewObject<UBoxComponent>(Landing);Landing->SetRootComponent(Shape);
            Shape->SetBoxExtent(FVector(1500,1000,50));Shape->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
            Shape->SetCollisionObjectType(ECC_WorldStatic);Shape->SetCollisionResponseToAllChannels(ECR_Block);
            Landing->SetActorLocation(FVector(1500,0,-350));Shape->RegisterComponent();
        }
        auto* Class=LoadClass<AU01Character>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Character.BP_U01Character_C"));
        if(!Class){Test.AddError(TEXT("D BP missing"));return false;}
        Pawn=World->SpawnActor<AU01Character>(Class,FVector(0,0,110),FRotator::ZeroRotator);
        Pawn->AutoPossessAI=EAutoPossessAI::Disabled;
        World->SpawnActor<AAIController>()->Possess(Pawn);
        Pawn->GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
        Pawn->GetMesh()->bEnableUpdateRateOptimizations=false;
        if(!BeginPlayInTestWorld()) return false;
        Tick(1.25);
        Anim=Cast<UU01AnimInstance>(Pawn->GetMesh()->GetAnimInstance());
        return Test.TestNotNull(TEXT("Actual D AnimBP instance"),Anim);
    }
    void Step(float Dt=1.f/60,FVector Input=FVector::ZeroVector,bool Sprint=false)
    {
        Pawn->GetU01Movement()->SetSprintRequested(Sprint); Pawn->AddMovementInput(Input);
        TickTestWorld(Dt);
    }
    void Tick(float Seconds,FVector Input=FVector::ZeroVector,bool Sprint=false,float Dt=1.f/60)
    {for(int I=0;I<FMath::RoundToInt(Seconds/Dt);++I) Step(Dt,Input,Sprint);}
    void Record(const FString& Case,const FString& Values)
    {
        FString SHA; FParse::Value(FCommandLine::Get(),TEXT("U01SourceSHA="),SHA);
        const auto* World=GetTestWorld(); const auto* Context=GEngine->GetWorldContextFromWorld(World);
        Test.AddInfo(FString::Printf(TEXT("U01D_MEASURE sourceSHA=%s pid=%u utc=%s world=%s context=%s worldType=%d netMode=%d pawn=%s controller=%s owner=%s role=%d remoteRole=%d local=%d mesh=%s anim=%s method=GameWorldControlledInput case=%s %s"),
            *SHA,FPlatformProcess::GetCurrentProcessId(),*FDateTime::UtcNow().ToIso8601(),*World->GetPathName(),Context?*Context->ContextHandle.ToString():TEXT("none"),int(World->WorldType),int(World->GetNetMode()),*Pawn->GetPathName(),*GetPathNameSafe(Pawn->GetController()),*GetPathNameSafe(Pawn->GetOwner()),int(Pawn->GetLocalRole()),int(Pawn->GetRemoteRole()),Pawn->IsLocallyControlled(),*GetPathNameSafe(Pawn->GetMesh()->GetSkeletalMeshAsset()),*GetPathNameSafe(Anim->GetClass()),*Case,*Values));
    }
    AU01Character* Pawn=nullptr;
    UU01AnimInstance* Anim=nullptr;
private: FAutomationTestBase& Test;
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DAssets,"AnimeMMORPG.U01.D.AssetPolicy",DFlags)
bool FU01DAssets::RunTest(const FString&)
{
    auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/SKM_U01"));
    auto* Skeleton=LoadObject<USkeleton>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/SK_U01"));
    if(!TestNotNull(TEXT("Own mesh"),Mesh)||!TestNotNull(TEXT("Own skeleton"),Skeleton)) return false;
    TestEqual(TEXT("Own skeleton assigned"),Mesh->GetSkeleton(),Skeleton);
    TestNotNull(TEXT("Own right hand socket"),Skeleton->FindSocket(TEXT("U01_Sword_R")));
    auto* Source=LoadObject<USkeleton>(nullptr,TEXT("/Game/Characters/Mannequins/Meshes/SK_Mannequin"));
    TestNull(TEXT("Shared skeleton untouched"),Source->FindSocket(TEXT("U01_Sword_R")));
    for(const TCHAR* Name:{TEXT("Idle"),TEXT("Walk"),TEXT("Jog"),TEXT("Jump"),TEXT("Fall"),TEXT("Land")})
    {
        auto* Clip=LoadObject<UAnimSequence>(nullptr,*(FString(TEXT("/Game/AnimeMMORPG/U01/Animation/A_U01_"))+Name));
        if(!TestNotNull(Name,Clip)) return false;
        TestEqual(TEXT("Compatible own skeleton"),Clip->GetSkeleton(),Skeleton);
        TestTrue(TEXT("Extract root, force lock"),Clip->bEnableRootMotion && Clip->bForceRootLock);
        TestEqual(TEXT("Root locked at first frame"),int(Clip->RootMotionRootLock),int(ERootMotionRootLock::AnimFirstFrame));
    }
    auto* Blend=LoadObject<UBlendSpace1D>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/BS_U01_Locomotion"));
    if(!TestNotNull(TEXT("Own BlendSpace"),Blend)) return false;
    TestEqual(TEXT("Four calibrated samples"),Blend->GetBlendSamples().Num(),4);
    for(const auto& Sample:Blend->GetBlendSamples()) TestTrue(TEXT("Bounded play rates"),Sample.RateScale>=.6 && Sample.RateScale<=2.5);
    TArray<FBlendSampleData> Weights; int32 CachedIndex=INDEX_NONE;
    TestTrue(TEXT("Serialized interpolation produces a pose at 500cm/s"),Blend->GetSamplesFromBlendInput(FVector(500,0,0),Weights,CachedIndex,true));
    TestTrue(TEXT("Nonempty evaluated samples"),Weights.Num()>0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DMovement,"AnimeMMORPG.U01.D.AnimatedMotor",DFlags)
bool FU01DMovement::RunTest(const FString&)
{
    FAnimatedFixture F(*this); if(!F.Start()) return false;
    TestEqual(TEXT("Discard extracted motion"),int(F.Anim->RootMotionMode),int(ERootMotionMode::IgnoreRootMotion));
    F.Tick(1,FVector::ForwardVector);
    double Start=F.Pawn->GetActorLocation().X; F.Tick(10,FVector::ForwardVector);
    double Walk=F.Pawn->GetActorLocation().X-Start;
    TestTrue(TEXT("Animated walk 50m within .5m"),FMath::Abs(Walk-5000)<50);
    F.Tick(1,FVector::ForwardVector,true); Start=F.Pawn->GetActorLocation().X; F.Tick(10,FVector::ForwardVector,true);
    double Sprint=F.Pawn->GetActorLocation().X-Start;
    TestTrue(TEXT("Animated sprint 70m within .5m"),FMath::Abs(Sprint-7000)<50);
    F.Record(TEXT("travel"),FString::Printf(TEXT("walk10sCm=%.9f sprint10sCm=%.9f"),Walk,Sprint));
    F.Tick(2);
    for(float Dt:{1.f/30,1.f/60,1.f/120})
    {
        double Base=F.Pawn->GetActorLocation().Z,Peak=Base;
        F.Pawn->Jump();
        for(int I=0;I<FMath::RoundToInt(1.5/Dt);++I){ F.Step(Dt); Peak=FMath::Max(Peak,F.Pawn->GetActorLocation().Z); }
        F.Pawn->StopJumping(); F.Tick(.5);
        TestTrue(TEXT("Animated apex 120cm within 5cm"),FMath::Abs(Peak-Base-120)<5);
        F.Record(TEXT("apex"),FString::Printf(TEXT("integrationDt=%.9f heightCm=%.9f gravity=%.6f"),Dt,Peak-Base,F.Pawn->GetU01Movement()->GetGravityZ()));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DTransitions,"AnimeMMORPG.U01.D.TransitionsAndAttachment",DFlags)
bool FU01DTransitions::RunTest(const FString&)
{
    FAnimatedFixture F(*this); if(!F.Start()) return false;
    TestEqual(TEXT("Idle"),F.Anim->PoseIndex,0);
    const FVector IdleHand=F.Pawn->GetMesh()->GetSocketTransform(TEXT("hand_r"),RTS_Component).GetLocation();
    F.Tick(.5,FVector::ForwardVector);
    TestEqual(TEXT("Moving"),F.Anim->PoseIndex,1);
    double HandChange=0,SocketError=0,RootDrift=0;
    const FVector Root=F.Pawn->GetMesh()->GetSocketTransform(TEXT("root"),RTS_Component).GetLocation();
    const FVector MovingHand=F.Pawn->GetMesh()->GetSocketTransform(TEXT("hand_r"),RTS_Component).GetLocation();
    const FVector MovingFoot=F.Pawn->GetMesh()->GetSocketTransform(TEXT("foot_r"),RTS_Component).GetLocation();
    double WalkHandCycle=0,WalkFootCycle=0;
    for(int I=0;I<120;++I)
    {
        F.Step(1.f/60,FVector::ForwardVector);
        auto* Mesh=F.Pawn->GetMesh();
        WalkHandCycle=FMath::Max(WalkHandCycle,FVector::Distance(MovingHand,Mesh->GetSocketTransform(TEXT("hand_r"),RTS_Component).GetLocation()));
        WalkFootCycle=FMath::Max(WalkFootCycle,FVector::Distance(MovingFoot,Mesh->GetSocketTransform(TEXT("foot_r"),RTS_Component).GetLocation()));
        HandChange=FMath::Max(HandChange,FVector::Distance(IdleHand,Mesh->GetSocketTransform(TEXT("hand_r"),RTS_Component).GetLocation()));
        RootDrift=FMath::Max(RootDrift,FVector::Distance(Root,Mesh->GetSocketTransform(TEXT("root"),RTS_Component).GetLocation()));
        SocketError=FMath::Max(SocketError,FVector::Distance(F.Pawn->SwordRoot->GetComponentLocation(),Mesh->GetSocketTransform(TEXT("U01_Sword_R"),RTS_World).GetLocation()));
    }
    // Carry deliberately damps the right arm. Foot cycles remain the proof that
    // locomotion is animated; do not demand the old unarmed hand swing.
    TestTrue(TEXT("Steady walk foot cycles, not frozen pose"),WalkFootCycle>10);
    F.Tick(1,FVector::ForwardVector,true);
    const FVector SprintFoot=F.Pawn->GetMesh()->GetSocketTransform(TEXT("foot_r"),RTS_Component).GetLocation();
    double SprintFootCycle=0;
    for(int I=0;I<120;++I)
    {
        F.Step(1.f/60,FVector::ForwardVector,true);
        SprintFootCycle=FMath::Max(SprintFootCycle,FVector::Distance(SprintFoot,F.Pawn->GetMesh()->GetSocketTransform(TEXT("foot_r"),RTS_Component).GetLocation()));
    }
    TestTrue(TEXT("Steady sprint foot cycles"),SprintFootCycle>10);
    TestTrue(TEXT("Root does not drift"),RootDrift<.5);
    TestTrue(TEXT("Sword attached to animated hand"),SocketError<.1);
    F.Tick(1); F.Pawn->Jump();
    TSet<int32> Phases;
    for(int I=0;I<100;++I){F.Step();Phases.Add(F.Anim->PoseIndex);}
    F.Pawn->StopJumping();
    for(int Phase:{0,2,3,4}) TestTrue(FString::Printf(TEXT("Jump cycle observes phase %d"),Phase),Phases.Contains(Phase));
    TestEqual(TEXT("No stuck landing/falling"),F.Anim->PoseIndex,0);
    for(auto* Part:{F.Pawn->SwordBlade.Get(),F.Pawn->SwordGuard.Get(),F.Pawn->SwordGrip.Get()})
    {
        TestNotNull(TEXT("Visible block mesh"),Part->GetStaticMesh().Get());
        TestEqual(TEXT("No collision"),Part->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
        TestFalse(TEXT("No overlap"),Part->GetGenerateOverlapEvents());
        TestFalse(TEXT("No physics"),Part->IsSimulatingPhysics());
        TestFalse(TEXT("No navigation effect"),Part->CanEverAffectNavigation());
    }
    TestEqual(TEXT("Capsule radius unchanged"),F.Pawn->GetCapsuleComponent()->GetUnscaledCapsuleRadius(),42.f);
    TestEqual(TEXT("Capsule height unchanged"),F.Pawn->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(),96.f);
    F.Record(TEXT("pose-attachment"),FString::Printf(TEXT("handChangeCm=%.9f rootDriftCm=%.9f socketErrorCm=%.9f walkHandCycleCm=%.9f walkFootCycleCm=%.9f sprintFootCycleCm=%.9f"),HandChange,RootDrift,SocketError,WalkHandCycle,WalkFootCycle,SprintFootCycle));
    FAnimatedFixture Ledge(*this); if(!Ledge.Start(true)) return false;
    bool SawFall=false,SawJump=false;
    for(int I=0;I<60;++I){Ledge.Step(1.f/60,FVector::ForwardVector);SawFall|=Ledge.Anim->PoseIndex==3;SawJump|=Ledge.Anim->PoseIndex==2;}
    TestTrue(TEXT("Ledge directly falls"),SawFall); TestFalse(TEXT("No false ascent at ledge"),SawJump);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DLanding,"AnimeMMORPG.U01.D.LandingTransitions",DFlags)
bool FU01DLanding::RunTest(const FString&)
{
    auto BlendDeadline=[this](FAnimatedFixture& F,FVector Input,bool Sprint)
    {
        auto* Node=AnimNode<FAnimNode_BlendListByInt>(F.Anim);
        if(!TestNotNull(TEXT("Compiled selector"),Node))return;
        for(float Time:Node->GetBlendTimes())TestTrue(TEXT("Every pose explicitly blends in .100s"),FMath::IsNearlyEqual(Time,.1f,1.e-6f));
        F.Tick(.025f,Input,Sprint,1.f/120);
        const float Early=ActiveBlendWeight(F.Anim);
        TestTrue(TEXT("Transition blends rather than snapping"),Early>=0 && Early<.999f);
        F.Tick(.084f,Input,Sprint,1.f/120);
        TestTrue(TEXT("Target pose full weight by .100s plus sample tolerance"),ActiveBlendWeight(F.Anim)>.999f);
    };
    for(bool Sprint:{false,true})
    {
        FAnimatedFixture F(*this);if(!F.Start())return false;
        F.Tick(1,FVector::ForwardVector,Sprint);F.Pawn->Jump();
        bool Air=false,Land=false;
        for(int I=0;I<160;++I)
        {
            F.Step(1.f/120,FVector::ForwardVector,Sprint);
            Air|=F.Anim->bFalling;
            if(Air && F.Anim->bGrounded){Land=true;TestEqual(TEXT("Moving touchdown goes directly to locomotion"),F.Anim->PoseIndex,1);break;}
        }
        F.Pawn->StopJumping();TestTrue(TEXT("Observed moving touchdown"),Land);
        BlendDeadline(F,FVector::ForwardVector,Sprint);
        TestEqual(TEXT("Still locomotion, no delayed land pose"),F.Anim->PoseIndex,1);
        F.Record(Sprint?TEXT("sprint-jump-land"):TEXT("walk-jump-land"),FString::Printf(TEXT("pose=%d blendWeight=%.6f speed=%.6f"),F.Anim->PoseIndex,ActiveBlendWeight(F.Anim),F.Anim->GroundSpeed));
    }
    auto StationaryLand=[this](FAnimatedFixture& F)
    {
        F.Pawn->Jump();bool Air=false;
        for(int I=0;I<150;++I){F.Step(1.f/120);Air|=F.Anim->bFalling;if(Air&&F.Anim->bGrounded){F.Pawn->StopJumping();return TestEqual(TEXT("Stationary touchdown enters land"),F.Anim->PoseIndex,4);}}
        AddError(TEXT("No stationary touchdown"));return false;
    };
    {
        FAnimatedFixture F(*this);if(!F.Start()||!StationaryLand(F))return false;
        F.Tick(.15f,FVector::ZeroVector,false,1.f/120);TestEqual(TEXT("Stationary land retained before .25s"),F.Anim->PoseIndex,4);
        float Since=.15f;
        while(F.Anim->PoseIndex==4 && Since<.275f){F.Step(1.f/120);Since+=1.f/120;}
        TestTrue(TEXT("Stationary hold expires at most .25s + one sample"),Since<=.25f+1.f/120+.00001);
        TestEqual(TEXT("Stationary hold returns idle"),F.Anim->PoseIndex,0);
        BlendDeadline(F,FVector::ZeroVector,false);
        F.Record(TEXT("stationary-land"),FString::Printf(TEXT("holdSampleSeconds=%.9f idleWeight=%.6f"),Since,ActiveBlendWeight(F.Anim)));
    }
    {
        FAnimatedFixture F(*this);if(!F.Start()||!StationaryLand(F))return false;
        F.Tick(.05f);F.Step(1.f/120,FVector::ForwardVector);
        TestTrue(TEXT("Actual speed exceeds locomotion threshold"),F.Anim->GroundSpeed>3);
        TestEqual(TEXT("Movement cancels stationary hold in same animation update"),F.Anim->PoseIndex,1);
        BlendDeadline(F,FVector::ForwardVector,false);
    }
    {
        FAnimatedFixture F(*this);if(!F.Start())return false;
        F.Pawn->Jump();bool Queued=false,SawAir=false,Rejump=false;
        for(int I=0;I<300;++I)
        {
            F.Step(1.f/120);SawAir|=F.Anim->bFalling;
            const double Feet=F.Pawn->GetU01Movement()->GetActorFeetLocation().Z;
            if(SawAir&&!Queued&&F.Anim->VerticalSpeed < -200 && Feet<22)
            {F.Pawn->StopJumping();F.Pawn->Jump();Queued=true;}
            if(Queued && F.Anim->VerticalSpeed>200)
            {Rejump=true;TestEqual(TEXT("Buffered jump immediately takes airborne priority"),F.Anim->PoseIndex,2);break;}
        }
        TestTrue(TEXT("Buffered at touchdown and jumped again"),Queued&&Rejump);F.Pawn->StopJumping();
    }
    {
        FAnimatedFixture F(*this);if(!F.Start()||!StationaryLand(F))return false;
        F.Pawn->Jump();F.Step(1.f/120);TestEqual(TEXT("New jump interrupts stationary land"),F.Anim->PoseIndex,2);F.Pawn->StopJumping();
    }
    {
        FAnimatedFixture F(*this);if(!F.Start()||!StationaryLand(F))return false;
        F.Pawn->GetU01Movement()->SetMovementMode(MOVE_Falling);F.Pawn->GetU01Movement()->Velocity=FVector(0,0,-100);
        F.Pawn->AddActorWorldOffset(FVector(0,0,200));F.Step(1.f/120);
        TestEqual(TEXT("Falling interrupts stationary land immediately"),F.Anim->PoseIndex,3);
    }
    {
        FAnimatedFixture F(*this);if(!F.Start(true))return false;
        // Run off actual collision geometry to the lower landing surface.
        bool Fall=false,Land=false;
        for(int I=0;I<300;++I){F.Step(1.f/120,FVector::ForwardVector);Fall|=F.Anim->PoseIndex==3;if(Fall&&F.Anim->bGrounded){Land=true;TestEqual(TEXT("Ledge descent resumes run at contact"),F.Anim->PoseIndex,1);break;}}
        TestTrue(TEXT("Descending contact reached"),Land);BlendDeadline(F,FVector::ForwardVector,false);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DGrip,"AnimeMMORPG.U01.D.GripIsolationAndAttachment",DFlags)
bool FU01DGrip::RunTest(const FString&)
{
    FAnimatedFixture F(*this);if(!F.Start())return false;
    auto* Grip=LoadObject<UPoseAsset>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/PA_U01_RightGrip"));
    if(!TestNotNull(TEXT("Own grip pose asset"),Grip))return false;
    TestEqual(TEXT("Named authored grip pose"),Grip->GetPoseIndexByName(TEXT("RightGrip")),0);
    TestEqual(TEXT("One grip pose"),Grip->GetNumPoses(),1);
    auto* Mesh=F.Pawn->GetMesh();auto* Layer=ArmLayer(F.Anim,false);
    if(!TestNotNull(TEXT("Finger-only layer after selector"),Layer))return false;
    for(const FVector Input:{FVector::ZeroVector,FVector::ForwardVector})
    {
        F.Tick(.5,Input);const auto With=Mesh->GetBoneSpaceTransforms();
        Layer->BlendWeights[0]=0;Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();const auto Without=Mesh->GetBoneSpaceTransforms();
        const auto& Ref=Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();int Changed=0;
        for(int I=0;I<With.Num();++I)
        {
            const FString N=Ref.GetBoneName(I).ToString();const bool Finger=N.EndsWith(TEXT("_r"))&&(N.StartsWith(TEXT("thumb_0"))||N.StartsWith(TEXT("index_0"))||N.StartsWith(TEXT("middle_0"))||N.StartsWith(TEXT("ring_0"))||N.StartsWith(TEXT("pinky_0")));
            if(Finger)Changed+=With[I].GetRotation().AngularDistance(Without[I].GetRotation())>.05;
            else TestTrue(TEXT("Grip preserves all non-finger local transforms including wrist/arm"),With[I].Equals(Without[I],.001));
        }
        TestTrue(TEXT("Grip actually changes finger joints"),Changed>=10);
        Layer->BlendWeights[0]=1;Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();
    }
    double MaxAngle=0,MaxDistance=0;
    F.Pawn->Jump();
    for(int I=0;I<150;++I)
    {
        F.Step(1.f/120,FVector::ForwardVector,true);
        const FTransform Socket=Mesh->GetSocketTransform(TEXT("U01_Sword_R"),RTS_World),Sword=F.Pawn->SwordRoot->GetComponentTransform();
        MaxDistance=FMath::Max(MaxDistance,FVector::Distance(Socket.GetLocation(),Sword.GetLocation()));
        MaxAngle=FMath::Max(MaxAngle,double(FMath::RadiansToDegrees(Socket.GetRotation().AngularDistance(Sword.GetRotation()))));
    }
    F.Pawn->StopJumping();TestTrue(TEXT("Attachment position"),MaxDistance<.1);TestTrue(TEXT("Attachment orientation"),MaxAngle<.01);
    F.Record(TEXT("grip-attachment"),FString::Printf(TEXT("maxPositionErrorCm=%.9f maxAngleErrorDegrees=%.9f"),MaxDistance,MaxAngle));
    F.Pawn->SetActorLocation(FVector(0,0,300));F.Pawn->GetU01Movement()->StopMovementImmediately();
    auto* PC=F.Pawn->GetController();PC->SetControlRotation(FRotator::ZeroRotator);
    // Place a wall 50cm behind the pivot, then remove it to exercise B's recursive owner-hide.
    auto* Wall=F.GetTestWorld()->SpawnActor<AActor>();auto* Box=NewObject<UBoxComponent>(Wall);Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(10,200,200));Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);Box->SetCollisionObjectType(ECC_WorldStatic);Box->SetCollisionResponseToAllChannels(ECR_Block);Wall->SetActorLocation(FVector(-55,0,370));Box->RegisterComponent();
    FMinimalViewInfo View;F.Pawn->CalcCamera(.016,View);
    TestTrue(TEXT("Close camera hides mesh"),Mesh->bOwnerNoSee);
    for(auto* Part:{F.Pawn->SwordGrip.Get(),F.Pawn->SwordGuard.Get(),F.Pawn->SwordBlade.Get()})TestTrue(TEXT("Close camera hides sword"),Part->bOwnerNoSee);
    Wall->Destroy();for(int I=0;I<120;++I)F.Pawn->CalcCamera(.016,View);
    TestFalse(TEXT("Clear camera restores mesh"),Mesh->bOwnerNoSee);
    for(auto* Part:{F.Pawn->SwordGrip.Get(),F.Pawn->SwordGuard.Get(),F.Pawn->SwordBlade.Get()})TestFalse(TEXT("Clear camera restores sword"),Part->bOwnerNoSee);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DCarry,"AnimeMMORPG.U01.D.CarryTrajectory",DFlags)
bool FU01DCarry::RunTest(const FString&)
{
    FAnimatedFixture F(*this);if(!F.Start())return false;
    auto* Mesh=F.Pawn->GetMesh();auto* Layer=ArmLayer(F.Anim,true);
    if(!TestNotNull(TEXT("Carry layer before accepted grip"),Layer))return false;
    auto* Pose=LoadObject<UPoseAsset>(nullptr,TEXT("/Game/AnimeMMORPG/U01/Animation/PA_U01_RightCarry"));
    if(!TestNotNull(TEXT("Own right carry pose"),Pose))return false;
    TestEqual(TEXT("Single carry pose"),Pose->GetNumPoses(),1);
    const auto& Ref=Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
    // A/B evaluate at the same player time: outside the right shoulder branch,
    // including every leg/root/spine/left-arm bone, the carry layer is identity.
    F.Tick(.5,FVector::ForwardVector,true);
    const auto With=Mesh->GetBoneSpaceTransforms();Layer->BlendWeights[0]=0;Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();const auto Without=Mesh->GetBoneSpaceTransforms();
    const int Clavicle=Ref.FindBoneIndex(TEXT("clavicle_r"));int ArmChanges=0;
    for(int I=0;I<With.Num();++I)
    {
        int Parent=I;while(Parent>=0&&Parent!=Clavicle)Parent=Ref.GetParentIndex(Parent);
        if(Parent<0)TestTrue(TEXT("Carry preserves legs/motor root/spine/left arm"),With[I].Equals(Without[I],.001));
        else if(Ref.GetBoneName(I)==TEXT("upperarm_r")||Ref.GetBoneName(I)==TEXT("lowerarm_r")||Ref.GetBoneName(I)==TEXT("hand_r"))
            ArmChanges+=With[I].GetRotation().AngularDistance(Without[I].GetRotation())>.05;
    }
    TestTrue(TEXT("Carry changes actual upper/lower/wrist pose"),ArmChanges>=2);
    Layer->BlendWeights[0]=1;Mesh->TickAnimation(0,false);Mesh->RefreshBoneTransforms();
    double MinClearance=1.e9,MaxAngle=0,MaxGripError=0,MaxBladeStep=0;FVector PreviousTip=FVector::ZeroVector;bool HaveTip=false;
    TSet<int> Phases;int Samples=0;
    // Conservative bone-following body capsules, fixture only: not sword collision
    // and not a proof of triangle-perfect nonintersection from every camera angle.
    struct FBody{const TCHAR* A;const TCHAR* B;double Radius;};
    const FBody Bodies[]={{TEXT("pelvis"),TEXT("spine_02"),17},{TEXT("spine_02"),TEXT("neck_01"),19},{TEXT("neck_01"),TEXT("head"),12},{TEXT("thigh_r"),TEXT("calf_r"),10},{TEXT("thigh_l"),TEXT("calf_l"),10}};
    auto Sample=[&]()
    {
        const auto Sword=F.Pawn->SwordBlade->GetComponentTransform();
        const FVector A=Sword.TransformPosition(FVector(-50,0,0)),B=Sword.TransformPosition(FVector(50,0,0));
        for(const auto& Body:Bodies)
        {
            FVector OnSword,OnBody;
            FMath::SegmentDistToSegmentSafe(A,B,Mesh->GetSocketLocation(Body.A),Mesh->GetSocketLocation(Body.B),OnSword,OnBody);
            MinClearance=FMath::Min(MinClearance,FVector::Distance(OnSword,OnBody)-Body.Radius-3.25);
        }
        const FTransform Socket=Mesh->GetSocketTransform(TEXT("U01_Sword_R"),RTS_World);
        MaxAngle=FMath::Max(MaxAngle,double(FMath::RadiansToDegrees(Socket.GetRotation().AngularDistance(F.Pawn->SwordRoot->GetComponentQuat()))));
        MaxGripError=FMath::Max(MaxGripError,FVector::Distance(Socket.GetLocation(),F.Pawn->SwordRoot->GetComponentLocation()));
        const FVector TipCS=Mesh->GetComponentTransform().InverseTransformPosition(B);
        if(HaveTip)MaxBladeStep=FMath::Max(MaxBladeStep,FVector::Distance(TipCS,PreviousTip));
        PreviousTip=TipCS;HaveTip=true;Phases.Add(F.Anim->PoseIndex);++Samples;
    };
    auto Run=[&](int Frames,FVector Direction,bool Sprint){for(int I=0;I<Frames;++I){F.Step(1.f/120,Direction,Sprint);Sample();}};
    Run(120,FVector::ZeroVector,false);Run(180,FVector::ForwardVector,false);Run(180,FVector::ForwardVector,true);
    F.Pawn->Jump();Run(150,FVector::ForwardVector,true);F.Pawn->StopJumping();
    Run(120,FVector::RightVector,true);Run(120,-FVector::ForwardVector,true);Run(120,-FVector::RightVector,true);
    Run(120,FVector::ZeroVector,false);F.Pawn->Jump();Run(160,FVector::ZeroVector,false);F.Pawn->StopJumping();
    for(int Phase:{0,1,2,3,4})TestTrue(FString::Printf(TEXT("Trajectory includes pose %d"),Phase),Phases.Contains(Phase));
    TestTrue(TEXT("Blade clears body proxy through locomotion/jump/land/turn transitions"),MinClearance>0);
    TestTrue(TEXT("No abrupt component-space blade jump at 120Hz fixture"),MaxBladeStep<8);
    TestTrue(TEXT("Grip attachment position unchanged"),MaxGripError<.1);TestTrue(TEXT("Grip attachment orientation unchanged"),MaxAngle<.01);
    for(auto* Part:{F.Pawn->SwordBlade.Get(),F.Pawn->SwordGuard.Get(),F.Pawn->SwordGrip.Get()})TestEqual(TEXT("Sword collision remains off"),Part->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
    F.Record(TEXT("carry-trajectory"),FString::Printf(TEXT("samples=%d minBodyProxyClearanceCm=%.6f maxTipStepComponentCm=%.6f socketPositionErrorCm=%.6f socketAngleErrorDegrees=%.6f"),Samples,MinClearance,MaxBladeStep,MaxGripError,MaxAngle));
    return true;
}
#endif
