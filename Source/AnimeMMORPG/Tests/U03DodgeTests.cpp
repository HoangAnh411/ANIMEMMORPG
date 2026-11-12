#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U03/U03ActionModel.h"
#include "U01/U01Character.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02VitalComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"
#include "AIController.h"
#include "Kismet/GameplayStatics.h"
using namespace AnimeMMORPG;
struct FU03B1Access
{
 static void HP(UU02VitalComponent* V,int32 Value){V->State.HP=Value;V->State.bDead=false;}
 static void Stale(UU02CombatComponent* C,uint64 Seq,uint64 Life){C->ServerCombat_Implementation(uint8(U03::ECommand::Dodge),Seq,0,0,C->GetCombatSnapshot().PawnId,Life,FVector2D(1,0));}
};
namespace
{
constexpr auto U03B1Flags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
U03::FAdmissionContext Enabled(){U03::FAdmissionContext C;C.bDodgeEnabled=true;return C;}
struct FModel
{
 U02::FLifeId Life{FGuid(1,2,3,4),1};U03::FTimelineModel M{Life};TArray<U03::FActiveInterval> Out;uint64 Seq=0;
 U03::EAdmission Press(double At,U03::ECommand Command=U03::ECommand::Dodge,FVector2D Direction=FVector2D(1,0),double Yaw=0)
 {return M.SubmitBatchUnopposed({{++Seq,Life,Command,At,Yaw,Direction}},Enabled(),Out)[0].Result;}
 void Advance(double T){M.AdvanceUnopposed(T,Out);}
};
struct FWorld:FTestWorldWrapper
{
 AU01Character* P;UU02CollisionWorld* Collision;uint64 Seq=0;UBoxComponent* Ground;
 FWorld(FVector Extents=FVector(10000,10000,50))
 {
  CreateTestWorld(EWorldType::Game);auto* W=GetTestWorld();W->GetWorldSettings()->DefaultGameMode=AGameModeBase::StaticClass();
  auto* Floor=W->SpawnActor<AActor>();Ground=NewObject<UBoxComponent>(Floor);Floor->SetRootComponent(Ground);Ground->SetBoxExtent(Extents);Ground->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Ground->SetCollisionResponseToAllChannels(ECR_Block);Ground->RegisterComponent();Floor->SetActorLocation(FVector(0,0,-50));
  P=Spawn(FVector(0,0,98),1);BeginPlayInTestWorld();for(int I=0;I<30;++I)TickTestWorld(1.f/60);Collision=W->GetSubsystem<UU02CollisionWorld>();
 }
 AU01Character* Spawn(FVector Position,uint32 Id)
 {
  auto* W=GetTestWorld();FTransform T(Position);auto* C=W->SpawnActorDeferred<AU01Character>(AU01Character::StaticClass(),T,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);C->NetworkPawnId=FGuid(Id,0,0,1);UGameplayStatics::FinishSpawningActor(C,T);auto* PC=W->SpawnActor<AAIController>();PC->Possess(C);return C;
 }
 double Now()const{return GetTestWorld()->GetTimeSeconds();}
 void Press(double At,U03::ECommand Command=U03::ECommand::Dodge,FVector2D Direction=FVector2D(1,0),double Yaw=0)
 {P->Combat->SubmitCombatIntent(Command,++Seq,Now(),Yaw,Direction);Collision->DrainAt(At);}
 UBoxComponent* Box(FVector Center,FVector Half,FRotator Rotation=FRotator::ZeroRotator)
 {auto* A=GetTestWorld()->SpawnActor<AActor>();auto* B=NewObject<UBoxComponent>(A);A->SetRootComponent(B);B->SetBoxExtent(Half);B->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);B->SetCollisionResponseToAllChannels(ECR_Block);B->RegisterComponent();A->SetActorLocationAndRotation(Center,Rotation);return B;}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeDeadlines,"AnimeMMORPG.U03.B1.ModelDeadlinesAndSequentialCharges",U03B1Flags)
