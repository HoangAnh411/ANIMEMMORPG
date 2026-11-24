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
