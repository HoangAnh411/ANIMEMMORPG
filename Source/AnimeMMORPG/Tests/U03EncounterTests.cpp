#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "U03/U03ActionModel.h"
#include "U03/U03EncounterModel.h"
using namespace AnimeMMORPG;
using namespace AnimeMMORPG::U03;
namespace { constexpr auto C2Flags=EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter; }
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2MonsterAdmission,"AnimeMMORPG.U03.C2.MonsterAdmissionAndInterruptEdges",C2Flags)
bool FC2MonsterAdmission::RunTest(const FString&)
{
    const U02::FLifeId Life{FGuid(703,2,0,1),1};FAdmissionContext C;C.bMonster=true;C.bDefenseEnabled=C.bDodgeEnabled=true;
    for(double At:{0.,.599999,.60,.600001,.749999,.75,.750001,1.499999})
    {
        FTimelineModel M(Life);TArray<FActiveInterval> Out;
        auto R=M.SubmitBatchUnopposed({{1,Life,ECommand::Monster,0,45}},C,Out);
        TestEqual(TEXT("Monster uses common admission"),R[0].Result,EAdmission::Accepted);
        TestEqual(TEXT("definition identity"),M.Current()->GetDefinition().Id,EAction::Monster);
        TestEqual(TEXT("raw100"),M.Current()->GetDefinition().RawDamage,100);
        TestEqual(TEXT("duration1.50"),M.Current()->End(),1.50);
        TestEqual(TEXT("pure startup Interrupt"),M.CancelUnopposed(ECutoff::Interrupt,At,true,Out),At<.60);
        M.AdvanceUnopposed(2.,Out);
        TestEqual(TEXT("startup Interrupt suppresses all active"),Out.IsEmpty(),At<.60);
        for(const auto& I:Out){TestTrue(TEXT("active range"),I.Begin>=.60&&I.End<=.75);TestEqual(TEXT("raw remains captured"),I.RawDamage,100);}
    }
    for(auto Command:{ECommand::Attack,ECommand::Q,ECommand::E,ECommand::Dodge,ECommand::Guard,ECommand::Feint})
    {
        FTimelineModel M(Life);TArray<FActiveInterval> Out;
        TestEqual(TEXT("no player commands for monster"),M.SubmitBatchUnopposed({{1,Life,Command,0,0}},C,Out)[0].Result,EAdmission::Unsupported);
    }
    FTimelineModel P(Life);TArray<FActiveInterval> Out;
    TestEqual(TEXT("player context cannot admit Monster"),P.SubmitBatchUnopposed({{1,Life,ECommand::Monster,0,0}},{},Out)[0].Result,EAdmission::Unsupported);
    for(auto Reason:{ECutoff::Dodge,ECutoff::Guard,ECutoff::Feint})
    {FActionInstance A(EAction::Monster,{Life,1},0,0);TestFalse(TEXT("no replacement permissions leaked"),A.Cancel(Reason,.1));}
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2MonsterBoundaries,"AnimeMMORPG.U03.C2.MonsterDecisionBoundaries",C2Flags)
bool FC2MonsterBoundaries::RunTest(const FString&)
{
    for(double D:{-.000001,0.,.000001})
    {
        FMonsterObservation O;O.TargetDistance=200.+D;
        TestEqual(TEXT("attack inclusive200"),DecideMonster(EMonsterState::Chase,O).bAttack,D<=0);
        O.TargetDistance=1000.+D;
        TestEqual(TEXT("detect inclusive1000"),DecideMonster(EMonsterState::Idle,O).State,D<=0?EMonsterState::Chase:EMonsterState::Idle);
        TestEqual(TEXT("retain inclusive1000"),DecideMonster(EMonsterState::Action,O).State,D<=0?EMonsterState::Chase:EMonsterState::Return);
        O.TargetDistance=100;O.SpawnDistance=1500.+D;
        TestEqual(TEXT("leash strict1500"),DecideMonster(EMonsterState::Chase,O).bCancel,D>0);
        O.SpawnDistance=50.+D;
        TestEqual(TEXT("return inclusive50"),DecideMonster(EMonsterState::Return,O).bReset,D<=0);
    }
    FMonsterObservation O;O.TargetDistance=100;O.SpawnDistance=100;O.bLineOfSight=false;O.bAction=true;
    TestEqual(TEXT("LOS cancels action"),DecideMonster(EMonsterState::Action,O).State,EMonsterState::Return);
    O.bLineOfSight=true;
    TestEqual(TEXT("Return never rechases"),DecideMonster(EMonsterState::Return,O).State,EMonsterState::Return);
    O.bMonsterAlive=false;TestEqual(TEXT("death"),DecideMonster(EMonsterState::Return,O).State,EMonsterState::Defeated);
    O.bMonsterAlive=true;TestEqual(TEXT("no auto resurrection"),DecideMonster(EMonsterState::Defeated,O).State,EMonsterState::Defeated);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FC2RetryModel,"AnimeMMORPG.U03.C2.EncounterTerminalAndRetryAdmission",C2Flags)
bool FC2RetryModel::RunTest(const FString&)
{
    for(bool MonsterFirst:{false,true})
    {
        FEncounterModel M;
        TestFalse(TEXT("Running rejects Retry"),M.AdmitRetry(1,1,true));
        TestTrue(TEXT("first lethal decides"),M.Defeat(MonsterFirst));TestFalse(TEXT("later same-time lethal cannot create draw"),M.Defeat(!MonsterFirst));
        TestEqual(TEXT("inherited first lethal result"),M.Result,MonsterFirst?EEncounterResult::Won:EEncounterResult::Lost);
        TestFalse(TEXT("unowned"),M.AdmitRetry(1,2,false));TestFalse(TEXT("zero"),M.AdmitRetry(1,0,true));
        TestFalse(TEXT("duplicate"),M.AdmitRetry(1,1,true));TestFalse(TEXT("stale revision"),M.AdmitRetry(0,2,true));
        TestTrue(TEXT("fresh owned terminal"),M.AdmitRetry(1,3,true));M.CommitRetry();
        TestEqual(TEXT("revision"),M.Revision,uint64(2));TestEqual(TEXT("Running last"),M.Result,EEncounterResult::Running);
        TestTrue(TEXT("new lethal"),M.Defeat(true));TestFalse(TEXT("old duplicate"),M.AdmitRetry(2,3,true));
        M.bClosed=true;TestFalse(TEXT("disconnect ends ownership"),M.AdmitRetry(2,4,true));TestFalse(TEXT("closed lethal"),M.Defeat(false));
    }
    return true;
}
#endif
