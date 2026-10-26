"""Geometric routing cleanup; electrical acceptance requires KiCad DRC afterwards."""
from pathlib import Path
import json,math,collections,copy
import numpy as np
R=Path(__file__).resolve().parents[1]
exec((R/'tools/route_adapter.py').read_text().split('by=collections')[0])
data=json.loads((R/'hardware/routed_copper.json').read_text());before=copy.deepcopy(data)
segments=data['segments'];vias=data['vias'];stats=collections.Counter()
def key(q):return tuple(round(float(x),5) for x in q)
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def near(q,s):
 a,b=s['a'],s['b'];dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
 t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den)) if den else 0
 return dist(q,[a[0]+t*dx,a[1]+t*dy])
def inpad(q,s):
 return any(p['net']==s['net'] and s['layer'] in p['layers'] and abs(q[0]-p['x'])<=p['w']/2+.001 and abs(q[1]-p['y'])<=p['h']/2+.001 for p in pads)
def anchor(q,s):
 return inpad(q,s) or any(v['net']==s['net'] and dist(q,[v['x'],v['y']])<=.3 for v in vias)
# Make nearly straight pad escapes exactly straight by moving only inside copper pads.
for s in segments:
 a,b=s['a'],s['b']
 for i,j in [(0,1),(1,0)]:
  if .00001<abs(a[i]-b[i])<.081 and abs(a[j]-b[j])>.15:
   for end,other in [(a,b),(b,a)]:
    q=end[:];q[i]=other[i]
    if inpad(end,s) and inpad(q,s):end[i]=q[i];stats['pad_escape_aligned']+=1;break
# Unify the old 0.04mm fanout/grid endpoint mismatch before building junctions.
canonical={}
for seg in segments:
 for side in ['a','b']:
  q=seg[side];group=canonical.setdefault((seg['net'],seg['layer']),[])
  via=next(([v['x'],v['y']] for v in vias if v['net']==seg['net'] and dist(q,[v['x'],v['y']])<.081),None)
  hit=via if via is not None else next((p for p in group if dist(q,p)<.081),None)
  if hit is not None:
   if dist(q,hit)>.0001:stats['near_endpoints_unified']+=1
   seg[side]=list(hit)
  else:group.append(list(q))
# Remove copper segments wholly hidden in one own pad.
keep=[]
for s in segments:
 if any(p['net']==s['net'] and s['layer'] in p['layers'] and all(abs(q[0]-p['x'])<=p['w']/2 and abs(q[1]-p['y'])<=p['h']/2 for q in [s['a'],s['b']]) for p in pads):stats['inside_pad_segments_removed']+=1
 else:keep.append(s)
