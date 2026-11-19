#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "U01/U01DodgeInput.h"
#include "U01/U01PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "U03/U03ActionModel.h"

using namespace AnimeMMORPG::U01;
struct FU04R1InputAccess
{
 static void Edge(AU01PlayerController* PC,FKey K,bool Down,bool Locked=false)
 {if(Down){PC->ObservedKeys.Add(K);PC->ReleaseGate.Down(K,Locked);}else{PC->ObservedKeys.Remove(K);PC->ReleaseGate.Up(K);}}
 static FVector2D Snapshot(AU01PlayerController* PC,const FPreferences& P)
 {return ObservedDodgeDirection(PC->ObservedKeys,PC->ReleaseGate,P);}
};
namespace
{
constexpr auto U04R1Flags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter;
struct FAdapter
{
 TSet<FKey> Observed;FReleaseGate Gate;FPreferences Preferences;TArray<FVector2D> Sent;
 void Edge(FKey K,bool Down,bool Locked=false)
 {
  const bool New=IsNewObservedPress(Observed,K,Down);
  if(Down){Observed.Add(K);Gate.Down(K,Locked);}else{Observed.Remove(K);Gate.Up(K);}
  if(New&&!Locked&&Gate.Allows(K)&&CanonicalKey(K)==Preferences.Keys[Dodge])Sent.Add(Snapshot());
 }
 FVector2D Snapshot() const{return ObservedDodgeDirection(Observed,Gate,Preferences);}
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU04R1Edges,"AnimeMMORPG.U04.R1.Input.EdgeOrder",U04R1Flags)
bool FU04R1Edges::RunTest(const FString&)
{
 FAdapter A;A.Edge(EKeys::W,true);A.Edge(EKeys::LeftShift,true);
 TestEqual(TEXT("W then dodge, same dispatch frame"),A.Sent.Last(),FVector2D(1,0));
 A.Edge(EKeys::LeftShift,true);TestEqual(TEXT("repeat has no action"),A.Sent.Num(),1);
 A.Edge(EKeys::W,false);A.Edge(EKeys::D,true);
 TestEqual(TEXT("sent snapshot immutable"),A.Sent[0],FVector2D(1,0));
 FAdapter B;B.Edge(EKeys::LeftShift,true);B.Edge(EKeys::W,true);
 TestEqual(TEXT("dodge then W"),B.Sent[0],FVector2D::ZeroVector);
 FAdapter C;C.Edge(EKeys::W,true);C.Edge(EKeys::W,false);C.Edge(EKeys::LeftShift,true);
 TestEqual(TEXT("W released before dodge"),C.Sent[0],FVector2D::ZeroVector);
 using namespace AnimeMMORPG;
 U02::FLifeId Life{FGuid(1,2,3,4),1};U03::FTimelineModel Model{Life};U03::FAdmissionContext Context;Context.bDodgeEnabled=true;
 TArray<U03::FActiveInterval> Out;
 Model.SubmitBatchUnopposed({{1,Life,U03::ECommand::Dodge,0,0,B.Sent[0]}},Context,Out);
 TestEqual(TEXT("zero direction retains backward model fallback"),Model.Dodge().Direction,FVector(-1,0,0));
 FAdapter D;D.Edge(EKeys::W,true);D.Edge(EKeys::D,true);D.Edge(EKeys::LeftShift,true);
 U03::FTimelineModel Diagonal{Life};Diagonal.SubmitBatchUnopposed({{1,Life,U03::ECommand::Dodge,0,0,D.Sent[0]}},Context,Out);
 D.Edge(EKeys::W,false);D.Edge(EKeys::S,true);
 TestTrue(TEXT("model normalizes frozen diagonal"),Diagonal.Dodge().Direction.Equals(FVector(1,1,0).GetSafeNormal(),1.e-12));
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU04R1Axes,"AnimeMMORPG.U04.R1.Input.BindingsAxesAliases",U04R1Flags)
bool FU04R1Axes::RunTest(const FString&)
{
 const FKey Keys[]={EKeys::W,EKeys::S,EKeys::A,EKeys::D};
 const FVector2D Expected[]={FVector2D(1,0),FVector2D(-1,0),FVector2D(0,-1),FVector2D(0,1)};
 for(int32 I=0;I<4;++I){FAdapter A;A.Edge(Keys[I],true);TestEqual(TEXT("cardinal"),A.Snapshot(),Expected[I]);}
 FAdapter A;A.Edge(EKeys::W,true);A.Edge(EKeys::S,true);A.Edge(EKeys::A,true);A.Edge(EKeys::D,true);
 TestEqual(TEXT("opposing axes cancel"),A.Snapshot(),FVector2D::ZeroVector);
 A.Edge(EKeys::S,false);A.Edge(EKeys::A,false);TestEqual(TEXT("release opponents"),A.Snapshot(),FVector2D(1,1));
 FAdapter B;B.Preferences.Keys[Forward]=EKeys::H;B.Preferences.Keys[Right]=EKeys::LeftControl;B.Preferences.Keys[Dodge]=EKeys::J;
 B.Edge(EKeys::W,true);TestEqual(TEXT("old binding excluded"),B.Snapshot(),FVector2D::ZeroVector);
 B.Edge(EKeys::H,true);B.Edge(EKeys::LeftControl,true);B.Edge(EKeys::RightControl,true);B.Edge(EKeys::J,true);
 TestEqual(TEXT("rebound keys and alias counted once"),B.Sent.Last(),FVector2D(1,1));
 B.Edge(EKeys::LeftControl,false);TestEqual(TEXT("other alias still held"),B.Snapshot(),FVector2D(1,1));
 B.Edge(EKeys::LeftControl,true,true);B.Edge(EKeys::RightControl,false);TestEqual(TEXT("quarantined alias excluded"),B.Snapshot(),FVector2D(1,0));
 B.Edge(EKeys::RightControl,true);TestEqual(TEXT("unblocked alias independent"),B.Snapshot(),FVector2D(1,1));
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU04R1Quarantine,"AnimeMMORPG.U04.R1.Input.QuarantineLifecycle",U04R1Flags)
bool FU04R1Quarantine::RunTest(const FString&)
{
 for(const TCHAR* Transition:{TEXT("menu"),TEXT("focus loss"),TEXT("rebind"),TEXT("Retry"),TEXT("Resume")})
 {
  FAdapter A;A.Edge(EKeys::W,true);A.Edge(EKeys::LeftShift,true);A.Gate.Lock();A.Edge(EKeys::LeftShift,true);
  TestEqual(Transition,A.Snapshot(),FVector2D::ZeroVector);TestEqual(TEXT("held dodge not repeated"),A.Sent.Num(),1);
  A.Edge(EKeys::LeftShift,false);A.Edge(EKeys::LeftShift,true);TestEqual(TEXT("direction still quarantined"),A.Sent.Last(),FVector2D::ZeroVector);
  A.Edge(EKeys::W,false);A.Edge(EKeys::W,true);TestEqual(TEXT("physical release rearms direction"),A.Snapshot(),FVector2D(1,0));
  FAdapter EnterLocked;EnterLocked.Edge(EKeys::W,true,true);EnterLocked.Edge(EKeys::LeftShift,true,true);
  TestEqual(TEXT("press during lock excluded"),EnterLocked.Snapshot(),FVector2D::ZeroVector);TestEqual(TEXT("no action during lock"),EnterLocked.Sent.Num(),0);
 }
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FU04R1Players,"AnimeMMORPG.U04.R1.Input.LocalPlayerIsolation",U04R1Flags)
bool FU04R1Players::RunTest(const FString&)
{
 FTestWorldWrapper W;W.CreateTestWorld(EWorldType::Game);
 auto* A=W.GetTestWorld()->SpawnActor<AU01PlayerController>();auto* B=W.GetTestWorld()->SpawnActor<AU01PlayerController>();
 auto* LA=NewObject<ULocalPlayer>(GEngine);auto* LB=NewObject<ULocalPlayer>(GEngine);A->SetPlayer(LA);B->SetPlayer(LB);
 FPreferences P;FU04R1InputAccess::Edge(A,EKeys::W,true);
 TestEqual(TEXT("A observed key"),FU04R1InputAccess::Snapshot(A,P),FVector2D(1,0));
 TestEqual(TEXT("B has no A edge"),FU04R1InputAccess::Snapshot(B,P),FVector2D::ZeroVector);
 FU04R1InputAccess::Edge(B,EKeys::S,true);FU04R1InputAccess::Edge(A,EKeys::W,true,true);
 TestEqual(TEXT("A quarantine independent"),FU04R1InputAccess::Snapshot(A,P),FVector2D::ZeroVector);
 TestEqual(TEXT("B unaffected"),FU04R1InputAccess::Snapshot(B,P),FVector2D(-1,0));
 TestTrue(TEXT("distinct actual local players"),A->GetLocalPlayer()==LA&&B->GetLocalPlayer()==LB&&LA!=LB);
 return true;
}
#endif
