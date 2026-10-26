from pathlib import Path
from PIL import Image,ImageDraw
import re,json
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs'
s=(ROOT/'vendor/DisplayFont/glcdfont.c').read_text(encoding='utf8').split('font[] PROGMEM = {',1)[1].split('};',1)[0]
s=re.sub(r'//[^\n]*','',s);font=[int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',s)]
catalog=json.loads((DOC/'topic_catalogue.json').read_text())
def put(d,x,y,s,color='#ffffff',scale=1):
 for ch in s:
  k=ord(ch) if ord(ch)<128 else 63
  for col in range(5):
   for bit in range(8):
    if font[k*5+col]&(1<<bit):d.rectangle((x+col*scale,y+bit*scale,x+(col+1)*scale-1,y+(bit+1)*scale-1),fill=color)
  x+=6*scale

def image_page(name,rows,title,start,total,mode='AUTO / AKTIV'):
 im=Image.new('RGB',(480,320),'#080808');d=ImageDraw.Draw(im)
 text=lambda x,y,s,color='#ffffff',scale=1:put(d,x,y,s,color,scale)
 d.rectangle((4,0,235,21),fill='#101b20',outline='#49d2ff')
 d.rectangle((244,0,475,21),fill='#101b20',outline='#49d2ff')
 text(12,7,'WH-MDC09J3E5','#49d2ff');text(220,7,'>','#49d2ff')
 text(260,7,mode,'#f7b84b' if 'RX:' in mode else '#ffffff');text(460,7,'>','#49d2ff')
 text(8,24,('' if title=='Uebersicht' else title+' | ')+'WP: 2s   EXTRA: 3s   LAN','#9cb4be')
 for x,t in [(8,'Nr.'),(42,'Topic'),(360,'Wert / Einheit')]:text(x,36,t,'#49d2ff')
 for row,(number,label,value) in enumerate(rows[:20]):
  y=48+row*12
  if row%2==0:d.rectangle((4,y,475,y+11),fill='#101b20')
  text(8,y+2,str(number),'#49d2ff');text(42,y+2,label[:50],'#bbced6');text(360,y+2,value[:18])
 for i,t in enumerate(['< ZURUECK','WEITER >','ANSICHTEN','START']):
  d.rectangle((i*120,288,i*120+118,311),outline='#49d2ff');text(i*120+8,296,t)
 text(8,313,str(start+1)+'-'+str(min(start+20,total))+' / '+str(total)+'  |  BEISPIELWERTE','#9cb4be')
 text(330,313,'HMX 0.1.0-dev.7','#9cb4be');im.resize((1440,960),Image.Resampling.NEAREST).save(DOC/name)

overview=json.loads((DOC/'overview.json').read_text(encoding='utf8'))
image_page('display_uebersicht.png',[(r['id'],r['label'],r['sample']) for r in overview],'Uebersicht',0,len(overview))
image_page('display_fremdverkehr.png',[(r['id'],r['label'],r['sample']) for r in overview],'Uebersicht',0,len(overview),'AUTO / RX: LISTEN ONLY')
vals=['0','4 C','8 K','5 K','5 K','-5 K','0','0 C','18 C','35 C','25 C','15 C','-15 C','21 C','0 C','18 C','28 C','27 C','0 W','0 W']
image_page('display_topics.png',[(i,catalog['TOP'][i],vals[i-20]) for i in range(20,40)],'Alle WP-Topics',20,144)
im=Image.new('RGB',(480,320),'#080808');d=ImageDraw.Draw(im)
d.rectangle((4,0,235,21),fill='#101b20',outline='#49d2ff')
d.rectangle((244,0,475,21),fill='#101b20',outline='#49d2ff')
put(d,12,7,'WH-MDC09J3E5','#49d2ff');put(d,220,7,'>','#49d2ff')
put(d,260,7,'AUTO / AKTIV');put(d,460,7,'>','#49d2ff')
put(d,8,24,'Betriebsart | WP: 2s   EXTRA: 3s   LAN','#9cb4be')
put(d,12,52,'Auswahl wird dauerhaft gespeichert','#9cb4be')
for y,label in [(96,'* Automatisch'),(168,'  Listen only')]:
 d.rectangle((12,y,467,y+47),outline='#49d2ff');put(d,24,y+12,label,scale=2)
put(d,12,244,'Aktive Betriebsart steht immer oben','#9cb4be')
put(d,12,268,'Unten: Abbrechen / zur Anzeige zurueck','#9cb4be')
d.rectangle((0,288,118,311),outline='#49d2ff');put(d,8,296,'ABBRECHEN')
put(d,8,313,'Betriebsart dauerhaft speichern','#9cb4be');put(d,330,313,'HMX 0.1.0-dev.7','#9cb4be')
im.resize((1440,960),Image.Resampling.NEAREST).save(DOC/'display_betriebsart.png')
print('6x8 display and persistent-mode previews generated')

# Exact device-info layout from the sample model; display-only community table.
models=json.loads((DOC/'model_catalogue.json').read_text(encoding='utf8'))
m=next(r for r in models['rows'] if r['id']==21)
im=Image.open(DOC/'display_uebersicht.png').resize((480,320),Image.Resampling.NEAREST)
d=ImageDraw.Draw(im);d.rectangle((0,24,479,287),fill='#080808')
put(d,8,24,'Geraeteinfo | WP: 2s   EXTRA: 3s   LAN','#9cb4be')
lines=['Geraeteinfo / TOP92','Status: eindeutig zugeordnet','Innen: '+m['idu'],
'Aussen: '+m['odu'],'Kit: '+m['kit'],'Leistung: '+m['power']+' kW',
'Phasen: '+m['phase'],'Typ: '+m['type'],'','Kennung: '+m['key'],'',
'Quelle: HeishaMon / HeatPumpType.md','Tabelle: '+str(models['count'])+' Eintraege',
'Modelltabelle: '+models['upstream_commit'][:12],'Firmwarebasis: b3ef43691f21','Empfang: 2s','HeishaMon: Local build',
'Erweiterung: HMX 0.1.0-dev.7','Community-Zuordnung; keine WP-Befehle.']
for i,line in enumerate(lines):put(d,8,50+i*12,line,'#49d2ff' if i==0 else '#ffffff')
d.rectangle((121,289,237,310),fill='#080808')
d.rectangle((0,312,329,319),fill='#080808')
put(d,8,313,'Geraeteinfo: Zurueck zur Ansicht','#9cb4be')
im.resize((1440,960),Image.Resampling.NEAREST).save(DOC/'display_geraeteinfo.png')
