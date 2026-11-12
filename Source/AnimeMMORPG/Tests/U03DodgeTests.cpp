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
#include "Algo/Reverse.h"
using namespace AnimeMMORPG;
struct FU03B1Access
{
 static void Reverse(UU02CollisionWorld* W){Algo::Reverse(W->Sources);}
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
 FModel Empty;Empty.Press(0);Empty.Press(.6);Empty.Press(1.,U03::ECommand::Attack);TestEqual(TEXT("exhausted replacement rejected"),Empty.Press(1.05),U03::EAdmission::Resource);TestTrue(TEXT("exhausted replacement leaves startup"),Empty.M.Current()&&Empty.M.Current()->Startup(1.05));
 FModel CC;auto Context=Enabled();Context.bHardCC=true;auto Results=CC.M.SubmitBatchUnopposed({{1,CC.Life,U03::ECommand::Dodge,0,0}},Context,CC.Out);TestEqual(TEXT("hard CC admission gate fixture"),Results[0].Result,U03::EAdmission::Locked);TestEqual(TEXT("no charge consumed under CC fixture"),CC.M.Dodge().Charges,2);
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
 {FWorld W;const double S=W.Now();auto* Enemy=W.Spawn(FVector(350,0,98),2);W.Collision->bCharacterFixtureTargets=true;W.Collision->FixtureCritRoll=.5;if(Lethal)FU03B1Access::HP(W.P->Vital,60);
  Enemy->Combat->SubmitAttackIntent(1,0,180);W.Press(S);W.Collision->DrainAt(S+1.);TestEqual(TEXT("dodge has no iframe"),W.P->Vital->GetSnapshot().HP,Lethal?0:940);if(Lethal){TestTrue(TEXT("motion stopped at death hit"),W.P->Combat->GetCombatSnapshot().DodgeMotionEnd<=S+.16);TestTrue(TEXT("moving path committed exactly through lethal .16"),FMath::Abs(W.P->GetActorLocation().X-192.)<1.);}
  W.ForwardErrorMessages(this);}
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeGate,"AnimeMMORPG.U03.B1.RuntimeMenuAndStaleLife",U03B1Flags)
bool FDodgeGate::RunTest(const FString&)
{
 FWorld W;const double S=W.Now();W.Press(S);W.P->Combat->SetControlPlaying(false);W.Collision->DrainAt(S+.25);TestTrue(TEXT("menu does not cancel accepted motion"),W.P->GetActorLocation().X>295);W.P->Combat->SetControlPlaying(true);W.Press(S+.5);TestTrue(TEXT("waiting dodge queued"),W.P->Combat->GetAdmission().PendingCommand!=0);W.P->Combat->SetControlPlaying(false);W.Collision->DrainAt(S+.7);TestEqual(TEXT("control lock clears queued dodge"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(1));
 const uint64 OldLife=W.P->Combat->GetCombatSnapshot().LifeGeneration;W.P->Combat->ResetLabCombat();W.P->Combat->SetControlPlaying(true);FU03B1Access::Stale(W.P->Combat,100,OldLife);W.Collision->DrainAt(S+.7);TestEqual(TEXT("old life cannot dodge or spend"),W.P->Combat->GetCombatSnapshot().DodgeCharges,2);TestEqual(TEXT("old life no sequence"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(0));W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeBatch,"AnimeMMORPG.U03.B1.RuntimeBatchPriorityAndRejectedReplacement",U03B1Flags)
bool FDodgeBatch::RunTest(const FString&)
{
 FWorld W;const double S=W.Now();W.P->Combat->SubmitAttackIntent(1,0,0);W.P->Combat->SubmitCombatIntent(U03::ECommand::Dodge,2,0,0,FVector2D(1,1));W.Seq=2;W.Collision->DrainAt(S);TestEqual(TEXT("same timestamp dodge wins before attack"),W.P->Combat->GetCombatSnapshot().ActionSequence,uint64(0));TestEqual(TEXT("one dodge"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(1));W.Collision->DrainAt(S+.6);W.Press(S+.6);W.Press(S+1.,U03::ECommand::Attack);W.Press(S+1.05);TestEqual(TEXT("no charge keeps sword startup"),W.P->Combat->GetCombatSnapshot().Phase,uint8(U02::EPhase::Startup));TestEqual(TEXT("no charge does not change dodge"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(2));W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeSlow,"AnimeMMORPG.U03.B1.RuntimeSlowMotorBudgetFixture",U03B1Flags)
bool FDodgeSlow::RunTest(const FString&)
{
 FWorld W;auto* Motor=W.P->GetU01Movement();Motor->MaxWalkSpeed=50;Motor->MaxAcceleration=5;Motor->GroundFriction=100;Motor->BrakingDecelerationWalking=100000;
 // Labelled policy fixture only: B2 slow effect gameplay is not implemented.
 const double S=W.Now();const FVector Before=W.P->GetActorLocation();W.Press(S);W.Collision->DrainAt(S+.25);TestTrue(TEXT("low ordinary motor budget/friction does not scale dodge"),FMath::Abs((W.P->GetActorLocation()-Before).Size2D()-300.)<5.);TestEqual(TEXT("still one charge"),W.P->Combat->GetCombatSnapshot().DodgeCharges,1);W.ForwardErrorMessages(this);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeInteraction,"AnimeMMORPG.U03.B1.RuntimeInteractionClearsWaitingDodge",U03B1Flags)
bool FDodgeInteraction::RunTest(const FString&)
{
 for(auto Lock:{EU01MotorLock::Interacting,EU01MotorLock::Control})
 {FWorld W;const double S=W.Now();W.Press(S);W.Press(S+.5);TestTrue(TEXT("waiting precondition queued"),W.P->Combat->GetAdmission().PendingCommand!=0);W.P->GetU01Movement()->SetMotorLock(Lock,true);W.Collision->DrainAt(S+.65);TestEqual(TEXT("authority lock discards pending before .60"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(1));TestEqual(TEXT("no second charge spent"),W.P->Combat->GetCombatSnapshot().DodgeCharges,1);TestEqual(TEXT("pending cleared"),W.P->Combat->GetAdmission().PendingCommand,uint64(0));W.P->GetU01Movement()->SetMotorLock(Lock,false);W.Press(S+.7);TestEqual(TEXT("fresh press after unlock still valid"),W.P->Combat->GetCombatSnapshot().DodgeSequence,uint64(2));W.ForwardErrorMessages(this);}
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeRetained,"AnimeMMORPG.U03.B1.R1.RetainedWallSlideAndStepPrefixes",U03B1Flags)
bool FDodgeRetained::RunTest(const FString&)
{
 for(int Case=0;Case<3;++Case)
 {
  FWorld W;const double S=W.Now();W.Box(FVector(53,0,Case==2?15:150),FVector(10,Case==1?200:20,Case==2?15:150));
  const FVector2D Direction=Case==1?FVector2D(1,1):FVector2D(1,0);W.Press(S,U03::ECommand::Dodge,Direction);auto* M=W.P->GetU01Movement();
  const auto& Snapshot=W.P->Combat->GetCombatSnapshot();M->PlanDodge(S,S+1./240.,FVector(Direction.X,Direction.Y,0).GetSafeNormal(),Snapshot.LifeGeneration,Snapshot.DodgeSequence);
  for(double Offset:{.0002,.0005,.001,.002,.003,.004})
  {const double At=S+Offset;const auto Expected=M->DodgePositionAt(At);M->CommitDodge(At);TestTrue(TEXT("retained swept prefix exactly equals actual transform"),W.P->GetActorLocation().Equals(Expected,1.e-6));}
  W.ForwardErrorMessages(this);
 }
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgeMidHit,"AnimeMMORPG.U03.B1.R1.IncomingMidWallAndStepLethal",U03B1Flags)
bool FDodgeMidHit::RunTest(const FString&)
{
 for(bool Step:{false,true})for(bool Lethal:{false,true})
 {
  FVector Reference;double ReferenceTime=0;
  for(bool Short:{false,true})
  {
   FWorld W;const double S=W.Now();W.Box(FVector(Step?143:53,0,Step?15:150),FVector(Step?100:10,20,Step?15:150));
   auto* Enemy=W.Spawn(FVector(95.5,-150,98),2);W.Collision->bCharacterFixtureTargets=true;W.Collision->FixtureCritRoll=.5;if(Lethal)FU03B1Access::HP(W.P->Vital,60);
   Enemy->Combat->SubmitAttackIntent(1,0,90);W.Collision->DrainAt(S);W.Press(S+.159);
   auto* M=W.P->GetU01Movement();const auto Snapshot=W.P->Combat->GetCombatSnapshot();M->PlanDodge(S+.159,S+.159+1./240.,FVector(1,0,0),Snapshot.LifeGeneration,Snapshot.DodgeSequence);
   const double HitTime=S+.16;const FVector Expected=M->DodgePositionAt(HitTime);FVector AtHit;double ActualTime=-1;
   W.Collision->OnGeometryConfirmed.AddLambda([&](const U02::FHitCandidate& Hit){if(Hit.Id.Target.Pawn==W.P->NetworkPawnId){ActualTime=Hit.TimestampSeconds;AtHit=W.P->GetActorLocation();}});
   if(Short)for(double T=S+.1593;T<HitTime;T+=.0003)W.Collision->DrainAt(T);
   W.Collision->DrainAt(HitTime);
   TestEqual(TEXT("contact at incoming active entry, not chord crossing later"),ActualTime,HitTime);
   TestTrue(TEXT("contact geometry equals actual committed prefix"),AtHit.Equals(Expected,1.e-6));
   TestEqual(TEXT("real damage, no iframe"),W.P->Vital->GetSnapshot().HP,Lethal?0:940);
   if(Step)TestTrue(TEXT("hit occurs during vertical StepUp leg"),Expected.Z>98.2);
   if(!Short){Reference=AtHit;ReferenceTime=ActualTime;}else{TestTrue(TEXT("long and short update same contact position"),AtHit.Equals(Reference,1.e-6));TestEqual(TEXT("long and short update same hit time"),ActualTime,ReferenceTime);}
   if(Lethal){W.Collision->DrainAt(S+1.);TestTrue(TEXT("lethal cutoff preserves intermediate position"),W.P->GetActorLocation().Equals(AtHit,1.e-6));}
   AddInfo(FString::Printf(TEXT("U03B1_R1_MID step=%d lethal=%d short=%d expected=%.17g actual=%.17g position=%s"),Step,Lethal,Short,HitTime,ActualTime,*AtHit.ToString()));W.ForwardErrorMessages(this);
  }
 }
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDodgePairs,"AnimeMMORPG.U03.B1.R1.SimultaneousPawnCCD",U03B1Flags)
bool FDodgePairs::RunTest(const FString&)
{
 for(bool Follow:{false,true})
 {
  FVector ReferenceA,ReferenceB;
  for(bool Reverse:{false,true})for(bool Short:{false,true})
  {
   FWorld W;const double S=W.Now();auto* Other=W.Spawn(FVector(Follow?85:100,0,98.15),2);
   W.P->Combat->SubmitCombatIntent(U03::ECommand::Dodge,1,0,0,FVector2D(1,0));Other->Combat->SubmitCombatIntent(U03::ECommand::Dodge,1,0,0,FVector2D(Follow?1:-1,0));W.Collision->DrainAt(S);
   if(Reverse)FU03B1Access::Reverse(W.Collision);
   if(Short)for(double T=S+.0007;T<S+.25;T+=.0007)W.Collision->DrainAt(T);
   W.Collision->DrainAt(S+.25);const auto A=W.P->GetActorLocation(),B=Other->GetActorLocation();
   TestTrue(TEXT("moving capsules do not interpenetrate"),(A-B).Size2D()>=83.999);
   if(Follow)TestTrue(TEXT("following motion not blocked by stale peer transform"),A.X>295&&B.X>380);else TestTrue(TEXT("opposed dodges stop before crossing"),A.X<10&&B.X>90);
   if(!Reverse&&!Short){ReferenceA=A;ReferenceB=B;}else{TestTrue(TEXT("collection/update partition invariant A"),A.Equals(ReferenceA,1.e-5));TestTrue(TEXT("collection/update partition invariant B"),B.Equals(ReferenceB,1.e-5));}
   TestEqual(TEXT("one charge each"),Other->Combat->GetCombatSnapshot().DodgeCharges,1);W.ForwardErrorMessages(this);
  }
 }
 return true;
}
#endif
