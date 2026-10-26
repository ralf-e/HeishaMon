"""Actual two-sided PCB plots and illustrative assembly cross section."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
R=Path(__file__).resolve().parents[1]
out=Image.new('RGB',(1600,1350),'#f0f4f7');d=ImageDraw.Draw(out)
f=lambda n,b=False:ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if b else 'segoeui.ttf'),n)
def t(x,y,s,n=26,b=False,c='#183b53'):d.text((x,y),s,font=f(n,b),fill=c)
t(35,18,'HeishaMon V6 – kompakte Überkopf-Platine Rev.0.6',38,True)
t(35,76,'23 × 41 mm · 2 Kupferlagen · 64,2 % weniger Fläche als Rev.0.3',28)
for i,(file,title) in enumerate([('PCB_Vorderseite.png','F: SMD / LCD – montiert unten'),('PCB_Rueckseite.png','B: Stiftleisten – montiert oben')]):
 x=35+i*510;y=173
 im=ImageOps.contain(Image.open(R/'docs'/file).convert('RGB'),(465,765));out.paste(im,(x,y));d.rectangle((x-1,y-1,x+im.width+1,y+im.height+1),outline='#183b53',width=2);t(x,130,title,24,True)
x=1080;y=175
for text in ['Rückseite manuell bestücken:', 'J1/J2: lange Stapelanschlüsse', 'J3: GPIO oben links, 2×4', 'Kein mechanischer Schalter', '', 'Vorderseite mit allen SMD', 'GH-LCD an linker F-Kante.', '', 'Um 180° um die Längsachse', 'kippen: Stecker oben,', 'LCD montiert unten rechts.', '', 'Kontaktspiegelung wird', 'am tatsächlichen PCB geprüft.', '', 'Pin 1: quadratisches Pad.', 'GPIO-Belegung aufgedruckt.']:
 t(x,y,text,25);y+=37
t(35,970,'Einbauprinzip – Seitenansicht; Höhen und V6-Mechanik noch unvermessen',28,True)
# This is an assembly principle, not a dimensioned package model.
d.rectangle((110,1208,1430,1230),fill='#78935c');t(130,1238,'V6-Grundplatine',25)
d.rectangle((220,1104,1350,1125),fill='#4a8686');t(35,1097,'Adapter',25)
for x in [345,1045]:
 d.rectangle((x,1065,x+30,1104),fill='#323b40');d.rectangle((x+10,1125,x+20,1208),fill='#ba9d4b')
d.rectangle((340,1030,1110,1065),fill='#337876');t(500,1033,'W5500 / Ethernet oben',24,c='#ffffff')
for x in [260,300]:d.rectangle((x,1050,x+14,1125),fill='#bc9c43')
t(180,1010,'GPIO J3 oben links',24)
d.rectangle((465,1125,545,1155),fill='#d49a42');d.rectangle((1100,1125,1270,1180),fill='#dbbd64')
t(335,1163,'SMD unten',23);t(990,1181,'GH-LCD unten rechts',23)
t(35,1290,'Kein Fertigungsfreigabestand: Abstand zur V6, Steckerlängen und Kabelraum praktisch prüfen.',25,c='#a05019')
out.save(R/'docs/Platzierung_annotiert.png')
