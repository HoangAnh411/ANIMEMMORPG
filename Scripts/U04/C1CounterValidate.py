"""Fail-closed, single-action checks of the actual Build-03 export schema.

PASS covers exported assertions. Reopen, concurrent-world isolation and individual
occlusion/suppression observations remain explicitly unproven dynamically.
"""
import csv
import json
import math
import re
from pathlib import Path
from C1Run import NATIVE, PROFILE, arguments, read, sha
from C1Identity import IdentityError, path_key
from C1Counter import prepare_transition


def same_windows_path(left, right):
    try:
        return path_key(left)==path_key(right)
    except IdentityError:
        return False

COUNTERS = dict(visits='hurtboxVisits', geometry='geometryTests', occlusion='occlusionCalls',
                candidates='candidates', confirmed='confirmedHits', suppressed='duplicateSuppression',
                intervals='collectIntervals', actions='actions')
LIMITS = ['reopen rejection: source only; no Closed/reopen export',
          'two concurrent UWorld isolation: source only; no dynamic experiment',
          'occlusion origin and individual suppression observations: aggregate only',
          'initial target HP and registration identities: prepare/source plus final export, no initial target snapshot']


def reconcile(s, w, record, prepared, after, rows):
    invalid, failures = [], []
    def require(ok, name):
        if not ok: invalid.append(name)
    def check(ok, name):
        if not ok: failures.append(name)
    try:
        n, h, inside = w['subjects'], w['boxes'], w['placement'] == 'in'
        require(n in (1,10,40) and h in (1,3) and w['placement'] in ('in','out'), 'workload')
        require(s['pid'] == record['pid'] and s['world'] == prepared['world'] == after['world'], 'summary_pid_world')
        require((s['subjects'],s['hurtboxesPerSubject'],s['inside']) == (n,h,inside), 'summary_workload')
        require(s['requestedSeconds'] == 5 and all(math.isfinite(s[k]) for k in ('startWall','endWall')) and s['endWall'] >= s['startWall']+5, 'window_duration')
        require(s['fixedTimeStep'] is False and s['fixedFrameRate'] is False and s['smoothing'] is False and s['dilation']==1, 'time_profile')
        cv = {part.rsplit(' ',1)[0]:float(part.rsplit(' ',1)[1]) for part in PROFILE.split(',')}
        require(s['cvars']==cv and (s['width'],s['height'])==(1280,720), 'profile_B')
        require(bool(rows), 'frames_empty')
        for row in rows:
            require(int(row['focus'])==1, 'frame_focus')
            require(s['startWall'] <= float(row['wall']) <= s['endWall'], 'frame_wall_outside_window')
            require(prepared['worldSeconds'] <= float(row['world']) <= after['worldSeconds'], 'frame_world_outside_fresh_metrics')
            require(math.isfinite(float(row['dt'])) and float(row['dt'])>0, 'frame_dt')
            for k in COUNTERS:
                require(float(row[k]).is_integer() and int(row[k])>=0, 'frame_counter_type:'+k)
        for a,b in zip(rows,rows[1:]):
            require(int(b['frame'])==int(a['frame'])+1, 'frame_gap')
            require(float(b['wall'])>float(a['wall']) and float(b['world'])>float(a['world']), 'frame_time_not_increasing')
            for k in COUNTERS:
                require(int(b[k])>=int(a[k]), 'frame_counter_decreased:'+k)
        if rows:
            require(float(rows[0]['wall'])-s['startWall']<=float(rows[0]['dt'])+.02 and s['endWall']-float(rows[-1]['wall'])<=float(rows[-1]['dt'])+.02, 'frames_do_not_cover_window')
        for k,exported in COUNTERS.items():
            require(type(s[exported]) in (int,float) and math.isfinite(s[exported]) and s[exported]>=0 and int(s[exported])==s[exported], 'counter_type:'+exported)
            if rows: check(int(rows[-1][k])==s[exported], 'last_frame_summary:'+exported)
        reg = dict(registeredSubjects=n+1, registeredHurtboxes=n*h+2)
        check(s['registrationBegin']==s['registrationEnd']==reg, 'registration_including_two_attacker_hurtboxes')
        # Conditional on stable, settled fixture/source/registration; no invented
        # interval count and no assumption that a call count equals target count.
        check(s['collectIntervals']>0, 'no_collect_interval')
        check(s['hurtboxVisits']==s['collectIntervals']*(n*h+2), 'hurtbox_visits_formula')
        check(s['geometryTests']==s['collectIntervals']*n*h, 'eligible_geometry_formula')
        check(s['queriesPostContactDelta']==(s['geometryTests'] if inside else 0), 'post_contact_queries_formula')
        check(0<=s['confirmedHits']<=s['candidates']<=s['queriesPostContactDelta']<=s['geometryTests']<=s['hurtboxVisits'], 'counter_order')
        check(s['occlusionCalls']>=s['candidates'], 'occlusion_below_candidates')
        starts = [e for e in s['actionEvents'] if e['kind']=='ActionStarted']
        check(len(starts)==1 and s['actions']==1, 'exactly_one_action')
        for e in s['actionEvents']:
            require(e['pid']==record['pid'] and e['world']==s['world'] and e['runId']==record['runId'] and e['sourceSHA']==NATIVE, 'event_origin')
            require(e['worldType']==1 and e['netMode']==0 and e['localRole']==3 and e['pawn']==prepared['pawn'] and e['owner']==prepared['controller'], 'event_world_pawn_controller_authority')
            require(s['startWall']<=e['wall']<=s['endWall'], 'event_wall_outside_window')
            require(prepared['worldSeconds']<=e['observedSeconds']<=after['worldSeconds'], 'event_stale_world_time')
        if len(starts)!=1:
            return dict(status='INVALID' if invalid else 'FAIL',invalid=invalid,failures=failures,evidenceLimits=LIMITS)
        action=starts[0]; combat=prepared['combat']
        check(action['definition']==0 and action['raw']==60 and action['definitionVersion']==1, 'attack1_raw60')
        require(action['pawnId']==combat['pawnId'] and action['life']==combat['life'], 'attacker_life')
        require(after['combat']['pawnId']==combat['pawnId'] and after['combat']['life']==combat['life'], 'after_attacker_life')
        check(action['action']==combat['action']+1, 'new_action_sequence')
        check(after['combat']['action']==action['action'], 'after_action_sequence')
        require(action['actionId']==f"{action['pawnId']}:{action['life']}:{action['action']}" and action['lifeId']==f"{action['pawnId']}:{action['life']}", 'action_identity_encoding')
        require(action['start']==action['gameplaySeconds'] and prepared['worldSeconds']<=action['start']<=action['observedSeconds'], 'action_gameplay_window')
        require(action['start']<=action['activeStart']<=action['activeEnd']<=action['end'], 'action_active_bounds')
        if rows:
            require(action['gameplaySeconds']>=float(rows[0]['world'])-float(rows[0]['dt']), 'action_before_capture_frame')
            require(action['gameplaySeconds']<=float(rows[-1]['world']), 'action_after_capture_frame')
        targets={t['subject']:t for t in s['targets']}
        require(len(targets)==len(s['targets'])==n and action['pawnId'] not in targets, 'target_identity_set')
        events=s['damageEvents']
        check(len(events)==(n if inside else 0), 'damage_event_count')
        check(s['confirmedHits']==len(events), 'confirmed_vs_product_damage')
        check(after['combat']['damageResults']-combat['damageResults']==len(events), 'fresh_product_damage_results_delta')
        check(after['combat']['geometryQueries']-combat['geometryQueries']==s['queriesPostContactDelta'], 'fresh_product_post_contact_query_delta')
        for e in events:
            check((e['source'],e['sourceLife'],e['action'])==(action['pawnId'],action['life'],action['action']), 'damage_wrong_action_or_attacker_life')
            require(e['target'] in targets, 'damage_unknown_target')
            if e['target'] not in targets: continue
            t=targets[e['target']]
            check(e['targetLife']==t['life'] and e['hurtboxId'] in t['stableHurtboxIds'], 'damage_target_life_or_hurtbox')
            check(action['activeStart']<=e['at']<=action['activeEnd'], 'damage_outside_action_active_interval')
            check(e['damage']==60 and e['beforeHP']==1000000 and e['afterHP']==999940, 'damage_independent_60_HP')
            check(e['crit'] is False and e['death'] is False and e['absorbed']==0, 'crit_death_absorption')
        hp=[]
        for t in targets.values():
            check(sorted(t['stableHurtboxIds'])==([1] if h==1 else [1,2,3]), 'stable_hurtbox_ids')
            per_target=[e for e in events if e['target']==t['subject']]
            check(len(per_target)==(1 if inside else 0), 'per_target_single_damage')
            expected_hp=999940 if inside else 1000000
            check(t['hp']==expected_hp and t['maxHP']==1000000 and t['shield']==0 and t['dead'] is False and t['deathCount']==0 and t['lifeGeneration']==t['life'], 'target_final_HP_life')
            hp.append(dict(subject=t['subject'],life=t['life'],expected=expected_hp,actual=t['hp'],reconstructed=1000000-sum(e['damage'] for e in per_target)))
        return dict(status='INVALID' if invalid else 'FAIL' if failures else 'PASS',invalid=invalid,failures=failures,
                    evidenceLimits=LIMITS,pid=s['pid'],world=s['world'],actionIdentity=action['actionId'],workload=w,
                    productHits=len(events),hp=hp,counters={k:s[k] for k in COUNTERS.values()},queriesPostContactDelta=s['queriesPostContactDelta'],
                    candidateConfirmedRatio=s['candidates']/s['confirmedHits'] if s['confirmedHits'] else None)
    except (KeyError,TypeError,ValueError,OverflowError) as e:
        return dict(status='INVALID',invalid=invalid+['missing_or_malformed_link:'+str(e)],failures=failures,evidenceLimits=LIMITS)


