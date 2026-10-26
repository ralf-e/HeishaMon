from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
old=json.loads((R/'validation/routing_before_cleanup.json').read_text());new=json.loads((R/'hardware/routed_copper.json').read_text());pads=json.loads((R/'hardware/pcb_geometry.json').read_text())
im=Image.new('RGB',(1500,1100),'#eef3f6');d=ImageDraw.Draw(im)
f=lambda n,b=False:ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if b else 'segoeui.ttf'),n)
d.text((30,18),'Routingbereinigung - zwei konkrete Stellen',font=f(34,True),fill='#183b53')
for row,(title,bounds,net) in enumerate([('U1 Pin 6 / MCP_RST',(102,104.7,108,109.2),'MCP_RST'),('C2 / Abblockkondensator',(109,130.5,115,134.5),'+3V3_EXT')]):
 for col,(version,data) in enumerate([('Vorher - Rev.0.5',old),('Nachher - Rev.0.6',new)]):
  x0=30+col*740;y0=100+row*450;w=700;h=355;lo,top,hi,bottom=bounds;scale=min(w/(hi-lo),h/(bottom-top));
  d.rectangle((x0,y0,x0+w,y0+h),fill='#ffffff',outline='#9bb0bc',width=2)
  d.text((x0,y0-35),title+' | '+version,font=f(23,True),fill='#183b53')
  def xy(q):return (x0+(q[0]-lo)*scale,y0+(q[1]-top)*scale)
  def clip(a,b):
   dx=b[0]-a[0];dy=b[1]-a[1];t0=0.;t1=1.
   for p,q in [(-dx,a[0]-lo),(dx,hi-a[0]),(-dy,a[1]-top),(dy,bottom-a[1])]:
    if abs(p)<1e-10:
     if q<0:return None
     continue
    u=q/p
    if p<0:t0=max(t0,u)
    else:t1=min(t1,u)
    if t0>t1:return None
   return [[a[0]+t0*dx,a[1]+t0*dy],[a[0]+t1*dx,a[1]+t1*dy]]
  for s in data['segments']:
   if s['layer']!=0:continue
   clipped=clip(s['a'],s['b'])
   if clipped is None:continue
   d.line([xy(clipped[0]),xy(clipped[1])],fill='#d24b36' if s['net']==net else '#b8c7ce',width=max(1,round(s['width']*scale)))
  for v in data['vias']:
   if not(lo<=v['x']<=hi and top<=v['y']<=bottom):continue
   x,y=xy([v['x'],v['y']]);rad=.3*scale;d.ellipse((x-rad,y-rad,x+rad,y+rad),outline='#557a8e',width=3)
  for p in pads:
   if not(lo<=p['x']<=hi and top<=p['y']<=bottom):continue
   x,y=xy([p['x'],p['y']]);pw=p['w']*scale/2;ph=p['h']*scale/2
   d.rectangle((x-pw,y-ph,x+pw,y+ph),fill='#e5c779',outline='#8e6d24',width=2)
   if y-ph-22>=y0+3:d.text((x-pw,y-ph-22),p['ref']+'.'+p['pin'],font=f(17),fill='#183b53')
d.text((30,1015),'F.Cu-Auszug; Masseflaechen ausgeblendet. Rot: hervorgehobenes Netz, grau: weitere Leiterbahnen.',font=f(23),fill='#183b53')
d.text((30,1055),'MCP_RST: ueberlappenden Ruecklauf entfernt. C2: ungenutzten Leiterbahnauslauf entfernt.',font=f(23),fill='#183b53')
im.save(R/'docs/Routing_Bereinigung_rev06.png')