segments=keep
def split_all():
 global segments
 new=[]
 for s in segments:
  a,b=s['a'],s['b'];dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
  if den<1e-10:continue
  cuts=[0.,1.]
  for t in segments:
   if t is s or t['net']!=s['net'] or t['layer']!=s['layer']:continue
   for q in [t['a'],t['b']]:
    u=((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den
    if 0<u<1 and dist(q,[a[0]+u*dx,a[1]+u*dy])<.0001:cuts.append(u)
   c,e=t['a'],t['b'];ux=e[0]-c[0];uy=e[1]-c[1];cross=dx*uy-dy*ux
   if abs(cross)>1e-8:
    u=((c[0]-a[0])*uy-(c[1]-a[1])*ux)/cross;v=((c[0]-a[0])*dy-(c[1]-a[1])*dx)/cross
    if 0<u<1 and 0<=v<=1:cuts.append(u)
  cuts=sorted(set(round(x,8) for x in cuts))
  for l,h in zip(cuts,cuts[1:]):
   p=[round(a[0]+l*dx,5),round(a[1]+l*dy,5)];q=[round(a[0]+h*dx,5),round(a[1]+h*dy,5)]
   if dist(p,q)>.0001:new.append(dict(s,a=p,b=q))
 seen=set();segments=[]
 for s in new:
  k=(s['net'],s['layer'],s['width'],*sorted([key(s['a']),key(s['b'])]))
  if k not in seen:segments.append(s);seen.add(k)
  else:stats['overlap_duplicates_removed']+=1
def graph():
 g=collections.defaultdict(list)
 for i,s in enumerate(segments):
  for q in [s['a'],s['b']]:g[(s['net'],s['layer'],key(q))].append(i)
 return g
split_all()
def prune():
 global segments
 while True:
  g=graph();remove=set()
  for (_,_,q),ids in g.items():
   if len(ids)!=1:continue
   i=ids[0];s=segments[i]
   if anchor(q,s):continue
   if any(j!=i and t['net']==s['net'] and t['layer']==s['layer'] and near(q,t)<(s['width']+t['width'])/2-.015 for j,t in enumerate(segments)):continue
   remove.add(i)
  if not remove:break
  stats['dangling_segments_removed']+=len(remove);segments=[s for i,s in enumerate(segments) if i not in remove]
prune()
def chains():
 g=graph();used=set();out=[]
 for i,s in enumerate(segments):
  for start in [s['a'],s['b']]:
   if i in used:break
   if len(g[(s['net'],s['layer'],key(start))])==2 and not anchor(start,s):continue
   ids=[];points=[list(start)];cur=i;q=start
   while cur not in used:
    used.add(cur);ids.append(cur);t=segments[cur];n=t['b'] if key(t['a'])==key(q) else t['a'];points.append(list(n))
    adjacent=g[(t['net'],t['layer'],key(n))]
    if len(adjacent)!=2 or anchor(n,t):break
    nxt=next(k for k in adjacent if k!=cur)
    if segments[nxt]['width']!=s['width']:break
    cur=nxt;q=n
   out.append((s,points,ids))
 for i,s in enumerate(segments):
  if i not in used:out.append((s,[s['a'],s['b']],[i]))
 return out
def options(a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;m=min(abs(dx),abs(dy))
 if abs(dx)<1e-5 or abs(dy)<1e-5 or abs(abs(dx)-abs(dy))<1e-5:return [[a,b]]
 if abs(dx)>abs(dy):return [[a,[b[0]-sx*m,a[1]],b],[a,[a[0]+sx*m,b[1]],b]]
 return [[a,[a[0],b[1]-sy*m],b],[a,[b[0],a[1]+sy*m],b]]
def clear(path,s,blocked):
 for a,b in zip(path,path[1:]):
  n=max(1,math.ceil(dist(a,b)/.04))
  for u in range(n+1):
   x=a[0]+(b[0]-a[0])*u/n;y=a[1]+(b[1]-a[1])*u/n;ix,iy=coord(x,y)
   if not (0<=ix<NX and 0<=iy<NY) or blocked[s['layer'],iy,ix]:return False
 return True
new=[]
for s,path,ids in chains():
 blocked=mask_for(s['net'],s['width']/2)
 i=0;result=[path[0]]
 while i<len(path)-1:
  chosen=None
  for j in range(len(path)-1,i+1,-1):
   old=sum(dist(a,b) for a,b in zip(path[i:j],path[i+1:j+1]))
   for cand in options(path[i],path[j]):
    if len(cand)>=j-i+1 and sum(dist(a,b) for a,b in zip(cand,cand[1:]))>=old-.01:continue
    if clear(cand,s,blocked):chosen=(j,cand);break
   if chosen:break
  if chosen:
   j,cand=chosen;result.extend(cand[1:]);stats['chains_shortened']+=1;i=j
  else:result.append(path[i+1]);i+=1
 # Chamfer remaining right-angle bends with a continuous diagonal.
 smooth=[result[0]]
 for i in range(1,len(result)-1):
  a,b,c=result[i-1:i+2];l1=dist(a,b);l2=dist(b,c)
  u=[(b[k]-a[k])/l1 for k in [0,1]];v=[(c[k]-b[k])/l2 for k in [0,1]]
  if abs(sum(u[k]*v[k] for k in [0,1]))<.001 and not anchor(b,s):
   cut=min(.45,l1*.4,l2*.4);p=[b[k]-u[k]*cut for k in [0,1]];q=[b[k]+v[k]*cut for k in [0,1]]
   if cut>.12 and clear([p,q],s,blocked):smooth.extend([p,q]);stats['right_angles_chamfered']+=1;continue
  smooth.append(b)
 smooth.append(result[-1])
 for a,b in zip(smooth,smooth[1:]):
  if dist(a,b)>.0001:new.append(dict(s,a=[round(v,5) for v in a],b=[round(v,5) for v in b]))
segments=new;split_all();prune()
# Merge straight, unbranched pieces after trimming.
merged=[]
for s,path,ids in chains():
 out=[path[0]]
 for i in range(1,len(path)-1):
  a,b,c=out[-1],path[i],path[i+1];cross=(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
  if abs(cross)<.00001:stats['collinear_nodes_removed']+=1
  else:out.append(b)
 out.append(path[-1]);merged.extend(dict(s,a=a,b=b) for a,b in zip(out,out[1:]))
segments=merged
# Remove the small non-45-degree miters left by the old fanout/grid mismatch.
for _ in range(4):
 changed=False
 for (_,_,b),ids in list(graph().items()):
  if len(ids)!=2:continue
  s,t=[segments[i] for i in ids]
  if s['width']!=t['width'] or anchor(b,s):continue
  a=s['b'] if key(s['a'])==b else s['a'];c=t['b'] if key(t['a'])==b else t['a']
  candidates=[p for p in options(a,c) if len(p)==3 and .0001<dist(p[1],b)<.15]
  for candidate in sorted(candidates,key=lambda p:dist(p[1],b)):
   if clear(candidate,s,mask_for(s['net'],s['width']/2)):
    for edge in [s,t]:
     for side in ['a','b']:
      if key(edge[side])==b:edge[side]=[round(v,5) for v in candidate[1]]
    stats['irregular_miters_aligned']+=1;changed=True;break
 if not changed:break
data['segments']=segments
length=lambda ss:round(sum(dist(s['a'],s['b']) for s in ss),3)
report=dict(before_segments=len(before['segments']),after_segments=len(segments),before_length_mm=length(before['segments']),after_length_mm=length(segments),vias=len(vias),actions=dict(stats),status='CANDIDATE; KICAD DRC REQUIRED')
(R/'tmp/routed_copper.json').write_text(json.dumps(data));(R/'tmp/routing_cleanup.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
