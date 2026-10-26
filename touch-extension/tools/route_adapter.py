"""Reproducible two-layer grid routing draft. KiCad DRC is authoritative.
Input: pcb_io.py export. Output: routed_copper.json for pcb_io.py import.
"""
from pathlib import Path
import json,heapq,math,time,collections
import numpy as np
R=Path(__file__).resolve().parents[1];pads=json.loads((R/'tmp/pcb_geometry.json').read_text())
STEP=.1;X0=98.66;Y0=95;NX=231;NY=411;N=NX*NY;CLEAR=.23
segments=[];vias=[];paths=[]
def coord(x,y):return round((x-X0)/STEP),round((y-Y0)/STEP)
def point(x,y):return [round(X0+x*STEP,3),round(Y0+y*STEP,3)]
def rect(mask,x,y,w,h,r,layers):
 ix0=max(0,int((x-w/2-r-X0)/STEP)-1);ix1=min(NX,math.ceil((x+w/2+r-X0)/STEP)+2)
 iy0=max(0,int((y-h/2-r-Y0)/STEP)-1);iy1=min(NY,math.ceil((y+h/2+r-Y0)/STEP)+2)
 xx=np.maximum(np.abs(X0+np.arange(ix0,ix1)*STEP-x)-w/2,0)
 yy=np.maximum(np.abs(Y0+np.arange(iy0,iy1)*STEP-y)-h/2,0)
 hit=yy[:,None]**2+xx[None,:]**2<=r*r+1e-10
 for l in layers:mask[l,iy0:iy1,ix0:ix1]|=hit

def line(mask,a,b,r,layers):
 x,y=a;u,v=b
 ix0=max(0,int((min(x,u)-r-X0)/STEP)-1);ix1=min(NX,math.ceil((max(x,u)+r-X0)/STEP)+2)
 iy0=max(0,int((min(y,v)-r-Y0)/STEP)-1);iy1=min(NY,math.ceil((max(y,v)+r-Y0)/STEP)+2)
 xx=X0+np.arange(ix0,ix1)[None,:]*STEP;yy=Y0+np.arange(iy0,iy1)[:,None]*STEP
 den=(u-x)**2+(v-y)**2
 t=np.clip(((xx-x)*(u-x)+(yy-y)*(v-y))/den,0,1) if den else 0
 hit=(xx-x-t*(u-x))**2+(yy-y-t*(v-y))**2<=r*r+1e-10
 for l in layers:mask[l,iy0:iy1,ix0:ix1]|=hit

def mask_for(net,r,allpads=False):
 m=np.zeros((2,NY,NX),dtype=bool)
 # Copper-to-edge clearance: >=0.35mm, in addition to track radius.
 margin=.35+r
 for y in range(NY):
  if Y0+y*STEP<Y0+margin or Y0+y*STEP>136-margin:m[:,y,:]=True
 for x in range(NX):
  if X0+x*STEP<X0+margin or X0+x*STEP>121.66-margin:m[:,:,x]=True
 # GH mating-face recess: no routing copper in the removed edge strip.
 for yy in range(NY):
  if 114.1-r<=Y0+yy*STEP<=133.5+r:
   m[:,yy,X0+np.arange(NX)*STEP<99.35+margin]=True
 for pad in pads:
  if pad['net']!=net or allpads:rect(m,pad['x'],pad['y'],pad['w'],pad['h'],r+CLEAR,pad['layers'])
 for s in segments:
  if s['net']!=net:line(m,s['a'],s['b'],s['width']/2+r+CLEAR,[s['layer']])
 for v in vias:
  if v['net']!=net:rect(m,v['x'],v['y'],0,0,.3+r+CLEAR,[0,1])
 return m
