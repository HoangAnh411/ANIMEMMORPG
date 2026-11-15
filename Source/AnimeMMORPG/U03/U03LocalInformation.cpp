#include "U01/U01PlayerController.h"
#include "U03Encounter.h"
#include "U03FeedbackWindow.h"
#include "U02/U02NetworkState.h"
#include "GameFramework/GameStateBase.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02LabDummy.h"
#include "Components/CapsuleComponent.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "SceneView.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
DEFINE_LOG_CATEGORY_STATIC(LogU03Retry,Log,All);
namespace {
FVector InformationPoint(AActor* A)
{auto* C=Cast<AU01Character>(A);return A->GetActorLocation()+FVector(0,0,90-(C?C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight():0));}
FGuid InformationId(AActor* A)
{if(auto* C=Cast<AU01Character>(A))return C->NetworkPawnId;if(auto* D=Cast<AU02LabDummy>(A))return D->NetworkPawnId;return {};}
bool ProjectInformation(const AU01PlayerController* PC,AActor* A,FVector2D& Screen,FVector2D& Center)
{
    auto* LP=PC->GetLocalPlayer();if(!LP||!LP->ViewportClient||!LP->ViewportClient->Viewport)return false;
    FSceneViewProjectionData Data;if(!LP->GetProjectionData(LP->ViewportClient->Viewport,Data))return false;
    const FIntRect Rect=Data.GetConstrainedViewRect();Center=FVector2D(Rect.Width(),Rect.Height())*.5;
    if(!FSceneView::ProjectWorldToScreen(InformationPoint(A),Rect,Data.ComputeViewProjectionMatrix(),Screen))return false;
    Screen-=FVector2D(Rect.Min.X,Rect.Min.Y);
    return Screen.X>=0&&Screen.Y>=0&&Screen.X<Rect.Width()&&Screen.Y<Rect.Height();
}
bool InformationClear(const AU01PlayerController* PC,AActor* A)
{
    FVector Camera;FRotator Rotation;PC->GetPlayerViewPoint(Camera,Rotation);FCollisionQueryParams Q(SCENE_QUERY_STAT(U03TabLOS),false);
    for(TActorIterator<AActor> It(PC->GetWorld());It;++It)if(It->IsA<APawn>()||It->FindComponentByClass<UU02VitalComponent>())Q.AddIgnoredActor(*It);
    return !PC->GetWorld()->LineTraceTestByChannel(Camera,InformationPoint(A),ECC_GameTraceChannel2,Q);
}
}
void AU01PlayerController::ToggleInformationTarget()
{
    if(!IsLocalPlayerController())return;
    if(InformationSubject.IsValid()){InformationSubject.Reset();bInformationVisible=false;TargetRetention={};return;}
    auto* E=AU03Encounter::ForSubject(GetPawn());if(!GetPawn())return;
    TOptional<AnimeMMORPG::U03::FTargetRank> Best;
    for(TActorIterator<AActor> It(GetWorld());It;++It)
    {
        auto* A=*It;auto* V=A->FindComponentByClass<UU02VitalComponent>();
        if(!((E&&A==E->GetSnapshot().Monster)||A->ActorHasTag(TEXT("U03TabFixture")))||!V||V->GetSnapshot().bDead)continue;
        const double Distance=FVector::DistSquared(GetPawn()->GetActorLocation(),A->GetActorLocation());if(!AnimeMMORPG::U03::WithinTargetSelectionRange(Distance))continue;
        FVector2D Screen,Center;if(!ProjectInformation(this,A,Screen,Center)||!InformationClear(this,A))continue;
        const FGuid Id=InformationId(A);if(!Id.IsValid())continue;
        AnimeMMORPG::U03::FTargetRank Rank{FVector2D::DistSquared(Screen,Center),Distance,Id.ToString(EGuidFormats::Digits)};
        if(Best.IsSet()&&!(Rank<Best.GetValue()))continue;
        Best=Rank;InformationSubject=A;InformationPawn=Id;InformationLife=V->GetSnapshot().Generation;
        InformationEncounter=E?E->GetSnapshot().Id:FGuid();InformationRevision=E?E->GetSnapshot().Revision:0;
    }
    TargetRetention={};UpdateEncounterInformation();
}
void AU01PlayerController::UpdateEncounterInformation()
{
    auto* E=AU03Encounter::ForSubject(GetPawn());
    if(E&&!E->GetSnapshot().bClosed&&E->GetSnapshot().Result&&PresentedResultRevision!=E->GetSnapshot().Revision)
    {PresentedResultRevision=E->GetSnapshot().Revision;LockControls(EU01ControlState::AwaitingResume,TEXT("EncounterResult"));}
    bInformationVisible=false;auto* A=InformationSubject.Get();if(!A)return;
    auto* V=A->FindComponentByClass<UU02VitalComponent>();const bool SameEncounter=E?E->GetSnapshot().Id==InformationEncounter&&E->GetSnapshot().Revision==InformationRevision:!InformationEncounter.IsValid();
    const bool SameLife=V&&V->GetSnapshot().Generation==InformationLife&&InformationId(A)==InformationPawn;
    const bool Clear=InformationClear(this,A);
    if(!GetPawn()||!SameEncounter||!TargetRetention.Update(GetWorld()->GetTimeSeconds(),FVector::Distance(GetPawn()->GetActorLocation(),A->GetActorLocation()),V&&!V->GetSnapshot().bDead,SameLife,Clear))
    {InformationSubject.Reset();TargetRetention={};return;}
    FVector2D Center;bInformationVisible=Clear&&ProjectInformation(this,A,InformationScreen,Center);
}
bool AU01PlayerController::InformationTarget(FVector2D& Screen,FString& Text) const
{
    if(!bInformationVisible||!InformationSubject.IsValid())return false;
    auto* V=InformationSubject->FindComponentByClass<UU02VitalComponent>();if(!V||V->GetSnapshot().bDead)return false;
    Screen=InformationScreen;Text=FString::Printf(TEXT("TARGET HP %d/%d"),V->GetSnapshot().HP,V->GetSnapshot().MaxHP);return true;
}
bool AU01PlayerController::RecentHitInformation(FVector2D& Screen,FString& Text) const
{
    if(!IsLocalPlayerController()||GetNetMode()==NM_DedicatedServer)return false;
    const auto* P=Cast<AU01Character>(GetPawn());if(!P||!P->Combat)return false;
    const auto& S=P->Combat->GetCombatSnapshot();const auto* E=AU03Encounter::ForSubject(GetPawn());
    if(!E||E->GetSnapshot().bClosed||S.EncounterId!=E->GetSnapshot().Id||S.EncounterRevision!=E->GetSnapshot().Revision)return false;
    const auto* Clock=GetWorld()->GetGameState();const double Now=Clock?Clock->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();
    const FU02ConfirmedResult* Latest=nullptr;
    for(TActorIterator<AU02NetworkState> It(GetWorld());It;++It)for(const auto& R:It->Results)
    {
        if(R.PresentationKind||R.Source!=S.PawnId||R.SourceLife!=S.LifeGeneration||R.EncounterId!=S.EncounterId||R.EncounterRevision!=S.EncounterRevision||!R.Action||R.Defense!=uint8(AnimeMMORPG::U03::EDefense::Hit))continue;
        if(AnimeMMORPG::U03::FeedbackRemaining(R.Timestamp,Now)<=0)continue;
        if(!Latest||R.Timestamp>Latest->Timestamp||(R.Timestamp==Latest->Timestamp&&R.Serial>Latest->Serial))Latest=&R;
    }
    if(!Latest)return false;
    auto* A=E->GetSnapshot().Monster.Get();if(!A||A->NetworkPawnId!=Latest->Target||A->Vital->GetSnapshot().Generation!=Latest->TargetLife)return false;
    FVector2D Center;
    if(!AnimeMMORPG::U03::RecentHitVisible(Latest->Timestamp,Now,true,ProjectInformation(this,A,Screen,Center),InformationClear(this,A)))return false;
    const auto V=A->Vital->GetSnapshot();Text=FString::Printf(TEXT("HIT HP %d/%d"),V.HP,V.MaxHP);return true;
}
void AU01PlayerController::RequestEncounterRetry()
{
    auto* E=AU03Encounter::ForSubject(GetPawn());if(!E)return;
    QuarantineHeldKeys();LockControls(EU01ControlState::AwaitingResume,TEXT("Retry"));
    const auto S=E->GetSnapshot();ServerEncounterRetry(S.Id,S.Revision,++RetrySequence);
}
void AU01PlayerController::ServerEncounterRetry_Implementation(FGuid Id,uint64 Revision,uint64 Sequence)
{
    auto* E=AU03Encounter::ForSubject(GetPawn());const bool Accepted=E&&E->Retry(this,Id,Revision,Sequence);
    UE_LOG(LogU03Retry,Display,TEXT("U03C2_RETRY owner=%s claim=%s revision=%llu sequence=%llu accepted=%d current=%s currentRevision=%llu"),*GetPathName(),*Id.ToString(),Revision,Sequence,Accepted,E?*E->GetSnapshot().Id.ToString():TEXT("none"),E?E->GetSnapshot().Revision:0);
}
void AU01PlayerController::U03C2RetryClaim(const FString& Text,uint64 Revision,uint64 Sequence)
{
#if !UE_BUILD_SHIPPING
    FGuid Id;
    if(!FParse::Param(FCommandLine::Get(),TEXT("U02FProbe"))||!GetWorld()->GetMapName().EndsWith(TEXT("L_NetworkLab"))||!FGuid::Parse(Text,Id))return;
    // Probe the product request through this controller's real owned RPC channel. No fixture reset path.
    RetrySequence=FMath::Max(RetrySequence,Sequence);ServerEncounterRetry(Id,Revision,Sequence);
#endif
}
void AU01PlayerController::OpenRegressionLab()
{if(IsLocalPlayerController())ClientTravel(GetWorld()->GetOutermost()->GetName()+TEXT("?U03Regression=1"),TRAVEL_Absolute);}
