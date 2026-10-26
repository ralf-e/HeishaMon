from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];a=json.loads((R/'hardware/pcb_audit.json').read_text())
im=Image.new('RGB',(1350,1120),'#eef3f6');d=ImageDraw.Draw(im)
f=lambda n:ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',n)
def text(x,y,s,n=25,c='#183b53'):d.text((x,y),s,font=f(n),fill=c)
scale=20;ox=180;oy=150
def xy(x,y):return (ox+(220.32-x-98.66)*scale,oy+(y-95)*scale)
outline=a['connector_geometry']['edge_segments'];points=[]
# Exact outline, assembled view (B); F connector shown through the board.
poly=[(98.66,95),(121.66,95),(121.66,136),(98.66,136),(98.66,133.5),(99.35,133.5),(99.35,114.1),(98.66,114.1)]
d.polygon([xy(x,y) for x,y in poly],fill='#dce8dc',outline='#42634b',width=3)
for ref,color in [('J1','#d7a440'),('J2','#d7a440'),('J3','#d7a440')]:
 for p in a['pads']+[dict(ref='J2',pin='4',x=100,y=105.12)]: # include intentionally NC contact J2.4
  if p['ref']!=ref:continue
  x,y=xy(p['x'],p['y']);d.ellipse((x-13,y-13,x+13,y+13),fill=color,outline='#564820',width=2);d.ellipse((x-5,y-5,x+5,y+5),fill='#222222')
x1,y1=xy(99.35,112.8);x2,y2=xy(103.4,134.8)
d.rectangle((min(x1,x2),y1,max(x1,x2),y2),fill='#ead49c',outline='#986b18',width=3)
text(40,25,'Rev.0.6 - montierte Ansicht von oben',36)
text(40,78,'23 x 41 mm | GH-Buchse liegt auf der Unterseite',26)
text(230,190,'W5500',26);text(245,226,'oben',23)
text(40,770,'J3: oben links',24);d.line((175,790,*xy(119,129)),fill='#183b53',width=3)
x,y=xy(99.35,123.8);d.line((x,y,920,y),fill='#986b18',width=8);d.polygon([(920,y),(895,y-14),(895,y+14)],fill='#986b18')
text(720,y-90,'GH 90 Grad: unten rechts',26);text(720,y-52,'Kabelabgang seitlich nach rechts',24);text(720,y+25,'Kurzer, gerader Kabelweg zum Display',24)
text(720,820,'Steckfront direkt am ausgesparten Rand.',23)
text(720,856,'Endbereiche tragen die originalen Haltepads.',22)
text(40,1020,'Anschlusslage aus dem PCB; V6-Hoehen und Gehaeusefreiheit praktisch pruefen.',24)
im.save(R/'docs/Montageanschluesse_rev06.png')