bool FDodgeDeadlines::RunTest(const FString&)
{
 FModel X;TestEqual(TEXT("first admitted"),X.Press(0),U03::EAdmission::Accepted);const auto First=X.M.Dodge();
 TestTrue(TEXT("before motion end"),First.Moving(.249999));TestFalse(TEXT("exact .25 motion end"),First.Moving(.25));TestTrue(TEXT("before .35 lock"),First.Locked(.349999));TestFalse(TEXT("exact .35 unlocked"),First.Locked(.35));
 TestEqual(TEXT("buffer waiting .60"),X.Press(.5),U03::EAdmission::Queued);X.Advance(.60);TestEqual(TEXT("exact spacing consumes pending"),X.M.Dodge().Sequence,uint64(2));TestEqual(TEXT("zero charges"),X.M.Dodge().Charges,0);TestEqual(TEXT("second does not reset recharge"),X.M.Dodge().RestoreAt,2.);
 TestEqual(TEXT("no-charge reject"),X.Press(.7),U03::EAdmission::Resource);TestFalse(TEXT("no-charge no buffer"),X.M.GetPendingDodge().IsSet());X.Advance(1.999999);TestEqual(TEXT("no early charge"),X.M.Dodge().Charges,0);X.Advance(2.);TestEqual(TEXT("charge at2"),X.M.Dodge().Charges,1);TestEqual(TEXT("sequential next4"),X.M.Dodge().RestoreAt,4.);X.Advance(4.);TestEqual(TEXT("full at4"),X.M.Dodge().Charges,2);TestEqual(TEXT("no energy spent"),X.M.Resources().Energy(),100.);
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeBuffer,"AnimeMMORPG.U03.B1.ModelBufferReplacementAndPriority",U03B1Flags)
bool FDodgeBuffer::RunTest(const FString&)
{
 for(int Case=0;Case<3;++Case){FModel X;X.Press(0);X.Press(Case==0?.45:.5);if(Case==1)X.Press(.55,U03::ECommand::Dodge,FVector2D(0,1),90);if(Case==2)X.M.ClearPending();X.Advance(1.);TestEqual(TEXT("exact expiry/control clear do not start"),X.M.Dodge().Sequence,Case==1?uint64(2):uint64(1));if(Case==1)TestTrue(TEXT("captured camera-local normalized direction"),X.M.Dodge().Direction.Equals(FVector(-1,0,0),1.e-6));}
 FModel X;auto C=Enabled();auto R=X.M.SubmitBatchUnopposed({{1,X.Life,U03::ECommand::Attack,0,0},{2,X.Life,U03::ECommand::Dodge,0,0}},C,X.Out);TestFalse(TEXT("dodge priority blocks attack"),X.M.Current()!=nullptr);TestEqual(TEXT("single dodge"),X.M.Dodge().Sequence,uint64(1));
 auto Duplicate=X.M.SubmitBatchUnopposed({{2,X.Life,U03::ECommand::Dodge,0,0}},C,X.Out);TestEqual(TEXT("duplicate rejected"),Duplicate[0].Result,U03::EAdmission::Stale);
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeCancel,"AnimeMMORPG.U03.B1.ModelStartupReplacementAndLifecycle",U03B1Flags)
bool FDodgeCancel::RunTest(const FString&)
{
 for(double T:{.159999,.16,.22}){FModel X;X.Press(0,U03::ECommand::Attack);const auto Result=X.Press(T);TestEqual(TEXT("only startup cancellable"),Result,T<.16?U03::EAdmission::Accepted:U03::EAdmission::Busy);TestEqual(TEXT("rejection leaves charges"),X.M.Dodge().Charges,T<.16?1:2);TestEqual(TEXT("rejection preserves old action"),X.M.Current()!=nullptr,T>=.16);}
 FModel X;X.Press(0);X.Press(.5);X.M.CancelUnopposed(U03::ECutoff::Death,.55,true,X.Out);X.Advance(3.);TestEqual(TEXT("death removes pending"),X.M.Dodge().Sequence,uint64(1));TestEqual(TEXT("dead cannot dodge"),X.Press(3.),U03::EAdmission::Locked);
 FModel Ground;Ground.Press(0);Ground.M.CancelUnopposed(U03::ECutoff::LostGround,.1,true,Ground.Out);TestFalse(TEXT("lost ground ends movement"),Ground.M.Dodge().Moving(.1));TestEqual(TEXT("stale grounded context cannot dodge"),Ground.Press(.6),U03::EAdmission::Locked);auto Life=Ground.Life;++Life.Generation;TestTrue(TEXT("reset"),Ground.M.ResetLife(Life,.6));TestEqual(TEXT("reset charges"),Ground.M.Dodge().Charges,2);
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeDistance,"AnimeMMORPG.U03.B1.RuntimeSweptDistanceAndLongUpdate",U03B1Flags)
bool FDodgeDistance::RunTest(const FString&)
{
 for(double Step:{1./30,1./60,1./120,1.})
 {FWorld W;const double S=W.Now();const FVector Before=W.P->GetActorLocation();W.Press(S);for(double T=S+Step;T<S+.25;T+=Step)W.Collision->DrainAt(T);W.Collision->DrainAt(S+.25);const FVector After=W.P->GetActorLocation();TestTrue(TEXT("300cm +/-5 swept native motor"),FMath::Abs((After-Before).Size2D()-300.)<=5.);W.Collision->DrainAt(S+.35);TestFalse(TEXT("unlock .35"),W.P->Combat->GetCombatSnapshot().bLocked);TestEqual(TEXT("charge consumed"),W.P->Combat->GetCombatSnapshot().DodgeCharges,1);W.ForwardErrorMessages(this);}
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeObstacle,"AnimeMMORPG.U03.B1.RuntimeWallPersonAndCliff",U03B1Flags)
bool FDodgeObstacle::RunTest(const FString&)
{
 for(int Case=0;Case<3;++Case)
 {FWorld W(Case==2?FVector(150,10000,50):FVector(10000,10000,50));const double S=W.Now();if(Case==0)W.Box(FVector(180,0,150),FVector(10,200,150));if(Case==1)W.Spawn(FVector(180,0,98),2);W.Press(S);W.Collision->DrainAt(S+1.);const double X=W.P->GetActorLocation().X;TestTrue(TEXT("capsule never crosses wall/person or centre leaves cliff"),X<(Case==2?151.:145.));TestTrue(TEXT("no falling over intentionally stopped edge"),W.P->GetU01Movement()->IsMovingOnGround());TestEqual(TEXT("blocked still consumes"),W.P->Combat->GetCombatSnapshot().DodgeCharges,1);W.ForwardErrorMessages(this);}
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeRuntimeCancel,"AnimeMMORPG.U03.B1.RuntimeStartupCancelResetAndDamage",U03B1Flags)
bool FDodgeRuntimeCancel::RunTest(const FString&)
{
 FWorld W;const double S=W.Now();W.Press(S,U03::ECommand::Attack);W.Press(S+.1);TestEqual(TEXT("accepted dodge"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(1));W.Collision->DrainAt(S+.6);TestEqual(TEXT("cancelled sword never hits"),W.Collision->Confirmed.Num(),0);const double Next=W.P->Combat->GetCombatSnapshot().DodgeNextStart;W.Press(Next);const auto Sequence=W.P->Combat->GetCombatSnapshot().DodgeSequence;W.Press(Next+.2,U03::ECommand::Attack);TestEqual(TEXT("dodge lock rejects sword"),W.P->Combat->GetCombatSnapshot().DodgeSequence,Sequence);TestEqual(TEXT("no new sword admitted in dodge lock"),W.P->Combat->GetCombatSnapshot().ActionSequence,uint64(1));
 W.P->Combat->ResetLabCombat();TestEqual(TEXT("reset charges"),W.P->Combat->GetCombatSnapshot().DodgeCharges,2);TestEqual(TEXT("reset sequence"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(0));W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeTerrain,"AnimeMMORPG.U03.B1.RuntimeStepSlopeAndRemovedFloor",U03B1Flags)
bool FDodgeTerrain::RunTest(const FString&)
{
 for(float Height:{30.f,60.f}){FWorld W;const double S=W.Now();W.Box(FVector(170,0,Height*.5),FVector(70,200,Height*.5));W.Press(S);W.Collision->DrainAt(S+.25);TestTrue(TEXT("native step policy"),Height<45?W.P->GetActorLocation().X>230:W.P->GetActorLocation().X<110);W.ForwardErrorMessages(this);}
 for(double Angle:{30.,44.,46.,60.})
 {FWorld W;const double R=FMath::DegreesToRadians(Angle);W.Box(FVector(400*FMath::Cos(R)+10*FMath::Sin(R),0,400*FMath::Sin(R)-10*FMath::Cos(R)),FVector(400,200,10),FRotator(Angle,0,0));const double S=W.Now();W.Press(S);W.Collision->DrainAt(S+.25);TestTrue(TEXT("dodge keeps walkable slope threshold"),Angle<45?W.P->GetActorLocation().Z>170:W.P->GetActorLocation().Z<158);W.ForwardErrorMessages(this);}
 {FWorld W;const double S=W.Now();W.Press(S);W.Collision->DrainAt(S+.05);const FVector Before=W.P->GetActorLocation();W.Ground->SetCollisionEnabled(ECollisionEnabled::NoCollision);W.Collision->DrainAt(S+.2);TestTrue(TEXT("removed current support stops horizontal motion"),(W.P->GetActorLocation()-Before).Size2D()<1.);TestTrue(TEXT("lost ground falls"),W.P->GetU01Movement()->IsFalling());W.ForwardErrorMessages(this);}
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeIncoming,"AnimeMMORPG.U03.B1.RuntimeNoIFrameAndDeathCutoff",U03B1Flags)
bool FDodgeIncoming::RunTest(const FString&)
{
 for(bool Lethal:{false,true})
 {FWorld W;const double S=W.Now();auto* Enemy=W.Spawn(FVector(-150,0,98),2);W.Collision->bCharacterFixtureTargets=true;W.Collision->FixtureCritRoll=.5;W.Box(FVector(100,0,150),FVector(10,200,150));if(Lethal)FU03B1Access::HP(W.P->Vital,60);
  Enemy->Combat->SubmitAttackIntent(1,0,0);W.Press(S);W.Collision->DrainAt(S+1.);TestEqual(TEXT("dodge has no iframe"),W.P->Vital->GetSnapshot().HP,Lethal?0:940);if(Lethal){TestTrue(TEXT("motion stopped at death hit"),W.P->Combat->GetCombatSnapshot().DodgeMotionEnd<=S+.16);TestTrue(TEXT("no movement past wall/death"),W.P->GetActorLocation().X<50.);}
  W.ForwardErrorMessages(this);}
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeGate,"AnimeMMORPG.U03.B1.RuntimeMenuAndStaleLife",U03B1Flags)
bool FDodgeGate::RunTest(const FString&)
{
 FWorld W;const double S=W.Now();W.Press(S);W.P->Combat->SetControlPlaying(false);W.Collision->DrainAt(S+.25);TestTrue(TEXT("menu does not cancel accepted motion"),W.P->GetActorLocation().X>295);W.P->Combat->SetControlPlaying(true);W.Press(S+.5);TestTrue(TEXT("waiting dodge queued"),W.P->Combat->GetAdmission().PendingCommand!=0);W.P->Combat->SetControlPlaying(false);W.Collision->DrainAt(S+.7);TestEqual(TEXT("control lock clears queued dodge"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(1));
 const uint64 OldLife=W.P->Combat->GetCombatSnapshot().LifeGeneration;W.P->Combat->ResetLabCombat();W.P->Combat->SetControlPlaying(true);FU03B1Access::Stale(W.P->Combat,100,OldLife);W.Collision->DrainAt(S+.7);TestEqual(TEXT("old life cannot dodge or spend"),W.P->Combat->GetCombatSnapshot().DodgeCharges,2);TestEqual(TEXT("old life no sequence"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(0));W.ForwardErrorMessages(this);return true;
}
#endif