def validate(run, single=False, require_stop=True):
    if not single: return dict(status='INVALID',invalid=['single-action CC diagnostics only'])
    try:
        receipt=read(run/'capture.json'); record=read(run/'process.json'); cmd=read(run/'command.json')
        def must(ok, reason):
            if not ok: raise ValueError(reason)
        must(receipt['process']==record and receipt['workload']==cmd['workload'], 'receipt_process_command')
        must(record['runId']==run.name and type(record['creationTicks']) is int and record['creationTicks']>0, 'run_creation_pin')
        must(record['sourceSHA']==NATIVE and record['arguments']==cmd['arguments']==arguments(Path(record['executable']),run,run.name), 'exact_command')
        must(cmd['purpose']=='counter-correctness' and cmd['trace']=='off' and cmd['actions']==1, 'command_scope')
        for name,digest in receipt['files'].items():
            must(name in ('summary.json','frames.csv') and sha(run/'Raw'/name)==digest, 'raw_file_hash')
        must(set(receipt['files'])=={'summary.json','frames.csv'} and receipt['outputWasEmpty'] is True, 'raw_file_set')
        journal=[json.loads(line) for line in (run/'journal.jsonl').read_text(encoding='utf-8').splitlines()]
        must([r['seq'] for r in journal]==list(range(1,len(journal)+1)), 'journal_sequence')
        must(not any(r['event']=='guard_failed' for r in journal), 'guard_failed')
        launch=[r['identity'] for r in journal if r['event']=='launch_identity_verified']
        must(len(launch)==1 and all(launch[0][k]==record[k] for k in ('pid','creationTicks','executable')) and launch[0]['argv']==record['arguments'], 'launch_identity_proof')
        for handle in ('originalHandle','queryHandle'):
            must(all(launch[0][handle][k]==record[k] for k in ('pid','creationTicks','executable')), 'handle_identity_proof')
        guarded=[r for r in journal if r['event']=='before_gameplay_lmb']
        must(len(guarded)==2 and all(r['actualPID']==record['pid'] and r['actualCreationTicks']==record['creationTicks'] and r['foregroundHWND']==r['targetHWND'] and r['foregroundPID']==record['pid'] for r in guarded), 'gameplay_edge_identity')
        edges=[r for r in journal if r['event']=='input_sent' and r.get('purpose')=='counter-action']
        must([r['down'] for r in edges]==[True,False] and edges[1]['monotonic']-edges[0]['monotonic']>=.035-1e-9, 'one_LMB_pair')
        texts=[r['command'] for r in journal if r['event']=='counter_command_sent']; w=cmd['workload']
        must(texts==[f"u04c1 prepare {w['subjects']} {w['boxes']} {w['placement']}",'u04c1 begin 5'], 'console_command_sequence')
        sent=[r for r in journal if r['event']=='counter_command_sent']
        begin_start=[r for r in journal if r['event']=='counter_command_start' and r['command']=='u04c1 begin 5']
        must(len(begin_start)==1 and begin_start[0]['monotonic']-sent[0]['monotonic']>=2 and sent[1]['seq']<edges[0]['seq'], 'prepare_settle_begin_input_order')
        must(any(r['event']=='counter_empty_output_before_begin' for r in journal), 'empty_output_journal')
        log=Path(record['log']).read_bytes()
        must(0<=receipt['inputOffset']<receipt['inputEndOffset']<=len(log), 'action_input_log_offsets')
        physical=log[receipt['inputOffset']:receipt['inputEndOffset']]
        must(re.findall(rb'PhysicalPress key=LeftMouseButton state=(\d+) accepted=(\d+)',physical)==[(b'0',b'1')] and physical.count(b'PhysicalRelease/Rearm key=LeftMouseButton')==1, 'current_physical_LMB_edges')
        for key in ('before','prepared','after'):
            sample=receipt[key]; m=sample['metrics']
            must(sample['requestOffset']<=sample['lineOffset']<sample['endOffset']<=len(log), 'fresh_metrics_offset')
            line=log[sample['lineOffset']:sample['endOffset']]
            must(line.endswith(b'\n') and json.loads(line.split(b'Metrics ',1)[1])==m, 'fresh_metrics_raw')
            must(m['pid']==record['pid'] and m['worldType']==1 and m['netMode']==0 and m['sourceSHA']==NATIVE and m['controlState']==0 and m['windowActive'] is True, 'metrics_identity_profile')
            must(m['locallyControlled'] is True and m['localPlayers']==1 and m['owner']==m['controller'], 'metrics_local_ownership')
            must(all(m[k]==receipt['prepared']['metrics'][k] for k in ('runID','world','worldContext','pawn','controller')), 'metrics_session')
        must(receipt['before']['endOffset']<=receipt['prepared']['requestOffset'] and receipt['prepared']['endOffset']<=receipt['after']['requestOffset'], 'metrics_request_order')
        transition = prepare_transition(receipt['before'], receipt['prepared'])
        must(receipt['prepareTransition'] == transition, 'prepare_transition_receipt')
        must(receipt['after']['metrics']['worldSeconds']>receipt['prepared']['metrics']['worldSeconds'], 'metrics_world_progress')
        with (run/'Raw/frames.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
        result=reconcile(read(run/'Raw/summary.json'),w,record,receipt['prepared']['metrics'],receipt['after']['metrics'],rows)
        if require_stop:
            stopped=read(run/'result.json'); final=read(run/'final.json')
            must(stopped.get('processExited') is True and final.get('processExited') is True, 'exit_proof:processExited')
            proof=final.get('exitEvidence'); stopped_proof=stopped.get('exitEvidence')
            must(isinstance(proof,dict) and isinstance(stopped_proof,dict), 'exit_proof:missing')
            for field in sorted(set(proof)|set(stopped_proof)):
                must(field in proof and field in stopped_proof and type(proof[field]) is type(stopped_proof[field]) and proof[field]==stopped_proof[field], 'result_final_exit_proof:'+field)
            must(proof['identityVerifiedAtStop'] is True and proof['handleSource']=='original_Popen' and proof['wait']=='signaled', 'stop_identity_marker')
            for field in ('pid','creationTicks'):
                must(type(proof.get(field)) is int and proof[field]==record[field], 'exit_identity:'+field)
            must(same_windows_path(proof.get('executable'),record['executable']), 'exit_identity:executable')
            exits=[r for r in journal if r['event']=='original_handle_process_exited']
            must(len(exits)==1, 'journal_exit_record_count:'+str(len(exits)))
            journal_proof=exits[0].get('evidence')
            must(isinstance(journal_proof,dict), 'journal_exit_proof:missing')
            for field in sorted(set(proof)|set(journal_proof)):
                must(field in proof and field in journal_proof, 'journal_exit_proof:missing:'+field)
                if field=='executable':
                    must(same_windows_path(journal_proof[field],proof[field]), 'journal_exit_proof:'+field)
                else:
                    must(type(journal_proof[field]) is type(proof[field]) and journal_proof[field]==proof[field], 'journal_exit_proof:'+field)
            must(stopped['status']==final['status']==result['status'], 'final_verdict_mismatch')
        return result
    except (OSError,KeyError,ValueError,TypeError,IndexError) as e:
        return dict(status='INVALID',invalid=['evidence:'+str(e)],evidenceLimits=LIMITS)
