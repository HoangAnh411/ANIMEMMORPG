#include "U03Encounter.h"
#include "U03FeedbackWindow.h"
#include "U02/U02NetworkState.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02LabDummy.h"
#include "U01/U01PlayerController.h"
#include "GameFramework/GameStateBase.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Canvas.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundWaveProcedural.h"

DEFINE_LOG_CATEGORY_STATIC(LogU03Presentation,Log,All);
void AU03EncounterHUD::DrawPresentation()
{
    if(GetNetMode()==NM_DedicatedServer||!Canvas||!PlayerOwner||!PlayerOwner->GetLocalPlayer())return;
    const auto* Clock=GetWorld()->GetGameState();const double Now=Clock?Clock->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();
    auto ProjectPoint=[this](FVector P,FVector2D& Out){return PlayerOwner->ProjectWorldLocationToScreen(P,Out,true);};
    auto Line=[&](FVector A,FVector B,float Width)
    {FVector2D X,Y;if(ProjectPoint(A,X)&&ProjectPoint(B,Y))DrawLine(X.X,X.Y,Y.X,Y.Y,FLinearColor::White,Width);};
    // Product Canvas cues do not depend on debug drawing or on-screen messages.
    for(TActorIterator<AU01Character> It(GetWorld());It;++It)
    {
        auto* P=*It;const auto& C=P->Combat->GetCombatSnapshot();
        const FVector Feet=P->GetActorLocation()-FVector(0,0,P->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
        FVector2D Screen;if(!ProjectPoint(Feet+FVector(0,0,205),Screen))continue;
        const bool Action=C.ActionSequence&&C.bLocked&&Now>=C.StartSeconds&&Now<C.StartSeconds+C.Duration&&C.Phase!=uint8(AnimeMMORPG::U02::EPhase::Cancelled);
        const TCHAR* Phase=Now<C.StartSeconds+C.ActiveStart?TEXT("WINDUP >>>"):Now<C.StartSeconds+C.ActiveEnd?TEXT("!! STRIKE !!"):TEXT("... RECOVER");
        if(Action)DrawText(Phase,FLinearColor::White,Screen.X-40,Screen.Y);
        if(C.bGuard){DrawText(TEXT("|== GUARD ==|"),FLinearColor::White,Screen.X-45,Screen.Y+18);}
        if(C.HardCC&&Now<C.HardEnd)DrawText(C.HardCC==5?TEXT("/ / GUARD BREAK / /"):TEXT("[ HARD CC ]"),FLinearColor::White,Screen.X-45,Screen.Y+35);
        if(C.DodgeSequence&&Now>=C.DodgeStart&&Now<C.DodgeLockEnd)DrawText(Now<C.DodgeMotionEnd?TEXT("<< DODGE >>"):TEXT("DODGE RECOVER"),FLinearColor::White,Screen.X-45,Screen.Y+18);
        if(Action&&P->IsA<AU03Monster>())
        {
            const FRotator R(0,C.AimYawDegrees,0);FVector V[8];
            for(int32 I=0;I<8;++I)V[I]=Feet+R.RotateVector(FVector((I&1)?200:0,(I&2)?60:-60,(I&4)?180:0));
            const float Width=Now<C.StartSeconds+C.ActiveStart?1.f:Now<C.StartSeconds+C.ActiveEnd?3.f:1.f;
            for(int32 I=0;I<8;++I)for(int32 Bit:{1,2,4})if(!(I&Bit))Line(V[I],V[I|Bit],Width);
            const FVector A=Feet+FVector(0,0,190),B=A+R.Vector()*180;
            Line(A,B,2);Line(B,B-R.RotateVector(FVector(25,15,0)),2);Line(B,B-R.RotateVector(FVector(25,-15,0)),2);
        }
    }
    TArray<FU02ConfirmedResult> Events;
    for(TActorIterator<AU02NetworkState> N(GetWorld());N;++N)
    {
        if(!N->HasActorBegunPlay())continue;
        if(!N->HasAuthority())FeedbackSerial=FMath::Max(FeedbackSerial,N->InitialHistorySerial);
        Events.Append(N->Results);Events.Append(N->PresentationEvents);
    }
    Events.Sort([](const auto& A,const auto& B){return A.Serial<B.Serial;});
    for(const auto& R:Events)
    {
        const bool New=AnimeMMORPG::U03::ConsumeFeedback(R.Serial,FeedbackSerial);
        AU01Character* Source=nullptr;AActor* Target=nullptr;
        for(TActorIterator<AU01Character> P(GetWorld());P;++P)
        {
            if(P->NetworkPawnId==R.Source&&P->Vital->GetSnapshot().Generation==R.SourceLife)Source=*P;
            if(P->NetworkPawnId==R.Target&&P->Vital->GetSnapshot().Generation==R.TargetLife)Target=*P;
        }
        for(TActorIterator<AU02LabDummy> D(GetWorld());D;++D)if(D->NetworkPawnId==R.Target&&D->Vital->GetSnapshot().Generation==R.TargetLife)Target=*D;
        auto* E=AU03Encounter::ForSubject(Source);
        if(!Source||!Target||AnimeMMORPG::U03::FeedbackRemaining(R.Timestamp,Now)<=0)continue;
        if(R.EncounterId.IsValid()){if(!E||E->GetSnapshot().bClosed||E->GetSnapshot().Id!=R.EncounterId||E->GetSnapshot().Revision!=R.EncounterRevision)continue;}
        else if(E)continue;
        const uint8 Kind=R.PresentationKind?R.PresentationKind+2:R.Defense; // hit0 block1 parry2 miss3 feint4 interrupt5 break6 X7
        const TCHAR* Labels[]={TEXT("+ HIT +"),TEXT("|== BLOCK ==|"),TEXT("( PARRY )"),TEXT("-- MISS --"),TEXT("< FEINT >"),TEXT("// INTERRUPT //"),TEXT("/ / BREAK / /"),TEXT("< X RELEASE >")};
        FVector2D Screen;const bool Visible=ProjectPoint(Target->GetActorLocation()+FVector(0,0,150),Screen)&&Screen.X>=0&&Screen.Y>=0&&Screen.X<Canvas->SizeX&&Screen.Y<Canvas->SizeY;
        if(Visible)
        {
            DrawText(Labels[FMath::Min<int32>(Kind,7)],FLinearColor::White,Screen.X-40,Screen.Y-20-(R.Serial%3)*18);
            if(Kind==2)for(int32 I=0;I<32;++I){const double A=2*PI*I/32,B=2*PI*(I+1)/32;DrawLine(Screen.X+40*FMath::Cos(A),Screen.Y+40*FMath::Sin(A),Screen.X+40*FMath::Cos(B),Screen.Y+40*FMath::Sin(B),FLinearColor::White,2);}
        }
        // Prime history silently on creation/reconnect. Old/late snapshots retain
        // visual lifetime only; one fresh sound at most per render sample.
        const bool Audio=AnimeMMORPG::U03::FreshFeedbackAudio(New,bFeedbackPrimed,Visible,R.Timestamp,Now);
        if(New)UE_LOG(LogU03Presentation,Display,TEXT("U03D_FEEDBACK serial=%llu kind=%u subject=%s life=%llu action=%llu encounter=%s revision=%llu at=%.9f now=%.9f audio=%d"),R.Serial,Kind,*R.Target.ToString(),R.TargetLife,R.Action,*R.EncounterId.ToString(),R.EncounterRevision,R.Timestamp,Now,Audio);
        if(!Audio)continue;
        FeedbackTone=NewObject<USoundWaveProcedural>(this);FeedbackTone->SetSampleRate(24000);FeedbackTone->NumChannels=1;FeedbackTone->Duration=.24f;
        TArray<int16> PCM;PCM.SetNumZeroed(5760);
        const double Frequencies[]={440,220,660,160,880,330,110,1320};
        for(int32 I=0;I<PCM.Num();++I)
        {
            const double T=I/24000.,Local=FMath::Fmod(T,.12);
            const double Hz=Kind==2?(T<.12?660.:990.):Frequencies[FMath::Min<int32>(Kind,7)]*(Kind==4?1.-T:Kind==5?1.+T:1.);
            const double Envelope=FMath::Min(1.,Local/.005)*FMath::Max(0.,1.-Local/.12);
            PCM[I]=int16(6000*Envelope*FMath::Sin(2*PI*Hz*Local));
        }
        FeedbackTone->QueueAudio(reinterpret_cast<const uint8*>(PCM.GetData()),PCM.Num()*sizeof(int16));UGameplayStatics::PlaySound2D(this,FeedbackTone);
    }
    bFeedbackPrimed=true;
}
