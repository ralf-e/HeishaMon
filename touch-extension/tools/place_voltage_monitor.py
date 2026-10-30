"""Pack Rev07 on the unchanged outline, keeping the mating connectors fixed.

Uses native footprint courtyards and keepouts for opposite-side through holes.
This is only a placement search; KiCad DRC remains the independent check.
"""
from pathlib import Path
import json,math,random
import pcbnew as p
R=Path(__file__).resolve().parents[1];H=R/'hardware/Rev07'
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
meta=json.loads((H/'netlist_design.json').read_text())
comps=[c for c in meta['components'] if c['footprint']]
fixed={'J1','J2','J3','J4'}
def box(fp,layer):
 points=[]
 for g in fp.GraphicalItems():
  if g.GetLayer()!=layer or not isinstance(g,p.PCB_SHAPE):continue
  bb=g.GetBoundingBox()
  for pt in [bb.GetPosition(),bb.GetEnd()]:points.append((p.ToMM(pt.x),p.ToMM(pt.y)))
 if not points:
  for pad in fp.Pads():
   pt=pad.GetPosition();sz=pad.GetSize();x,y=p.ToMM(pt.x),p.ToMM(pt.y);w,h=p.ToMM(sz.x),p.ToMM(sz.y)
   points.extend([(x-w/2-.25,y-h/2-.25),(x+w/2+.25,y+h/2+.25)])
 return (min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points))
def overlaps(a,b):return a[0]<b[2]+.02 and a[2]>b[0]-.02 and a[1]<b[3]+.02 and a[3]>b[1]-.02
board=p.LoadBoard(str(H/'HeishaMon_V6_Touch_Adapter.kicad_pcb'))
obstacles=[]
for fp in board.GetFootprints():
 if fp.GetReference() not in fixed:continue
 if fp.GetReference()=='J4':obstacles.append(box(fp,p.F_CrtYd))
 else:
  for pad in fp.Pads():
   x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y);w,h=p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y)
   obstacles.append((x-w/2-.25,y-h/2-.25,x+w/2+.25,y+h/2+.25))
geometries={}
for c in comps:
 if c['ref'] in fixed:continue
 lib,name=c['footprint'].split(':');fp=p.FootprintLoad(str(LIB/(lib+'.pretty')),name)
 geometries[c['ref']]={}
 for rot in [0,90]:
  fp.SetOrientationDegrees(rot);geometries[c['ref']][rot]=box(fp,p.F_CrtYd)

movable=[c for c in comps if c['ref'] not in fixed]
def area(c):
 b=geometries[c['ref']][0];return (b[2]-b[0])*(b[3]-b[1])
priority={'U1':0,'U3':1,'U2':2,'U4':3,'C1':4,'C4':5,'C5':6,'C6':7,'C2':8,'C3':9}
movable.sort(key=lambda c:(priority.get(c['ref'],10),-area(c)))
random.seed(7)
best=None
for attempt in range(15):
 placed=[];result={};failed=[]
 order=movable[:]
 if attempt:
  head=order[:4];tail=order[4:];random.shuffle(tail);order=head+tail
 for c in order:
  target={'C4':(114.3,112.4),'C5':(114.5,119.2),'C6':(118,120.5)}.get(c['ref'],c['boardat']);candidates=[]
  for rot,b in geometries[c['ref']].items():
   for ix in range(48):
    x=99.2+ix*.45
    for iy in range(89):
     y=95.6+iy*.45
     a=(x+b[0],y+b[1],x+b[2],y+b[3])
     if a[0]<98.9 or a[2]>121.42 or a[1]<95.25 or a[3]>135.75:continue
     if a[0]<99.6 and a[3]>113.85 and a[1]<133.75:continue
     if any(overlaps(a,o) for o in obstacles) or any(overlaps(a,o) for o in placed):continue
     score=(x-target[0])**2+(y-target[1])**2+(.1 if rot!=c['rot'] else 0)
     candidates.append((score,x,y,rot,a))
  if not candidates:failed.append(c['ref']);continue
  score,x,y,rot,a=min(candidates);placed.append(a);result[c['ref']]={'xy':[round(x,3),round(y,3)],'rotation':rot}
 print('attempt',attempt,'placed',len(result),'missing',failed,flush=True)
 if not failed:best=result;break
if best is None:raise SystemExit('No complete placement; no placement file written')
(H/'component_placement.json').write_text(json.dumps(best,indent=2)+'\n')
