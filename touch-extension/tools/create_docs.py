from pathlib import Path
import re,json,html,shutil
from PIL import Image,ImageDraw,ImageFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image as RLImage,Preformatted,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/"docs";OUT=ROOT/"output";OUT.mkdir(exist_ok=True)
FONT="C:/Windows/Fonts/segoeui.ttf";BOLD="C:/Windows/Fonts/segoeuib.ttf";MONO="C:/Windows/Fonts/consola.ttf"
class Drawing:
 def __init__(self,w,h,title):
  self.w=w;self.h=h;self.im=Image.new("RGB",(w,h),"white");self.p=ImageDraw.Draw(self.im)
  self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>']
  self.text(35,20,title,32,bold=True)
 def text(self,x,y,s,size=22,color="#183147",bold=False):
  self.p.text((x,y),s,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=color)
  self.svg.append(f'<text x="{x}" y="{y+size}" fill="{color}" font-family="Segoe UI, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(s))}</text>')
 def rect(self,x,y,w,h,label=None):
  self.p.rounded_rectangle((x,y,x+w,y+h),radius=9,fill="#f1f6fa",outline="#42677d",width=2)
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#f1f6fa" stroke="#42677d" stroke-width="2"/>')
  if label:self.text(x+15,y+12,label,24,bold=True)
 def line(self,x1,y1,x2,y2,label=None,color="#087e8b"):
  self.p.line((x1,y1,x2,y2),fill=color,width=3)
  self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"/>')
  if label:self.text((x1+x2)//2-50,(y1+y2)//2-27,label,20,color)
 def node(self,x,y):
  self.p.ellipse((x-5,y-5,x+5,y+5),fill="#087e8b")
  self.svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#087e8b"/>')
 def resistor(self,x,y,label):
  self.p.rectangle((x-10,y,x+10,y+45),fill="white",outline="#087e8b",width=3)
  self.svg.append(f'<rect x="{x-10}" y="{y}" width="20" height="45" fill="white" stroke="#087e8b" stroke-width="3"/>')
  self.text(x+17,y+5,label,21)
 def save(self,name):
  self.svg.append("</svg>");(DOC/(name+".svg")).write_text("\n".join(self.svg),encoding="utf8");self.im.save(DOC/(name+".png"))
d=Drawing(1650,820,"HeishaMon V6: steckbarer Zwischenadapter mit optionalem Ethernet")
d.rect(40,180,350,390,"HeishaMon V6")
for j,s in enumerate(["Ethernet-Stiftleiste","SPI: GPIO11 / 12 / 13","ETH: GPIO10 / 14 / 15","","Extra-GPIO33 bis 37","Gepruefte Versorgung"]):d.text(60,240+j*43,s,22)
d.rect(570,180,510,390,"Zwischenadapter")
for j,s in enumerate(["W5500: kontaktgleich durchverbunden","Display: eigener CS / DC / BL","I2C: Touch + MCP23008","Betriebsart per Touch + NVS","3,3-V-Versorgung der Erweiterung","Keine direkte Modul-Loetung"]):d.text(590,245+j*43,s,22)
d.rect(1240,180,370,390,"Waveshare SKU29318")
for j,s in enumerate(["3,5-Zoll IPS, 480 x 320","ST7796S: SPI","FT6336U: I2C","Touch nur fuer Anzeige","15-poliges GH1.25-Kabel","Keine SD-Kartennutzung"]):d.text(1260,245+j*43,s,22)
for a in [(390,330,570,330,"SPI"),(390,475,570,475,"GPIO"),(1080,330,1240,330,"SPI"),(1080,475,1240,475,"I2C")]:d.line(*a)
d.rect(615,85,420,65,"W5500 / USR-ES1 optional");d.line(825,150,825,180)
d.rect(590,650,470,65,"Touch: Auto / Listen only (NVS)");d.line(825,570,825,650)
d.text(40,755,"Netzplan, keine behauptete V6-Steckerreihenfolge. Kontaktpositionen am eigenen Board messen.",23,color="#a34e11");d.save("adapter_uebersicht")
d=Drawing(1650,1120,"SPI-Anschlussplan - gemeinsame Leitungen, getrennte Chip-Selects")
d.rect(40,100,360,390,"V6: logische Netze");d.rect(1190,100,410,390,"Display: 15-poliger Stecker")
for y,g,pin in [(190,"GPIO12 / SCK","6 SCLK"),(265,"GPIO11 / MOSI","5 MOSI")]:
 d.text(60,y-17,g,24);d.text(1210,y-17,pin,24);d.line(400,y,1190,y)
d.text(60,340,"GPIO13 / MISO",24);d.line(400,355,610,355);d.line(610,355,610,670)
d.rect(440,670,620,170,"W5500 auf dem Zwischenadapter")
d.text(575,735,"MISO",24);d.text(735,735,"SCK",24);d.text(845,735,"MOSI",24);d.text(465,785,"CS=GPIO10 / RST=GPIO14 / IRQ=GPIO15",22)
d.line(760,190,760,670);d.node(760,190);d.line(880,265,880,670);d.node(880,265)
d.text(1210,340,"4 MISO: offen",24);d.text(60,410,"GPIO10 / 14 / 15",24);d.text(60,448,"nur zum W5500",22)
d.rect(40,870,1550,170,"Weitere Displayleitungen")
for j,s in enumerate(["GPIO33 -> 8 LCD_CS   |   GPIO34 -> 9 LCD_DC   |   GPIO35 -> 11 LCD_BL (PWM)",
"8 LCD_CS: 10 kOhm nach 3,3 V   |   11 LCD_BL: 100 kOhm nach GND",
"7 SD_CS: 10 kOhm nach 3,3 V   |   10 LCD_RST: MCP GP2   |   15 TP_RST: MCP GP1"]):d.text(60,925+j*34,s,23)
d.text(40,1068,"SCK/MOSI kurz halten; optional je 22-47 Ohm am Abzweig. Alle Logikpegel 3,3 V.",23,color="#a34e11");d.save("adapter_spi")
d=Drawing(1650,1180,"I2C-, Reset- und Versorgungsplan")
d.rect(40,110,330,390,"V6 Extra-GPIOs");d.text(60,235,"GPIO36 / SDA",25);d.text(60,365,"GPIO37 / SCL",25)
d.rect(1200,110,400,390,"FT6336U / Touch 0x38");d.text(1220,235,"12 TP_SDA",25);d.text(1220,365,"13 TP_SCL",25)
d.line(370,255,1200,255);d.line(370,385,1200,385)
for x,y in [(620,255),(920,385)]:
 d.line(x,95,x,150);d.resistor(x,150,"4k7");d.line(x,195,x,y);d.node(x,y);d.text(x-40,65,"3,3 V",22)
d.rect(460,610,650,250,"MCP23008, Adresse 0x20")
d.line(710,255,710,610);d.node(710,255);d.line(1020,385,1020,610);d.node(1020,385)
d.text(675,575,"SDA",21);d.text(990,575,"SCL",21)
for j,s in enumerate(["VDD=3,3 V / VSS=GND / A0,A1,A2=GND","RESET: 10k nach 3,3 V; 100nF an VDD","GP1 -> 15 TP_RST; GP2 -> 10 LCD_RST","Beide Resetleitungen: je 10k nach 3,3 V"]):d.text(480,680+j*37,s,22)
d.text(45,950,"GP0 bleibt frei.",25)
d.text(45,1000,"Kein Schalter, kein R4.",23)
d.text(45,1033,"Betriebsart im ESP32 gespeichert.",23)
d.rect(1180,610,420,400,"Versorgung Erweiterung")
for j,s in enumerate(["V6: vorhandene 3,3 V","-> R0 (0 Ohm / Messung)","-> Display 1 VCC","-> MCP23008 VDD","","Display 2 3V3: offen","Alle GND gemeinsam","10uF + 100nF am Display","Keine Quellen parallel"]):d.text(1200,670+j*33,s,22)
d.text(460,1020,"Touch-INT und MCP-INT bleiben offen; Abfrage per Software.",22)
d.text(40,1115,"MCP23008 verwenden. Keine 5-V-Pull-ups auf SDA/SCL. V6-Versorgung vor Anschluss pruefen.",23,color="#a34e11");d.save("adapter_details")
overview=json.loads((DOC/"overview.json").read_text(encoding="utf8"))
samples=[(r["label"],r["sample"]) for r in overview]
h=(ROOT/"firmware/HeishaMon/decode.h").read_text(encoding="utf8")
def names(array):return re.findall(r'"([^"]+)"',re.search(r"static const char "+array+r"\[.*?\]\s+PROGMEM\s*=\s*\{(.*?)\};",h,re.S)[1])
catalog={"TOP":names("topics"),"XTOP":names("xtopics"),"OPT":names("optTopics")}
(DOC/"topic_catalogue.json").write_text(json.dumps(catalog,indent=2),encoding="utf8")
model_catalogue=json.loads((DOC/"model_catalogue.json").read_text(encoding="utf8"))
(DOC/"preview_data.js").write_text("const cat="+json.dumps(catalog)+";\nconst samples="+json.dumps(samples)+";\nconst overviewIds="+json.dumps([r["id"] for r in overview])+";\nconst modelCatalogue="+json.dumps(model_catalogue)+";",encoding="utf8")
import runpy
runpy.run_path(str(ROOT/"tools/make_ui_preview.py"))
pdfmetrics.registerFont(TTFont("Segoe",FONT));pdfmetrics.registerFont(TTFont("SegoeB",BOLD));pdfmetrics.registerFont(TTFont("Consola",MONO))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name="BodyDE",fontName="Segoe",fontSize=9.4,leading=14,spaceAfter=7,textColor=colors.HexColor("#173248")))
styles.add(ParagraphStyle(name="TitleDE",fontName="SegoeB",fontSize=25,leading=31,spaceAfter=14,textColor=colors.HexColor("#12334a")))
styles.add(ParagraphStyle(name="H2DE",fontName="SegoeB",fontSize=14,leading=19,spaceBefore=15,spaceAfter=9,textColor=colors.HexColor("#087e8b"),keepWithNext=True))
styles.add(ParagraphStyle(name="CellDE",fontName="Segoe",fontSize=8,leading=11,spaceAfter=0))
styles.add(ParagraphStyle(name="CodeDE",fontName="Consola",fontSize=7,leading=10,backColor=colors.HexColor("#edf2f5"),borderPadding=7,spaceAfter=9))
def fmt(s):
 s=html.escape(s);s=re.sub(r"\*\*(.*?)\*\*",r"<b>\1</b>",s)
 s=re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",r'<link href="\2" color="#087e8b">\1</link>',s);return s