moves=[(1,0,1000),(-1,0,1000),(0,1,1000),(0,-1,1000),(1,1,1414),(1,-1,1414),(-1,1,1414),(-1,-1,1414)]
def findpath(start,target,net,width):
 blocked=mask_for(net,width/2);vb=mask_for(net,.3,True);via_ok=~(vb[0]|vb[1]);flat=blocked.reshape(-1)
 for oldvia in vias:
  vx,vy=coord(oldvia['x'],oldvia['y'])
  for oy in range(max(0,vy-7),min(NY,vy+8)):
   for ox in range(max(0,vx-7),min(NX,vx+8)):
    if (ox-vx)**2+(oy-vy)**2<49:via_ok[oy,ox]=False
 sx,sy=coord(start['x'],start['y']);tx,ty=coord(target['x'],target['y']);tl=target['layers']
 def heur(x,y,l):
  dx=abs(x-tx);dy=abs(y-ty)
  return max(dx,dy)*1000+min(dx,dy)*414+(18000 if l not in tl else 0)
 heap=[];gs={};parent={}
 for l in start['layers']:
  z=l*N+sy*NX+sx
  if flat[z]:continue
  gs[z]=0;heapq.heappush(heap,(heur(sx,sy,l),0,z))
 count=0
 while heap:
  _,g,z=heapq.heappop(heap)
  if g!=gs.get(z):continue
  l,rem=divmod(z,N);y,x=divmod(rem,NX)
  if x==tx and y==ty and l in tl:
   out=[(x,y,l)]
   while z in parent:
    z=parent[z];ll,rr=divmod(z,N);yy,xx=divmod(rr,NX);out.append((xx,yy,ll))
   return out[::-1],count
  count+=1
  for dx,dy,cost in moves:
   xx=x+dx;yy=y+dy
   if not (0<=xx<NX and 0<=yy<NY):continue
   zz=l*N+yy*NX+xx
   if flat[zz]:continue
   # Avoid cutting blocked corners at diagonal steps.
   if dx and dy and (blocked[l,y,xx] or blocked[l,yy,x]):continue
   ng=g+cost+(cost//6 if l else 0)
   if ng<gs.get(zz,10**18):gs[zz]=ng;parent[zz]=z;heapq.heappush(heap,(ng+heur(xx,yy,l),ng,zz))
  if via_ok[y,x]:
   zz=(1-l)*N+y*NX+x;ng=g+18000
   if not flat[zz] and ng<gs.get(zz,10**18):gs[zz]=ng;parent[zz]=z;heapq.heappush(heap,(ng+heur(x,y,1-l),ng,zz))
 return None,count

def store_path(path,net,width):
 a=path[0];prev=a;direction=None
 for cur in path[1:]:
  if cur[2]!=prev[2]:
   if a!=prev:segments.append(dict(a=point(*a[:2]),b=point(*prev[:2]),layer=prev[2],net=net,width=width))
   x,y=point(*cur[:2]);vias.append(dict(x=x,y=y,net=net));a=cur;direction=None
  else:
   d=(cur[0]-prev[0],cur[1]-prev[1])
   if direction is not None and direction!=d:
    segments.append(dict(a=point(*a[:2]),b=point(*prev[:2]),layer=prev[2],net=net,width=width));a=prev
   direction=d
  prev=cur
 if a!=prev:segments.append(dict(a=point(*a[:2]),b=point(*prev[:2]),layer=prev[2],net=net,width=width))

by=collections.defaultdict(list)
for pad in pads:
 if pad['net'].startswith('NC:'):continue
 virtual=dict(pad);fan=False
 if pad['ref']=='U1':
  vx=103.3 if pad['x']<110.16 else 117.0;vy=round(pad['y']/STEP)*STEP;fan=True
 elif pad['ref'].startswith(('R','C')):
  vx=round(pad['x']/STEP)*STEP;vy=pad['y']+(-1.6 if abs(pad['y']-115.6)<.01 else 1.6);fan=True
 elif pad['ref']=='J4':
  vx=105.4;vy=round(pad['y']/STEP)*STEP;fan=True
 if abs(pad['y']-96.8)<.01:vy=97.9
 if fan:
  width=.5 if pad['net'].startswith('+') or pad['net']=='GND' else .25
  segments.append(dict(a=[pad['x'],pad['y']],b=[round(vx,3),round(vy,3)],layer=0,net=pad['net'],width=width))
  vias.append(dict(x=round(vx,3),y=round(vy,3),net=pad['net']))
  virtual.update(x=round(vx,3),y=round(vy,3),layers=[0,1])
 by[pad['net']].append(virtual)
# Critical SPI and local decoupling/power first, then short controls, ground last.
order=['I2C_SDA','I2C_SCL','LCD_BL','MODE_SW','LCD_RST','TP_RST','SPI_SCK','SPI_MOSI','LCD_SCK','LCD_MOSI','+3V3_EXT','+3V3_V6','+5V_V6']
order+=sorted((n for n in by if n not in order and n!='GND'),key=lambda n:len(by[n]))
# Ground pads use the filled ground planes, with preplaced escape vias.
order += []
import sys
if len(sys.argv)>1:
 chosen=json.loads(Path(sys.argv[1]).read_text());order=chosen+[net for net in order if net not in chosen]
order=[net for net in order if net in by];failed=[];starttime=time.time()
for net in order:
 pending=by[net][:]
 # Root at supply source / entry connector where available.
 root=next((p for p in pending if (net=='+3V3_EXT' and p['ref']=='R0') or (net=='+3V3_V6' and p['ref']=='J2')),pending[0])
 pending.remove(root);connected=[root];width=.5 if net.startswith('+') else .25
 while pending:
  d,a,b=min((((a['x']-b['x'])**2+(a['y']-b['y'])**2,a,b) for a in pending for b in connected),key=lambda item:item[0])
  path,count=findpath(a,b,net,width)
  if path is None:
   failed.append((net,a['ref']+'.'+a['pin'],b['ref']+'.'+b['pin']));print('FAILED',failed[-1],count,flush=True);pending.remove(a);continue
  store_path(path,net,width);connected.append(a);pending.remove(a)
  print(net,a['ref']+'.'+a['pin'],'->',b['ref']+'.'+b['pin'],len(path),'steps',count,'visited',flush=True)
(R/'tmp/routed_copper.json').write_text(json.dumps(dict(segments=segments,vias=vias,failed=failed)))
print('DONE',len(segments),'segments',len(vias),'vias; failed',failed,'seconds',round(time.time()-starttime),flush=True)
