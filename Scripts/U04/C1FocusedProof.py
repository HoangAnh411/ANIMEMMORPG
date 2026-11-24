"""Focused C1 proof checks over original B-format and network evidence."""
import math

from AnalyzeR1 import VERSION, dodge_chain, vector
from AnalyzeR1a import repro


def dodge_preconditions(raw, case):
    expected = {'w-shift': ['W', 'LeftShift'], 'shift-w': ['LeftShift', 'W']}[case]
    edges = [r for r in raw if r['kind'] == 'PhysicalEdge' and not r.get('console')
             and r['key'] in expected][:2]
    if [r['key'] for r in edges] != expected or not all(r['down'] for r in edges):
        raise ValueError('ordered_edges_missing')
    if edges[0]['frame'] != edges[1]['frame']:
        raise ValueError('different_dispatch_frames')
    admissions = [r for r in raw if r['kind'] == 'AuthorityAdmission']
    if len(admissions) != 1:
        raise ValueError('admission_missing_or_ambiguous')
    velocity = vector(admissions[0]['velocityBeforeBatch'])
    if len(velocity) != 3 or not all(map(math.isfinite, velocity)) or math.hypot(*velocity[:2]) > .01:
        raise ValueError('nonstationary_admission')


def check_dodge(raw, case):
    if VERSION != 'u04r1-entry-4':
        raise ValueError('wrong_analyzer')
    dodge_preconditions(raw, case)
    result = repro(raw, case, 60)
    if case == 'w-shift':
        result['entryChain'] = dodge_chain(raw, [r for r in raw if r['kind'] == 'frame'], 'forward')
    return result


def replicated_damage(before, samples, owner, action):
    """Validate a separately witnessed authority action and exact replication."""
    if set(samples) != {'Server', 'ClientA', 'ClientB'} or any(row is None for row in samples.values()):
        raise ValueError('client_missing_during_action')
    target = owner['encounter']['monster']
    if action['source'] != owner['pawn'] or action['sourceLife'] != owner['life']:
        raise ValueError('wrong_action_owner')
    if action['action'] <= 0 or action['at'] <= before['time']:
        raise ValueError('stale_action')
    keys = ('source', 'sourceLife', 'action')
    prior = {row['serial'] for row in before['results']}
    def event(state):
        rows = [r for r in state['results'] if all(r[k] == action[k] for k in keys)]
        if len(rows) != 1:
            raise ValueError('damage_receipt_missing_or_ambiguous')
        row = rows[0]
        if row['serial'] in prior or row['timestamp'] < action['at']:
            raise ValueError('stale_damage')
        if row['target'] != target or row['encounter'] != owner['encounter']['id']:
            raise ValueError('damage_target_or_encounter')
        if row['damage'] <= 0:
            raise ValueError('nonpositive_damage')
        target_states = [p for p in state['pawns'] if p['id'] == target]
        if (len(target_states) != 1 or target_states[0]['life'] != row['targetLife']
                or target_states[0]['vital']['hp'] != row['hp']):
            raise ValueError('damage_hp_or_life_mismatch')
        return row
    authority = event(samples['Server'])
    if any(event(samples[role]) != authority for role in ('ClientA', 'ClientB')):
        raise ValueError('replication_diverged')
    return authority


def combo_receipt(summary, prepared, after, edges, bias, process):
    actions = [item for item in summary['actionEvents'] if item['kind'] == 'ActionStarted']
    hits = summary['damageEvents']
    target, = summary['targets']
    actor = prepared['combat']
    if after['combat']['pawnId'] != actor['pawnId'] or after['combat']['life'] != actor['life']:
        raise ValueError('combo_pawn_or_life_changed')
    if any(not (summary['startWall'] <= item['wall'] <= summary['endWall']
                and 0 <= item['wall']-stamp-bias <= .40) for item,stamp in zip(actions,edges)):
        raise ValueError('combo_event_outside_input_window')
    problems = []
    if ([item['raw'] for item in actions] != [60,70,90] or summary['actions'] != 3
            or len(hits) != 3 or summary['confirmedHits'] != 3):
        problems.append('action_or_hit_count')
    hp = 1000000
    for number,(action,hit,damage) in enumerate(zip(actions,hits,(60,70,90)),1):
        if (action['action'] != number or action['pawnId'] != actor['pawnId']
                or action['life'] != actor['life'] or action['pid'] != process['pid']
                or action['runId'] != process['runId'] or action['sourceSHA'] != process['sourceSHA']
                or action['world'] != summary['world'] or action['owner'] != prepared['controller']):
            problems.append('action_identity')
        if (hit['source'] != actor['pawnId'] or hit['sourceLife'] != actor['life']
                or hit['action'] != action['action'] or hit['target'] != target['subject']
                or hit['targetLife'] != target['life'] or hit['hurtboxId'] != 1):
            problems.append('hit_identity')
        if (hit['damage'] != damage or hit['beforeHP'] != hp or hit['afterHP'] != hp-damage
                or hit['crit'] or hit['death'] or hit['absorbed']):
            problems.append('damage_hp')
        hp -= damage
    if target['hp'] != 999780 or target['dead'] or target['stableHurtboxIds'] != [1]:
        problems.append('target_end_state')
    return dict(status='FAIL' if problems else 'PASS', problems=problems, actions=actions, damage=hits, target=target)