lines=(DOC/"HeishaMon_V6_Touch_Anleitung.md").read_text(encoding="utf8").splitlines();story=[];i=0;fence=chr(96)*3
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith(fence):
  code=[];i+=1
  while i<len(lines) and not lines[i].startswith(fence):code.append(lines[i]);i+=1
  import textwrap
  wrapped=[]
  for c in code:wrapped+=textwrap.wrap(c,100,subsequent_indent="    ",break_long_words=True,break_on_hyphens=False) or [""]
  story.append(Preformatted("\n".join(wrapped),styles["CodeDE"]));i+=1;continue
 if line.startswith("|"):
  rows=[]
  while i<len(lines) and lines[i].startswith("|"):
   cells=[x.strip() for x in lines[i].strip("|").split("|")]
   if not all(re.fullmatch(r"[-: ]+",x) for x in cells):rows.append([Paragraph(fmt(x),styles["CellDE"]) for x in cells])
   i+=1
  n=len(rows[0]);widths=[495/n]*n
  if n==2:widths=[170,325]
  if n==3:widths=[155,160,180]
  t=Table(rows,colWidths=widths,repeatRows=1,hAlign="LEFT")
  t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dcecf2")),("VALIGN",(0,0),(-1,-1),"TOP"),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#c4d3dc")),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]));story+=[t,Spacer(1,9)];continue
 if line.startswith("!["):
  name=re.search(r"\((.*?)\)",line)[1];im=Image.open(DOC/name);w,h=im.size
  scale=min(495/w,(475 if name.startswith("renderings/") else 570)/h);story.append(RLImage(str(DOC/name),width=w*scale,height=h*scale));story.append(Spacer(1,9))
  if name=="adapter_uebersicht.png":
   im=Image.open(DOC/"adapter_spi.png");w,h=im.size;story.append(Paragraph("SPI-Anschlussplan",styles["H2DE"]));story.append(RLImage(str(DOC/"adapter_spi.png"),width=495,height=495*h/w))
  i+=1;continue
 if line.startswith("# "):story.append(Paragraph(fmt(line[2:]),styles["TitleDE"]));i+=1;continue
 if line.startswith("### JLCPCB-Rendering:"):story.append(PageBreak())
 if line.startswith("### "):story.append(Paragraph(fmt(line[4:]),styles["H2DE"]));i+=1;continue
 if line.startswith("## "):story.append(Paragraph(fmt(line[3:]),styles["H2DE"]));i+=1;continue
 para=[line];i+=1
 while i<len(lines) and lines[i].strip() and not lines[i].startswith(("#","|",fence,"![")):para.append(lines[i]);i+=1
 story.append(Paragraph("<br/>".join(fmt(p) for p in para),styles["BodyDE"]))
