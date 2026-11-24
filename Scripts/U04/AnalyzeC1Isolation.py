"""Reconstruct sphere/attack overlap independently at the recorded LOS sample."""
import math


def point(a, b, t):
    return [x+(y-x)*t for x,y in zip(a,b)]


def opportunity(row):
    if not row['continuous'] or row['unsupported']:
        raise ValueError('unresolved geometry or obstruction')
    if not all(len(row[key])==3 and all(map(math.isfinite,row[key]))
               for key in ('feet0','feet1','center0','center1','origin','nearest','half')):
        raise ValueError('missing pose')
    alpha=row['alpha']
    if alpha<0:
        return 'OUTSIDE'
    if alpha>1 or not row['sliceBegin']<=row['begin']<=row['end']<=row['sliceEnd']:
        raise ValueError('invalid slice')
    at=row['begin']+(row['end']-row['begin'])*alpha
    if abs(at-row['losTime'])>1e-7 or row['exclusive'] and at>=row['sliceEnd']:
        raise ValueError('LOS outside slice')
    feet=point(row['feet0'],row['feet1'],alpha)
    center=point(row['center0'],row['center1'],alpha)
    origin=[feet[0],feet[1],feet[2]+90]
    dx,dy,dz=[a-b for a,b in zip(center,origin)]
    angle=math.radians(row['yaw'])
    c,s=math.cos(angle),math.sin(angle)
    local=[c*dx+s*dy-100,-s*dx+c*dy,dz]
    squared=sum(max(0,abs(v)-h)**2 for v,h in zip(local,row['half']))
    if squared>row['radius']**2+1e-5:
        raise ValueError('claimed contact fails independent overlap')
    d=math.dist(origin,center)
    nearest=point(center,origin,min(1,row['radius']/d)) if d else origin
    if math.dist(origin,row['origin'])>1e-5 or math.dist(nearest,row['nearest'])>1e-5:
        raise ValueError('LOS endpoints mismatch')
    return 'VISIBLE' if row['visible'] else 'BLOCKED'


def evaluate(rows, identity, before, after, receipts, coverage, replicated):
    """Inputs must come from pinned authority samples and verified replication."""
    try:
        if not coverage or not replicated:
            return 'INVALID', 'receipt coverage or replication missing'
        action_keys=('run','world','source','sourceLife','action','definition','version','sourceEncounter')
        selected=[r for r in rows if all(r[k]==identity[k] for k in action_keys)]
        by_role={}
        for role in ('A','B'):
            target=identity[role]
            matched=[r for r in selected if all(r[k]==target[k] for k in ('target','targetLife','targetEncounter'))]
            if not matched:
                return 'INVALID','target observation missing: '+role
            by_role[role]=[(r,opportunity(r)) for r in matched]
        if identity['B']['targetEncounter']!=identity['sourceEncounter'] or identity['A']['targetEncounter']==identity['sourceEncounter']:
            return 'INVALID','encounter relationship'
        slice_key=lambda r: tuple(r[k] for k in ('previous','now','sliceBegin','sliceEnd'))
        a={slice_key(r) for r,state in by_role['A'] if state=='VISIBLE'}
        b={slice_key(r) for r,state in by_role['B'] if state=='VISIBLE'}
        if not a or not b:
            return 'CONDITION_NOT_MET','A/B has no visible contact'
        if not a&b:
            return 'INVALID','visible observations do not share a slice'
        hits={role:[h for h in receipts if all(h[k]==identity[k] for k in ('source','sourceLife','action'))
                         and h['target']==identity[role]['target'] and h['targetLife']==identity[role]['targetLife']]
              for role in ('A','B')}
        if hits['A']:
            return 'FAIL','cross-encounter damage receipt'
        if len(hits['B'])!=1 or hits['B'][0]['damage']<=0:
            return 'CONDITION_NOT_MET','positive control missing'
        if (before['B']-hits['B'][0]['damage']!=after['B'] or hits['B'][0]['hp']!=after['B']
                or before['A']!=after['A']):
            return 'INVALID','HP does not reconcile'
        return 'PASS','same attack, opportunity on both, damage only on B'
    except (KeyError,TypeError,ValueError) as exc:
        return 'INVALID',str(exc)
