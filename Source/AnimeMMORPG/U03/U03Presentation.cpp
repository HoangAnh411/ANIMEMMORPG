#include "U03Encounter.h"
#include "U03FeedbackWindow.h"
#include "U03InformationVisibility.h"
#include "U03TelegraphComponent.h"
#include "U02/U02NetworkState.h"
#include "U02/U02VitalComponent.h"
#include "U02/U02LabDummy.h"
#include "U01/U01PlayerController.h"
#include "GameFramework/GameStateBase.h"
#include "Components/CapsuleComponent.h"
#include "Components/AudioComponent.h"
#include "Engine/Canvas.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundWaveProcedural.h"
#include "Dom/JsonObject.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

DEFINE_LOG_CATEGORY_STATIC(LogU03Presentation,Log,All);
void AU03EncounterHUD::DrawPresentation()
{
    if(GetNetMode()==NM_DedicatedServer||!Canvas||!PlayerOwner||!PlayerOwner->GetLocalPlayer())return;
    const auto* PC=Cast<AU01PlayerController>(PlayerOwner);if(!PC)return;
    const bool Probe=FParse::Param(FCommandLine::Get(),TEXT("U03R1VisibilityProbe"));
    TArray<TSharedPtr<FJsonValue>> ActorRows,EventRows;
    const auto* Clock=GetWorld()->GetGameState();const double Now=Clock?Clock->GetServerWorldTimeSeconds():GetWorld()->GetTimeSeconds();
    FeedbackVoices.RemoveAll([&](const FFeedbackVoice& V)
    {
        if(!V.Audio.IsValid())return true;
        auto* Subject=V.Subject.Get();const auto* Vital=Subject?Subject->FindComponentByClass<UU02VitalComponent>():nullptr;
        auto* Source=V.Source.Get();const auto* SourceVital=Source?Source->FindComponentByClass<UU02VitalComponent>():nullptr;
        const auto* E=AU03Encounter::ForSubject(Subject);
        if(!SourceVital||SourceVital->GetSnapshot().Generation!=V.SourceLife||!Vital||!AnimeMMORPG::U03::SameFeedbackScope(Vital->GetSnapshot().Generation,V.Life,E?E->GetSnapshot().Id:FGuid(),V.Encounter,E?E->GetSnapshot().Revision:0,V.Revision))
        {V.Audio->Stop();UE_LOG(LogU03Presentation,Display,TEXT("U03D_AUDIO_STOP life=%llu revision=%llu reason=scope_changed"),V.Life,V.Revision);return true;}
        FVector2D Screen;
        if(!AnimeMMORPG::U03::PresentationVisible(PC,Subject,Subject->GetActorLocation()+FVector(0,0,150),Screen))
        {V.Audio->Stop();return true;}
        return false;
    });
    // Product Canvas cues do not depend on debug drawing or on-screen messages.
    for(TActorIterator<AU01Character> It(GetWorld());It;++It)
    {
        auto* P=*It;const auto& C=P->Combat->GetCombatSnapshot();
        const FVector Feet=P->GetActorLocation()-FVector(0,0,P->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
        FVector2D Screen;const bool Visible=AnimeMMORPG::U03::PresentationVisible(PC,P,Feet+FVector(0,0,205),Screen);
        if(Probe)
        {
            auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("subject"),P->NetworkPawnId.ToString());Row->SetBoolField(TEXT("visible"),Visible);
            Row->SetBoolField(TEXT("subjectClear"),AnimeMMORPG::U03::InformationClear(PC,P));Row->SetNumberField(TEXT("role"),P->GetLocalRole());
            int32 Clear=0,Blocked=0,Count=0;
            if(const auto* M=Cast<AU03Monster>(P))if(M->Telegraph)
            {
                FVector Camera;FRotator Rot;PC->GetPlayerViewPoint(Camera,Rot);
                for(const auto& Segment:M->Telegraph->GetSegments())
                {++Count;if(AnimeMMORPG::U03::InformationEnvironmentClear(GetWorld(),Camera,(Segment.A+Segment.B)*.5))++Clear;else ++Blocked;}
            }
            Row->SetNumberField(TEXT("worldDepthSegments"),Count);Row->SetNumberField(TEXT("clearSegmentMidpoints"),Clear);Row->SetNumberField(TEXT("blockedSegmentMidpoints"),Blocked);
            ActorRows.Add(MakeShared<FJsonValueObject>(Row));
        }
        if(!Visible)continue;
        const bool Action=C.ActionSequence&&C.bLocked&&Now>=C.StartSeconds&&Now<C.StartSeconds+C.Duration&&C.Phase!=uint8(AnimeMMORPG::U02::EPhase::Cancelled);
        const TCHAR* Phase=Now<C.StartSeconds+C.ActiveStart?TEXT("WINDUP >>>"):Now<C.StartSeconds+C.ActiveEnd?TEXT("!! STRIKE !!"):TEXT("... RECOVER");
        if(Action)DrawText(Phase,FLinearColor::White,Screen.X-40,Screen.Y);
        if(C.bGuard){DrawText(TEXT("|== GUARD ==|"),FLinearColor::White,Screen.X-45,Screen.Y+18);}
        if(C.HardCC&&Now<C.HardEnd)DrawText(C.HardCC==5?TEXT("/ / GUARD BREAK / /"):TEXT("[ HARD CC ]"),FLinearColor::White,Screen.X-45,Screen.Y+35);
        if(C.DodgeSequence&&Now>=C.DodgeStart&&Now<C.DodgeLockEnd)DrawText(Now<C.DodgeMotionEnd?TEXT("<< DODGE >>"):TEXT("DODGE RECOVER"),FLinearColor::White,Screen.X-45,Screen.Y+18);
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
        FVector2D Screen;const bool Visible=AnimeMMORPG::U03::PresentationVisible(PC,Target,Target->GetActorLocation()+FVector(0,0,150),Screen);
        if(Visible)
        {
            DrawText(Labels[FMath::Min<int32>(Kind,7)],FLinearColor::White,Screen.X-40,Screen.Y-20-(R.Serial%3)*18);
            if(Kind==2)for(int32 I=0;I<32;++I){const double A=2*PI*I/32,B=2*PI*(I+1)/32;DrawLine(Screen.X+40*FMath::Cos(A),Screen.Y+40*FMath::Sin(A),Screen.X+40*FMath::Cos(B),Screen.Y+40*FMath::Sin(B),FLinearColor::White,2);}
        }
        // Prime history silently on creation/reconnect. Old/late snapshots retain
        // visual lifetime only; one fresh sound at most per render sample.
        const bool Audio=AnimeMMORPG::U03::FreshFeedbackAudio(New,bFeedbackPrimed,Visible,R.Timestamp,Now);
        if(Probe)
        {
            auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("serial"),R.Serial);Row->SetStringField(TEXT("subject"),R.Target.ToString());
            Row->SetNumberField(TEXT("at"),R.Timestamp);Row->SetNumberField(TEXT("remaining"),AnimeMMORPG::U03::FeedbackRemaining(R.Timestamp,Now));
            Row->SetBoolField(TEXT("new"),New);Row->SetBoolField(TEXT("visible"),Visible);Row->SetBoolField(TEXT("audio"),Audio);Row->SetNumberField(TEXT("kind"),Kind);
            EventRows.Add(MakeShared<FJsonValueObject>(Row));
        }
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
        FeedbackTone->QueueAudio(reinterpret_cast<const uint8*>(PCM.GetData()),PCM.Num()*sizeof(int16));
        if(auto* Voice=UGameplayStatics::SpawnSound2D(this,FeedbackTone))FeedbackVoices.Add({Voice,Target,Source,R.SourceLife,R.TargetLife,R.EncounterId,R.EncounterRevision});
    }
    bFeedbackPrimed=true;
    if(Probe)
    {
        PresentationDiagnostics=MakeShared<FJsonObject>();PresentationDiagnostics->SetNumberField(TEXT("serverNow"),Now);
        PresentationDiagnostics->SetArrayField(TEXT("actors"),ActorRows);PresentationDiagnostics->SetArrayField(TEXT("events"),EventRows);
        PresentationDiagnostics->SetNumberField(TEXT("canvasTelegraphSegments"),0);
    }
}
TSharedRef<FJsonObject> AU03EncounterHUD::GetPresentationDiagnostics() const
{return PresentationDiagnostics.IsValid()?PresentationDiagnostics.ToSharedRef():MakeShared<FJsonObject>();}
