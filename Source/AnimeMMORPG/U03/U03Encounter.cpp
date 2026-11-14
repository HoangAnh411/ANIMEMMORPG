#include "U03Encounter.h"
#include "U01/U01PlayerController.h"
#include "U02/U02CombatComponent.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02CollisionWorld.h"
#include "U02/U02LabDummy.h"
#include "AIController.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/GameSession.h"
#include "UObject/ConstructorHelpers.h"
#include "DrawDebugHelpers.h"
#include "Engine/Canvas.h"
#include "Kismet/GameplayStatics.h"
#include <cmath>
using namespace AnimeMMORPG::U03;
namespace {
FVector FeetOf(AActor* A){auto* C=Cast<AU01Character>(A);return A->GetActorLocation()-FVector(0,0,C?C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight():0);}
}
AU03Monster::AU03Monster(const FObjectInitializer& I):Super(I)
{
    PrimaryActorTick.bCanEverTick=true;AIControllerClass=AAIController::StaticClass();AutoPossessAI=EAutoPossessAI::PlacedInWorldOrSpawned;
    auto* Body=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MonsterBlockout"));Body->SetupAttachment(RootComponent);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Shape(TEXT("/Engine/BasicShapes/Cone.Cone"));
    Body->SetStaticMesh(Shape.Object);Body->SetRelativeScale3D(FVector(.8,.8,1.7));Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);Body->SetCanEverAffectNavigation(false);
}
void AU03Monster::Tick(float Dt)
{
    Super::Tick(Dt);if(GetNetMode()==NM_DedicatedServer)return;
    const auto S=Combat->GetCombatSnapshot();const FVector F=FeetOf(this);
    const bool Startup=S.bLocked&&S.Phase==uint8(AnimeMMORPG::U02::EPhase::Startup);
    const bool Active=S.bLocked&&S.Phase==uint8(AnimeMMORPG::U02::EPhase::Active);
    if(auto* Body=Cast<UStaticMeshComponent>(GetDefaultSubobjectByName(TEXT("MonsterBlockout"))))Body->SetRelativeRotation(FRotator(Startup?-30:Active?55:S.bLocked?15:0,0,0));
    if(S.bLocked)
    {
        const FRotator R(0,S.AimYawDegrees,0);const FVector Center=F+R.RotateVector(FVector(100,0,90));
        DrawDebugBox(GetWorld(),Center,FVector(100,60,90),R.Quaternion(),Active?FColor::Red:Startup?FColor::Yellow:FColor::Silver,false,0,0,Active?4:1);
        DrawDebugDirectionalArrow(GetWorld(),F+FVector(0,0,190),F+FVector(0,0,190)+R.Vector()*(Startup?70:Active?180:35),20,FColor::White,false,0,0,3);
        DrawDebugString(GetWorld(),F+FVector(0,0,220),Startup?TEXT("WINDUP >>>"):Active?TEXT("STRIKE !"):TEXT("RECOVER ..."),nullptr,FColor::White,0,true);
    }
}
AU03Encounter::AU03Encounter(){bReplicates=true;bAlwaysRelevant=true;SetReplicateMovement(false);}
void AU03Encounter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(AU03Encounter,Snapshot);}
void AU03Encounter::Initialize(AU01PlayerController* PC,AU01Character* P,const FTransform& PS,const FTransform& MS,int32 Station)
{
    check(HasAuthority());SetOwner(PC);PlayerSpawn=PS;MonsterSpawn=MS;Snapshot.Id=FGuid::NewGuid();Snapshot.Player=P;Snapshot.Station=Station;
    Snapshot.OwnerLabel=PC->PlayerState?PC->PlayerState->GetPlayerName():PC->GetName();
    FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Snapshot.Monster=GetWorld()->SpawnActor<AU03Monster>(AU03Monster::StaticClass(),MS,Params);
    P->SetActorTransform(PS,false,nullptr,ETeleportType::TeleportPhysics);
    GetWorld()->GetSubsystem<UU02CollisionWorld>()->RebaseResetSubject(P);Publish();
}
AU03Encounter* AU03Encounter::ForSubject(const AActor* A)
{
    if(!A||!A->GetWorld())return nullptr;
    for(TActorIterator<AU03Encounter> E(A->GetWorld());E;++E)if(E->Snapshot.Player==A||E->Snapshot.Monster==A)return *E;return nullptr;
}
bool AU03Encounter::CanDamage(const AActor* A,const AActor* B)
{
    auto* E=ForSubject(A);if(!E||E!=ForSubject(B)||E->Model.bClosed||E->bResetting||E->Model.Result!=EEncounterResult::Running)return false;
    return (A==E->Snapshot.Player&&B==E->Snapshot.Monster)||(B==E->Snapshot.Player&&A==E->Snapshot.Monster);
}
bool AU03Encounter::EnvironmentClear(FVector A,FVector B) const
{
    FCollisionQueryParams Q(SCENE_QUERY_STAT(U03MonsterLOS),false);
    // Only solid environment occludes; every pawn is ignored, including other stations.
    for(TActorIterator<APawn> P(GetWorld());P;++P)Q.AddIgnoredActor(*P);
    return !GetWorld()->LineTraceTestByChannel(A,B,ECC_GameTraceChannel2,Q);
}
FMonsterObservation AU03Encounter::Observe(double At,const TFunction<FVector(AActor*,double)>& Feet) const
{
    FMonsterObservation O;auto* P=Snapshot.Player.Get();auto* M=Snapshot.Monster.Get();
    if(!P||!M){O.bMonsterAlive=false;return O;}
    const FVector MF=Feet(M,At),PF=Feet(P,At);
    O.TargetDistance=FVector::Distance(MF,PF);O.SpawnDistance=FVector::Distance(MF,MonsterSpawn.GetLocation()-FVector(0,0,96));
    O.bTargetAlive=!P->Vital->GetSnapshot().bDead;O.bMonsterAlive=!M->Vital->GetSnapshot().bDead;
    O.bLineOfSight=EnvironmentClear(MF+FVector(0,0,90),PF+FVector(0,0,90));
    O.bAction=M->Combat->Model&&M->Combat->Model->Current()&&At<M->Combat->Model->Current()->End()&&At<M->Combat->Model->Current()->Cutoff;return O;
}
double AU03Encounter::NextBoundary(double From,double Through,const TFunction<FVector(AActor*,double)>& Feet,const TArray<AnimeMMORPG::U02::FTriangle>& Triangles) const
{
    if(Model.bClosed||Model.Result!=EEncounterResult::Running||!Snapshot.Player||!Snapshot.Monster||Through<=From)return Through;
    double Next=Through;auto* M=Snapshot.Monster.Get();auto* P=Snapshot.Player.Get();
    const FVector M0=Feet(M,From),M1=Feet(M,Through),P0=Feet(P,From),P1=Feet(P,Through);
    auto Crossings=[&](FVector A,FVector B,double R)
    {
        const FVector V=B-A;const double AA=V.SizeSquared(),BB=2*FVector::DotProduct(A,V),CC=A.SizeSquared()-R*R;
        if(AA==0)return;const double Disc=BB*BB-4*AA*CC;if(Disc<0)return;
        for(double X:{(-BB-FMath::Sqrt(Disc))/(2*AA),(-BB+FMath::Sqrt(Disc))/(2*AA)})if(X>=0&&X<=1)
        {
            const double T=FMath::Lerp(From,Through,X);
            if(T>From)Next=FMath::Min(Next,T);
            // Inclusive distance boundary and its first representable successor are distinct.
            const double After=std::nextafter(T,Through+1.);if(After>From&&After<=Through)Next=FMath::Min(Next,After);
        }
    };
    Crossings(M0-P0,M1-P1,200);Crossings(M0-P0,M1-P1,1000);
    const FVector Spawn=MonsterSpawn.GetLocation()-FVector(0,0,96);
    Crossings(M0-Spawn,M1-Spawn,1500);Crossings(M0-Spawn,M1-Spawn,50);
    const FVector Up(0,0,90);const bool Clear=EnvironmentClear(M0+Up,P0+Up);
    auto Changed=[&](double Alpha){return EnvironmentClear(FMath::Lerp(M0,M1,Alpha)+Up,FMath::Lerp(P0,P1,Alpha)+Up)!=Clear;};
    auto Contact=AnimeMMORPG::U02::FirstVisible(M0+Up,M1+Up,P0+Up,P1+Up,0,{true,0,1},Triangles,Changed);
    if(Contact.IsSet()){const double T=FMath::Lerp(From,Through,Contact.GetValue());if(T>From)Next=FMath::Min(Next,T);}
    return Next;
}
void AU03Encounter::BeforeContacts(double At,const TFunction<FVector(AActor*,double)>& Feet)
{
    if(Model.bClosed||Model.Result!=EEncounterResult::Running||!Snapshot.Monster)return;
    auto* M=Snapshot.Monster.Get();const auto O=Observe(At,Feet);const auto D=DecideMonster(EMonsterState(Snapshot.AI),O);
    if(D.bCancel)GetWorld()->GetSubsystem<UU02CollisionWorld>()->ApplyLifecycle(M->Combat,At,ECutoff::Return,false);
    Snapshot.AI=uint8(D.State);bResetOnBarrier|=D.bReset;
    if(O.bAction&&D.State==EMonsterState::Action)
    {
        const double Yaw=(Feet(Snapshot.Player,At)-Feet(M,At)).Rotation().Yaw;
        if(M->Combat->Model->UpdateAim(At,Yaw)){M->Combat->StartupTurn.Retarget(At,Yaw);M->Combat->Publish(At,true);}
    }
    LastDecision=At;Publish();
}
void AU03Encounter::AfterBarrier(double At)
{
    if(Model.bClosed||Model.Result!=EEncounterResult::Running||!Snapshot.Monster)return;
    auto* M=Snapshot.Monster.Get();auto* AI=Cast<AAIController>(M->GetController());
    if(bResetOnBarrier){bResetOnBarrier=false;ResetSubjects(At,false);Snapshot.AI=uint8(EMonsterState::Idle);Publish();return;}
    const auto State=EMonsterState(Snapshot.AI);
    if(State==EMonsterState::Return){if(AI)AI->MoveToLocation(MonsterSpawn.GetLocation(),0,false,true,false,false,nullptr,false);return;}
    if(State==EMonsterState::Chase){if(AI)AI->MoveToLocation(Snapshot.Player->GetActorLocation(),0,false,true,false,false,nullptr,false);return;}
    if(AI)AI->StopMovement();
    if(State==EMonsterState::Action&&!M->Combat->Model->Current())
        M->Combat->SubmitMonsterIntent(++MonsterCommand,At,(Snapshot.Player->GetActorLocation()-M->GetActorLocation()).Rotation().Yaw);
}
void AU03Encounter::ResetSubjects(double At,bool Both)
{
    TGuardValue<bool> Reset(bResetting,true);auto* W=GetWorld()->GetSubsystem<UU02CollisionWorld>();
    TArray<AU01Character*> Subjects;if(Both)Subjects.Add(Snapshot.Player);Subjects.Add(Snapshot.Monster);
    for(auto* P:Subjects)W->MarkDead(P->Vital->GetLife());
    for(auto* P:Subjects)
    {
        if(auto* AI=Cast<AAIController>(P->GetController()))AI->StopMovement();
        check(P->Combat->ResetEncounterCombat(At));P->GetU01Movement()->ResetEncounterMotor();
        if(Both)P->SetActorTransform(P==Snapshot.Player?PlayerSpawn:MonsterSpawn,false,nullptr,ETeleportType::TeleportPhysics);
        W->RebaseResetSubject(P);
    }
}
bool AU03Encounter::Retry(AU01PlayerController* Requester,FGuid Id,uint64 Revision,uint64 Sequence)
{
    if(!HasAuthority()||Id!=Snapshot.Id||!Model.AdmitRetry(Revision,Sequence,Requester==GetOwner()&&Requester&&Requester->GetPawn()==Snapshot.Player))return false;
    const double At=GetWorld()->GetTimeSeconds();GetWorld()->GetSubsystem<UU02CollisionWorld>()->DrainAt(At);
    ResetSubjects(At,true);Model.CommitRetry();Snapshot.AI=uint8(EMonsterState::Idle);bResetOnBarrier=false;Publish();return true;
}
void AU03Encounter::ConfirmDefeat(AActor* Subject,double At)
{
    if(!HasAuthority()||(Subject!=Snapshot.Player&&Subject!=Snapshot.Monster)||!Model.Defeat(Subject==Snapshot.Monster))return;
    Snapshot.AI=uint8(Snapshot.Monster->Vital->GetSnapshot().bDead?EMonsterState::Defeated:EMonsterState::Idle);
    for(auto* P:{Snapshot.Player.Get(),Snapshot.Monster.Get()})
    {GetWorld()->GetSubsystem<UU02CollisionWorld>()->ApplyLifecycle(P->Combat,At,ECutoff::Return,false);if(auto* AI=Cast<AAIController>(P->GetController()))AI->StopMovement();}
    Publish();
}
void AU03Encounter::Close(double At)
{
    if(!HasAuthority()||Model.bClosed)return;Model.bClosed=true;
    for(auto* P:{Snapshot.Player.Get(),Snapshot.Monster.Get()})if(P){GetWorld()->GetSubsystem<UU02CollisionWorld>()->MarkDead(P->Vital->GetLife());if(auto* AI=Cast<AAIController>(P->GetController()))AI->StopMovement();}
    Publish();if(Snapshot.Monster)Snapshot.Monster->Destroy();SetOwner(nullptr);
}
void AU03Encounter::Publish()
{
    Snapshot.Revision=Model.Revision;Snapshot.Result=uint8(Model.Result);Snapshot.bClosed=Model.bClosed;
    for(auto* P:{Snapshot.Player.Get(),Snapshot.Monster.Get()})if(P)
    {P->Combat->Snapshot.EncounterId=Snapshot.Id;P->Combat->Snapshot.EncounterRevision=Snapshot.Revision;P->ForceNetUpdate();}
    ForceNetUpdate();
}
AU03EncounterGameMode::AU03EncounterGameMode()
{
    HUDClass=AU03EncounterHUD::StaticClass();
    static ConstructorHelpers::FClassFinder<APawn> Pawn(TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Character"));DefaultPawnClass=Pawn.Class;
    static ConstructorHelpers::FClassFinder<APlayerController> PC(TEXT("/Game/AnimeMMORPG/U01/Blueprints/BP_U01Controller"));PlayerControllerClass=PC.Class;
}
void AU03EncounterGameMode::RestartPlayer(AController* Controller)
{
    Super::RestartPlayer(Controller);auto* PC=Cast<AU01PlayerController>(Controller);auto* P=PC?Cast<AU01Character>(PC->GetPawn()):nullptr;
    if(P&&UGameplayStatics::ParseOption(OptionsString,TEXT("U03TabFixture"))==TEXT("1"))
    {
        P->SetActorLocation(FVector(15000,0,98.15),false,nullptr,ETeleportType::TeleportPhysics);GetWorld()->GetSubsystem<UU02CollisionWorld>()->RebaseResetSubject(P);
        for(TActorIterator<AU02LabDummy> D(GetWorld());D;++D)if(D->ActorHasTag(TEXT("U03TabFixture")))return;
        const FVector Positions[]={FVector(15500,45,78.15),FVector(15500,45,78.15),FVector(16000,45,78.15),FVector(15600,250,0),FVector(17000,-200,0)};
        for(int I=0;I<UE_ARRAY_COUNT(Positions);++I)
        {
            const FTransform X(Positions[I]);auto* D=GetWorld()->SpawnActorDeferred<AU02LabDummy>(AU02LabDummy::StaticClass(),X);
            D->NetworkPawnId=FGuid(703,2,9,I+1);D->Tags.Add(TEXT("U03TabFixture"));UGameplayStatics::FinishSpawningActor(D,X);
            auto* Label=NewObject<UTextRenderComponent>(D);Label->SetupAttachment(D->GetRootComponent());Label->SetRelativeLocation(FVector(0,0,220+I*22));Label->SetRelativeRotation(FRotator(0,180,0));Label->SetWorldSize(16);Label->SetText(FText::FromString(FString::Printf(TEXT("TAB FIXTURE ID%d | %s"),I+1,I<2?TEXT("coincident tie"):I==2?TEXT("same screen ray / farther"):TEXT("screen/distance candidate"))));Label->RegisterComponent();
        }
        return; // information fixture only, no extra gameplay encounter or AI
    }
    if(!P||IsRegression()||AU03Encounter::ForSubject(P))return;
    TSet<int32> Occupied;for(TActorIterator<AU03Encounter> E(GetWorld());E;++E)if(!E->GetSnapshot().bClosed)Occupied.Add(E->GetSnapshot().Station);
    int32 Station=0;while(Occupied.Contains(Station))++Station;
    if(Station>=4){if(GameSession)GameSession->KickPlayer(PC,FText::FromString(TEXT("C2 lab has four encounter stations")));return;}
    const FVector Base(15000,Station*5000,98.15);
    auto* E=GetWorld()->SpawnActor<AU03Encounter>();E->Initialize(PC,P,FTransform(FRotator::ZeroRotator,Base),FTransform(FRotator(0,180,0),Base+FVector(500,0,0)),Station);
}
bool AU03EncounterGameMode::IsRegression() const {return UGameplayStatics::ParseOption(OptionsString,TEXT("U03Regression"))==TEXT("1");}
void AU03EncounterGameMode::PreLogin(const FString& Options,const FString& Address,const FUniqueNetIdRepl& UniqueId,FString& ErrorMessage)
{
    Super::PreLogin(Options,Address,UniqueId,ErrorMessage);if(IsRegression()||!ErrorMessage.IsEmpty())return;
    int32 Count=0;for(TActorIterator<AU03Encounter> E(GetWorld());E;++E)if(!E->GetSnapshot().bClosed)++Count;
    if(Count>=4)ErrorMessage=TEXT("C2 lab has four encounter stations");
}
void AU03EncounterGameMode::Logout(AController* Exiting)
{
    if(Exiting)if(auto* E=AU03Encounter::ForSubject(Exiting->GetPawn())){E->Close(GetWorld()->GetTimeSeconds());E->Destroy();}Super::Logout(Exiting);
}
void AU03EncounterHUD::DrawHUD()
{
    Super::DrawHUD();auto* PC=Cast<AU01PlayerController>(PlayerOwner);if(!PC)return;
    FVector2D Screen;FString Text;
    if(PC->InformationTarget(Screen,Text))
    {
        DrawLine(Screen.X-12,Screen.Y,Screen.X-5,Screen.Y,FLinearColor::White,2);
        DrawLine(Screen.X+5,Screen.Y,Screen.X+12,Screen.Y,FLinearColor::White,2);
        DrawLine(Screen.X,Screen.Y-12,Screen.X,Screen.Y-5,FLinearColor::White,2);
        DrawText(Text,FLinearColor::White,Screen.X+16,Screen.Y-12,nullptr,1.);
    }
    if(auto* E=AU03Encounter::ForSubject(PC->GetPawn()))
    {
        const auto S=E->GetSnapshot();
        DrawText(FString::Printf(TEXT("C2 | %s | %s"),*S.OwnerLabel,S.Result==1?TEXT("WON - Escape / Retry"):S.Result==2?TEXT("LOST - Escape / Retry"):TEXT("Running")),FLinearColor::White,20,20,nullptr,1.2);
        const auto* P=Cast<AU01Character>(PC->GetPawn());if(P)DrawText(FString::Printf(TEXT("HP %d/%d"),P->Vital->GetSnapshot().HP,P->Vital->GetSnapshot().MaxHP),FLinearColor::White,20,45,nullptr,1.2);
        DrawText(FString::Printf(TEXT("[%s] target information | dodge, parry or E during WINDUP"),*PC->GetPreferences().Keys[AnimeMMORPG::U01::Target].GetDisplayName().ToString()),FLinearColor::White,20,70);
    }
}
