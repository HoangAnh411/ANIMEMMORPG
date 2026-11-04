#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "U01/U01Character.h"
#include "U01/U01AnimInstance.h"
#include "Tests/AutomationCommon.h"
#include "AIController.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace1D.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
constexpr auto DFlags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
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
    TestEqual(TEXT("Four calibrated samples"),Blend->GetNumberOfBlendSamples(),4);
    for(const auto& Sample:Blend->GetBlendSamples()) TestTrue(TEXT("Bounded play rates"),Sample.RateScale>=.6 && Sample.RateScale<=2.5);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU01DMovement,"AnimeMMORPG.U01.D.AnimatedMotor",DFlags)
bool FU01DMovement::RunTest(const FString&)
{
    FAnimatedFixture F(*this); if(!F.Start()) return false;
    TestEqual(TEXT("Discard extracted motion"),int(F.Anim->GetRootMotionMode()),int(ERootMotionMode::IgnoreRootMotion));
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
    for(int I=0;I<120;++I)
    {
        F.Step(1.f/60,FVector::ForwardVector);
        auto* Mesh=F.Pawn->GetMesh();
        HandChange=FMath::Max(HandChange,FVector::Distance(IdleHand,Mesh->GetSocketTransform(TEXT("hand_r"),RTS_Component).GetLocation()));
        RootDrift=FMath::Max(RootDrift,FVector::Distance(Root,Mesh->GetSocketTransform(TEXT("root"),RTS_Component).GetLocation()));
        SocketError=FMath::Max(SocketError,FVector::Distance(F.Pawn->SwordRoot->GetComponentLocation(),Mesh->GetSocketTransform(TEXT("U01_Sword_R"),RTS_World).GetLocation()));
    }
    TestTrue(TEXT("Evaluated moving bone pose, not reference pose"),HandChange>5);
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
        TestNotNull(TEXT("Visible block mesh"),Part->GetStaticMesh());
        TestEqual(TEXT("No collision"),Part->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
        TestFalse(TEXT("No overlap"),Part->GetGenerateOverlapEvents());
        TestFalse(TEXT("No physics"),Part->IsSimulatingPhysics());
        TestFalse(TEXT("No navigation effect"),Part->CanEverAffectNavigation());
    }
    TestEqual(TEXT("Capsule radius unchanged"),F.Pawn->GetCapsuleComponent()->GetUnscaledCapsuleRadius(),42.f);
    TestEqual(TEXT("Capsule height unchanged"),F.Pawn->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(),96.f);
    F.Record(TEXT("pose-attachment"),FString::Printf(TEXT("handChangeCm=%.9f rootDriftCm=%.9f socketErrorCm=%.9f"),HandChange,RootDrift,SocketError));
    FAnimatedFixture Ledge(*this); if(!Ledge.Start(true)) return false;
    bool SawFall=false,SawJump=false;
    for(int I=0;I<60;++I){Ledge.Step(1.f/60,FVector::ForwardVector);SawFall|=Ledge.Anim->PoseIndex==3;SawJump|=Ledge.Anim->PoseIndex==2;}
    TestTrue(TEXT("Ledge directly falls"),SawFall); TestFalse(TEXT("No false ascent at ledge"),SawJump);
    return true;
}
#endif
