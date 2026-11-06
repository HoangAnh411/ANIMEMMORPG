"""Independent slab oracle for review action66 and exact wall contact."""
import json,math,argparse,hashlib,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--review',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
raw=a.review.read_bytes();lines=raw.decode('utf-8-sig',errors='replace').splitlines();selected=[l for l in lines if 'action=66 ' in l and ('U02D_QUERY' in l or 'U02D_CONFIRMED' in l)]
assert selected and any('hurtbox=1 damage=NOT_IMPLEMENTED' in l for l in selected)
walls=[((65,-9140,0),(85,-8980,220)),((65,-9140,0),(155,-9120,220))]
def slab(o,e,lo,hi):
 enter,leave=0.,1.
 for i in range(3):
  v=e[i]-o[i]
  if v==0:
   if o[i]<lo[i] or o[i]>hi[i]:return None
  else:
   x,y=sorted(((lo[i]-o[i])/v,(hi[i]-o[i])/v));enter=max(enter,x);leave=min(leave,y)
   if enter>leave:return None
 return [enter,leave]
rows=[]
for name,x,expected in [('Action66Open',162.889,False),('AllBlocked',120,True)]:
 o=(x,-9181.335,92.15)
 for hurt,z,r in [(1,70,35),(2,145,20)]:
  c=(150,-9000,z);d=math.dist(o,c);end=tuple(c[i]+(o[i]-c[i])*r/d for i in range(3));hits=[slab(o,end,*wall) for wall in walls]
  assert any(h is not None for h in hits)==expected
  crosses={str(y):o[0]+(end[0]-o[0])*((y-o[1])/(end[1]-o[1])) for y in (-9140,-9120)}
  rows.append(dict(case=name,origin=o,center=c,radius=r,nearest=end,wallIntervals=hits,xAtHorizontalWallFaces=crosses,blocked=expected))
for lo,hi in walls:
 assert slab((lo[0],lo[1]-10,lo[2]),(lo[0],lo[1]+10,lo[2]),lo,hi) is not None
mid=(sum(v[0] for v in walls[1])/2,-9130,110)
record=dict(method='independent segment/AABB slab clipping, closed spatial bounds; no game visibility/triangle call',originalAction=66,notClaimedToBeScreenshotAction=True,reviewLog=str(a.review),reviewLogSHA256=hashlib.sha256(raw).hexdigest(),walls=[dict(min=lo,max=hi) for lo,hi in walls],cases=rows,faceEdgeTangent='BLOCKED')
(a.out/'INDEPENDENT.json').write_text(json.dumps(record,indent=2));(a.out/'ORIGINAL-ACTION66.log').write_text('\n'.join(selected))
print('Independent action66/open, moved-blocked, face/edge cases passed')
