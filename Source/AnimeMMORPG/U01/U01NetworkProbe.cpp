#include "U01NetworkProbe.h"
#include "U01Character.h"
#include "U01PlayerController.h"
#include "U01AnimInstance.h"
#include "U01Menu.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/GameStateBase.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UObjectIterator.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Engine/NetDriver.h"
#include "Engine/NetConnection.h"
#include "HAL/IConsoleManager.h"
#include "Misc/App.h"
#include "Misc/ConfigCacheIni.h"

DEFINE_LOG_CATEGORY_STATIC(LogU01Network,Log,All);
void UU01NetworkProbe::OnWorldBeginPlay(UWorld& World)
{
    Super::OnWorldBeginPlay(World);
#if !UE_BUILD_SHIPPING
    Enabled=FParse::Param(FCommandLine::Get(),TEXT("U01FProbe"));
    Run=FGuid::NewGuid().ToString();
    if(Enabled&&World.GetNetMode()!=NM_Client)
    {
        // A replicated movement base must resolve to the same server actor on
        // every client; independent local movable floors are not valid bases.
        auto* Floor=World.SpawnActor<AStaticMeshActor>(FVector(0,4000,-50),FRotator::ZeroRotator);
        Floor->SetReplicates(true);Floor->SetReplicateMovement(true);Floor->bAlwaysRelevant=true;
        Floor->Tags.Add(TEXT("U01F_TestGround"));
        auto* Shape=Floor->GetStaticMeshComponent();Shape->SetMobility(EComponentMobility::Movable);
        Shape->SetIsReplicated(true);
        Shape->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
        Floor->SetActorScale3D(FVector(300,30,1));Shape->SetCollisionProfileName(TEXT("BlockAll"));
        UE_LOG(LogU01Network,Display,TEXT("FixtureGround center=(0,4000,-50) sizeCm=(30000,3000,100) world=%s net=%d"),*World.GetPathName(),int32(World.GetNetMode()));
    }
#endif
}
void UU01NetworkProbe::Tick(float Dt)
{
    // Opt-in diagnosis only: sample every game frame, before the normal 5 Hz
    // collector. UTC and monotonic timestamps share the host clock on localhost.
    if(Enabled&&FParse::Param(FCommandLine::Get(),TEXT("U01FPerf")))
    {
        auto* World=GetWorld();auto D=MakeShared<FJsonObject>();
        D->SetStringField(TEXT("utc"),FDateTime::UtcNow().ToIso8601());
        D->SetNumberField(TEXT("wall"),FPlatformTime::Seconds());D->SetNumberField(TEXT("dt"),Dt);
        D->SetNumberField(TEXT("pid"),FPlatformProcess::GetCurrentProcessId());D->SetNumberField(TEXT("netMode"),int32(World->GetNetMode()));
        D->SetBoolField(TEXT("focus"),FApp::HasFocus());D->SetNumberField(TEXT("frame"),double(GFrameCounter));
        auto CV=[&](const TCHAR* Name){const auto* V=IConsoleManager::Get().FindConsoleVariable(Name);D->SetNumberField(Name,V?V->GetFloat():-999);};
        for(const auto* Name:{TEXT("t.MaxFPS"),TEXT("t.IdleWhenNotForeground"),TEXT("r.VSync"),TEXT("r.ScreenPercentage"),TEXT("net.UseAdaptiveNetUpdateFrequency")})CV(Name);
        bool Throttle=true;GConfig->GetBool(TEXT("/Script/UnrealEd.EditorPerformanceSettings"),TEXT("bThrottleCPUWhenNotForeground"),Throttle,GEditorSettingsIni);
        D->SetBoolField(TEXT("editorThrottle"),Throttle);
        if(const auto* Driver=World->GetNetDriver())
        {
#if DO_ENABLE_NET_TEST
            const auto& P=Driver->PacketSimulationSettings;
            D->SetNumberField(TEXT("pktLag"),P.PktLag);D->SetNumberField(TEXT("pktLagMin"),P.PktLagMin);D->SetNumberField(TEXT("pktLagMax"),P.PktLagMax);
            D->SetNumberField(TEXT("pktLoss"),P.PktLoss);D->SetNumberField(TEXT("pktOrder"),P.PktOrder);D->SetNumberField(TEXT("pktDup"),P.PktDup);
            D->SetNumberField(TEXT("incomingLagMin"),P.PktIncomingLagMin);D->SetNumberField(TEXT("incomingLagMax"),P.PktIncomingLagMax);D->SetNumberField(TEXT("incomingLoss"),P.PktIncomingLoss);
#endif
            TArray<TSharedPtr<FJsonValue>> Connections;
            auto Add=[&](const UNetConnection* N){if(!N)return;auto V=MakeShared<FJsonObject>();
                V->SetNumberField(TEXT("avgLagSeconds"),N->AvgLag);V->SetNumberField(TEXT("inPackets"),N->InPackets);V->SetNumberField(TEXT("outPackets"),N->OutPackets);
                V->SetNumberField(TEXT("inLost"),N->InPacketsLost);V->SetNumberField(TEXT("outLost"),N->OutPacketsLost);Connections.Add(MakeShared<FJsonValueObject>(V));};
            Add(Driver->ServerConnection);for(const auto& N:Driver->ClientConnections)Add(N.Get());D->SetArrayField(TEXT("connections"),Connections);
        }
        TArray<AActor*> Actors;UGameplayStatics::GetAllActorsOfClass(World,AU01Character::StaticClass(),Actors);TArray<TSharedPtr<FJsonValue>> Values;
        for(auto* A:Actors){auto* C=CastChecked<AU01Character>(A);auto* M=C->GetU01Movement();auto V=MakeShared<FJsonObject>();
            V->SetStringField(TEXT("id"),C->NetworkPawnId.ToString());V->SetBoolField(TEXT("local"),C->IsLocallyControlled());
            V->SetNumberField(TEXT("x"),C->GetActorLocation().X);V->SetNumberField(TEXT("z"),C->GetActorLocation().Z);
            V->SetNumberField(TEXT("repX"),C->GetReplicatedMovement().Location.X);V->SetNumberField(TEXT("repZ"),C->GetReplicatedMovement().Location.Z);
            V->SetNumberField(TEXT("meshX"),C->GetMesh()->GetComponentLocation().X);V->SetNumberField(TEXT("meshZ"),C->GetMesh()->GetComponentLocation().Z);
            V->SetNumberField(TEXT("speed"),C->GetVelocity().Size2D());V->SetNumberField(TEXT("updatesHz"),C->GetNetUpdateFrequency());V->SetNumberField(TEXT("minUpdatesHz"),C->GetMinNetUpdateFrequency());
            V->SetNumberField(TEXT("smoothMode"),int32(M->NetworkSmoothingMode));V->SetNumberField(TEXT("smoothSeconds"),M->NetworkSimulatedSmoothLocationTime);
            V->SetNumberField(TEXT("pingMs"),C->GetPlayerState()?C->GetPlayerState()->GetPingInMilliseconds():-1);
            Values.Add(MakeShared<FJsonValueObject>(V));}
        D->SetArrayField(TEXT("pawns"),Values);FString Text;FJsonSerializer::Serialize(D,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text));UE_LOG(LogU01Network,Display,TEXT("U01F_PERF %s"),*Text);
    }
    if(!Enabled)return;Elapsed+=Dt;if(Elapsed<.2f)return;Elapsed=0;
    auto* W=GetWorld();auto J=MakeShared<FJsonObject>();FString SHA;FParse::Value(FCommandLine::Get(),TEXT("U01SourceSHA="),SHA);
    J->SetStringField(TEXT("sourceSHA"),SHA);J->SetStringField(TEXT("runID"),Run);J->SetStringField(TEXT("utc"),FDateTime::UtcNow().ToIso8601());
    J->SetNumberField(TEXT("frameDt"),Dt);J->SetNumberField(TEXT("pid"),FPlatformProcess::GetCurrentProcessId());J->SetStringField(TEXT("world"),W->GetPathName());
    J->SetNumberField(TEXT("worldType"),int32(W->WorldType));J->SetNumberField(TEXT("netMode"),int32(W->GetNetMode()));J->SetNumberField(TEXT("seconds"),W->GetTimeSeconds());
    if(const auto* Context=GEngine->GetWorldContextFromWorld(W))J->SetStringField(TEXT("context"),Context->ContextHandle.ToString());
    J->SetNumberField(TEXT("localPlayers"),W->GetGameInstance()?W->GetGameInstance()->GetNumLocalPlayers():0);
    int32 Widgets=0;for(TObjectIterator<UU01Menu> It;It;++It)if(It->GetWorld()==W&&It->IsInViewport())++Widgets;
    J->SetNumberField(TEXT("visibleMenus"),Widgets);
    TArray<AActor*> Actors;UGameplayStatics::GetAllActorsOfClass(W,AU01Character::StaticClass(),Actors);TArray<TSharedPtr<FJsonValue>> Pawns;
    for(auto* Actor:Actors)
    {
        auto* C=CastChecked<AU01Character>(Actor);auto* M=C->GetU01Movement();auto P=MakeShared<FJsonObject>();
        P->SetStringField(TEXT("id"),C->NetworkPawnId.ToString());P->SetStringField(TEXT("path"),C->GetPathName());
        P->SetStringField(TEXT("owner"),GetPathNameSafe(C->GetOwner()));P->SetStringField(TEXT("controller"),GetPathNameSafe(C->GetController()));
        P->SetNumberField(TEXT("playerId"),C->GetPlayerState()?C->GetPlayerState()->GetPlayerId():-1);
        P->SetNumberField(TEXT("role"),int32(C->GetLocalRole()));P->SetNumberField(TEXT("remoteRole"),int32(C->GetRemoteRole()));P->SetBoolField(TEXT("local"),C->IsLocallyControlled());
        P->SetNumberField(TEXT("x"),C->GetActorLocation().X);P->SetNumberField(TEXT("y"),C->GetActorLocation().Y);P->SetNumberField(TEXT("z"),C->GetActorLocation().Z);
        P->SetNumberField(TEXT("speed"),C->GetVelocity().Size2D());P->SetNumberField(TEXT("vz"),C->GetVelocity().Z);P->SetNumberField(TEXT("repVz"),C->GetReplicatedMovement().LinearVelocity.Z);P->SetNumberField(TEXT("mode"),int32(M->MovementMode));
        P->SetNumberField(TEXT("locks"),M->GetLockMask());P->SetNumberField(TEXT("motorSeconds"),M->GetMotorTimeSeconds());
        P->SetBoolField(TEXT("sprint"),M->IsSprinting());P->SetNumberField(TEXT("corrections"),M->CorrectionCount);P->SetNumberField(TEXT("jumpCount"),C->JumpCurrentCount);
        if(const auto* Anim=Cast<UU01AnimInstance>(C->GetMesh()->GetAnimInstance()))
        {P->SetNumberField(TEXT("pose"),Anim->PoseIndex);P->SetNumberField(TEXT("animSpeed"),Anim->GroundSpeed);P->SetNumberField(TEXT("animVz"),Anim->VerticalSpeed);}
        Pawns.Add(MakeShared<FJsonValueObject>(P));
    }
    J->SetArrayField(TEXT("pawns"),Pawns);FString Text;FJsonSerializer::Serialize(J,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text));
    UE_LOG(LogU01Network,Display,TEXT("U01F_NET %s"),*Text);
}
void AU01PlayerController::U01NetFixture(const FString& Command)
{
#if !UE_BUILD_SHIPPING
    if(!IsLocalPlayerController()||!FParse::Param(FCommandLine::Get(),TEXT("U01FProbe")))return;
    auto* C=Cast<AU01Character>(GetPawn());if(!C)return;
    if(Command==TEXT("reset")){SetControlRotation(FRotator::ZeroRotator);ServerU01NetProbe(0,0,C->NetworkPawnId);}
    if(Command==TEXT("speed"))
    {
        C->GetU01Movement()->ProbeSpeed=2000;ServerU01NetProbe(1,2000,C->NetworkPawnId);
        UE_LOG(LogU01Network,Display,TEXT("ClientProbe Speed id=%s override=2000 duration=2.0"),*C->NetworkPawnId.ToString());
        FTimerHandle Timer;TWeakObjectPtr<AU01Character> Weak=C;
        GetWorldTimerManager().SetTimer(Timer,[Weak](){if(Weak.IsValid())Weak->GetU01Movement()->ProbeSpeed=0;},2.f,false);
    }
    if(Command==TEXT("jump")){C->StopJumping();C->Jump();C->GetU01Movement()->Velocity.Z+=800;UE_LOG(LogU01Network,Display,TEXT("ClientProbe ExtraJump id=%s velocityZ=%.3f"),*C->NetworkPawnId.ToString(),C->GetVelocity().Z);ServerU01NetProbe(2,800,C->NetworkPawnId);}
    if(Command==TEXT("other"))
    {
        TArray<AActor*> Actors;UGameplayStatics::GetAllActorsOfClass(this,AU01Character::StaticClass(),Actors);
        for(auto* A:Actors)if(A!=C){ServerU01NetProbe(3,2000,CastChecked<AU01Character>(A)->NetworkPawnId);break;}
    }
#endif
}
void AU01PlayerController::ServerU01NetProbe_Implementation(uint8 Kind,float Claim,FGuid Target)
{
#if !UE_BUILD_SHIPPING
    if(!FParse::Param(FCommandLine::Get(),TEXT("U01FProbe")))return;
    auto* C=Cast<AU01Character>(GetPawn());if(!C)return;
    if(Target!=C->NetworkPawnId){UE_LOG(LogU01Network,Display,TEXT("ProbeRejected Ownership target=%s own=%s controller=%s"),*Target.ToString(),*C->NetworkPawnId.ToString(),*GetPathName());return;}
    if(Kind==0)
    {
        const int32 ProbePlayerId=C->GetPlayerState()?C->GetPlayerState()->GetPlayerId():0;
        C->SetActorLocation(FVector(-5000,3500+(ProbePlayerId%2)*600,110),false,nullptr,ETeleportType::TeleportPhysics);
        C->GetU01Movement()->ResetFixtureState();C->GetU01Movement()->ForceReplicationUpdate();C->GetU01Movement()->ForceClientAdjustment();C->SetActorRotation(FRotator::ZeroRotator);SetControlRotation(FRotator::ZeroRotator);
        ClientSetLocation(C->GetActorLocation(),FRotator::ZeroRotator); // One explicit fixture reset, not locomotion replication.
        UE_LOG(LogU01Network,Display,TEXT("FixtureReset id=%s player=%d"),*Target.ToString(),ProbePlayerId);
    }
    else UE_LOG(LogU01Network,Display,TEXT("ProbeRejected %s claim=%.1f id=%s mode=%d count=%d serverMax=%.1f"),Kind==1?TEXT("Overspeed"):Kind==2?TEXT("ExtraJump"):TEXT("Unknown"),Claim,*Target.ToString(),int32(C->GetCharacterMovement()->MovementMode),C->JumpCurrentCount,C->GetU01Movement()->GetMaxSpeed());
#endif
}