def footer(c,doc):
 c.saveState();c.setStrokeColor(colors.HexColor("#c4d3dc"));c.line(50,43,545,43);c.setFont("Segoe",8);c.setFillColor(colors.HexColor("#546c7b"))
 c.drawString(50,30,"HeishaMon V6 Touch | 0.1.0-dev.7 | Entwicklungsstand, Hardwaretest ausstehend");c.drawRightString(545,30,str(doc.page));c.restoreState()
(ROOT/"tmp").mkdir(exist_ok=True)
pdf=ROOT/"tmp/HeishaMon_V6_Touch_Anleitung_dev7_Rev06_Basis.pdf"
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=58,title="HeishaMon V6 Touchdisplay - Aufbau und Software",author="Projekt HeishaMon").build(story,onFirstPage=footer,onLaterPages=footer)
shutil.copyfile(DOC/"HeishaMon_V6_Touch_Anleitung.md",OUT/"HeishaMon_V6_Touch_Anleitung_dev7_Rev06.md")
print("PDF, Schaltplaene, Displaybilder und Topic-Katalog erzeugt")

(DOC/"Display_Vorschau.html").write_text((DOC/"preview_template.html").read_text(encoding="utf8").replace("/*DATA*/",(DOC/"preview_data.js").read_text(encoding="utf8")),encoding="utf8")

from pypdf import PdfWriter
w=PdfWriter()
for p in [pdf,ROOT/"hardware/Gesamtschaltplan_rev06.pdf",ROOT/"hardware/Gesamtverdrahtung_rev06.pdf"]:w.append(str(p))
with open(OUT/"HeishaMon_V6_Touch_Anleitung_dev7_Rev06.pdf","wb") as out:w.write(out)
