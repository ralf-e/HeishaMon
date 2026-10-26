"""Remove unnecessary layer transitions; stitch the two ground planes."""
from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[1]
exec((R/'tools/route_adapter.py').read_text().split('by=collections')[0])
d=json.loads((R/'tmp/routed_copper.json').read_text());segments=d['segments'];vias=d['vias']
drc=json.loads((R/'hardware/DRC.json').read_text())
remove=[]
for v in drc.get('violations',[]):
 if v['type']=='via_dangling':
  pos=v['items'][0]['pos'];remove.append((pos['x'],pos['y']))
vias[:]=[v for v in vias if not any(abs(v['x']-x)<.001 and abs(v['y']-y)<.001 for x,y in remove)]
mask=mask_for('GND',.3,True)
count=0
for y in range(97,136,4):
 for x in [99,103,110,117,121]:
  if any(abs(x-a)<.001 and abs(y-b)<.001 for a,b in remove):continue
  ix,iy=coord(x,y)
  if mask[:,iy,ix].any():continue
  if any((v['x']-x)**2+(v['y']-y)**2<.8**2 for v in vias):continue
  vias.append(dict(x=x,y=y,net='GND'));count+=1
(R/'tmp/routed_copper.json').write_text(json.dumps(d))
print('Removed',len(remove),'dangling transitions; added',count,'ground stitches')
