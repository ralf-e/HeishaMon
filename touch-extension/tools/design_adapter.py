"""Generate a complete native KiCad schematic and a 2-layer placement draft.
Run with KiCad's Python (pcbnew). Connector geometry is a vendor-reference draft.
No Gerbers are generated: V6 mechanics and routing still require validation.
"""
from pathlib import Path
import json,re,uuid,math,copy,sys
import pcbnew as pcb
ROOT=Path(__file__).resolve().parents[1]
VOLTAGE='--voltage' in sys.argv
OUT=ROOT/"hardware"/"Rev07" if VOLTAGE else ROOT/"hardware"
OUT.mkdir(parents=True,exist_ok=True)
LIB=Path("C:/Program Files/KiCad/10.0/share/kicad")
class Q(str):pass
def parse(s):
 tok=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s);stack=[];root=None
 for t in tok:
  if t=="(":
   x=[]
   if stack:stack[-1].append(x)
   stack.append(x)
  elif t==")":
   x=stack.pop()
   if not stack:root=x
  else:
   if t.startswith('"'):v=Q(json.loads(t))
   else:
    try:v=float(t) if "." in t else int(t)
    except ValueError:v=t
   stack[-1].append(v)
 return root
def emit(x):
 if isinstance(x,list):return "("+" ".join(emit(v) for v in x)+")"
 if isinstance(x,Q):return json.dumps(str(x),ensure_ascii=False)
 if isinstance(x,float):return f"{x:.6f}".rstrip("0").rstrip(".")
 return str(x)
def child(x,key,default=None):return next((i for i in x if isinstance(i,list) and i and i[0]==key),default)
def children(x,key):return [i for i in x if isinstance(i,list) and i and i[0]==key]
def uid():return str(uuid.uuid4())
def effects(size=1.0,justify=None,hide=False):
 e=["effects",["font",["size",size,size]]]
 if justify:e.append(["justify",justify])
 if hide:e.append(["hide","yes"])
 return e
def voltage_annotations(sch):
 existing={str(v[1]) for v in children(sch,'text')}
 for title,x1,y1,x2,y2 in [('9  Spannungsmessung / ADC / Isolation',420,28,582,250),('10  12V-Messanschluss, kein Versorgungseingang',420,252,582,280),('11  Vier Messkanaele / Teiler und Filter',10,280,450,410)]:
  if title in existing:continue
  sch.append(['rectangle',['start',x1,y1],['end',x2,y2],['stroke',['width',.254],['type','default']],['fill',['type','none']],['uuid',Q(uid())]])
  sch.append(['text',Q(title),['at',x1+3,y1+5,0],effects(1.5,'left'),['uuid',Q(uid())]])
 sch[:]=[v for v in sch if not (isinstance(v,list) and v and v[0]=='text' and str(v[1]) in ['V6-Belegung / Hoehen / Stromreserve praktisch pruefen.','Keine Fertigungsfreigabe ohne Hardwarepruefung.'])]
 notes=[('GP0 = ADC_ENABLE: Low -> Messwerte ungueltig.',423,239),('AIN0 V6 3V3 / AIN1 EXT 3V3 / AIN2 5V / AIN3 12V',423,244),('Keine Fertigungsfreigabe; Passform und Hardwaretest ausstehend.',455,292),('12V nur Messleitung, positive Spannung 0..18V gegen GND.',455,299)]
 for label,x,y in notes:
  if label not in existing:sch.append(['text',Q(label),['at',x,y,0],effects(1.27,'left'),['uuid',Q(uid())]])

cache={}
def symbol(lib,name):
 key=lib+":"+name
 if key not in cache:
  tree=parse((LIB/"symbols"/(lib+".kicad_sym")).read_text(encoding="utf8"))
  value=next(i for i in children(tree,"symbol") if i[1]==name)
  parent=child(value,'extends')
  if parent:
   _,base=symbol(lib,str(parent[1]))
   inherited=copy.deepcopy(base);inherited[1]=Q(name)
   for item in children(inherited,'symbol'):item[1]=Q(str(item[1]).replace(str(parent[1]),name))
   for prop in children(value,'property'):
    inherited=[v for v in inherited if not (isinstance(v,list) and len(v)>1 and v[0]=='property' and v[1]==prop[1])]
    inherited.append(copy.deepcopy(prop))
   value=inherited
  cache[key]=copy.deepcopy(value)
 return key,copy.deepcopy(cache[key])
def getpins(sym):
 out=[]
 for unit in children(sym,"symbol"):
  for p in children(unit,"pin"):
   num=str(child(p,"number")[1]);name=str(child(p,"name")[1]);at=child(p,"at")
   out.append({"number":num,"name":name,"x":float(at[1]),"y":float(at[2]),"angle":int(at[3]),"type":str(p[1])})
 return out
comps=[]
def add(ref,lib,name,value,foot,nets,at,boardat,rot=0):
 key,sym=symbol(lib,name)
 comps.append(dict(ref=ref,lib_id=key,symbol=sym,value=value,footprint=foot,
                   nets={str(k):v for k,v in nets.items()},at=at,boardat=boardat,rot=rot,uuid=uid()))
con="Connector_Generic"
hdr=lambda n:f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"
add("J1",con,"Conn_01x06","USR-ES1 Reihe 1 / DURCHSTECK",hdr(6),
 {1:"GND",2:"GND",3:"SPI_MOSI",4:"SPI_SCK",5:"ETH_CS",6:"ETH_IRQ"},(40,55),(100,100))
add("J2",con,"Conn_01x06","USR-ES1 Reihe 2 / DURCHSTECK",hdr(6),
 {1:"GND",2:"+3V3_V6",3:"+3V3_V6",4:None,5:"ETH_RST",6:"SPI_MISO"},(40,95),(120.32,100))
add("J3",con,"Conn_01x08","V6 GPIO + VERSORGUNG / Adapterbelegung",hdr(8),
 {1:"LCD_CS",2:"LCD_DC",3:"LCD_BL",4:"I2C_SDA",5:"I2C_SCL",6:"+3V3_V6",7:"+5V_V6",8:"GND"},(40,145),(140,99))
add("J4",con,"Conn_01x15","Waveshare SKU29318 / GH1.25 15pol",
 "Connector_JST:JST_GH_SM15B-GHS-TB_1x15-1MP_P1.25mm_Horizontal",
 {1:"+3V3_EXT",2:None,3:"GND",4:None,5:"LCD_MOSI",6:"LCD_SCK",7:"SD_CS",
 8:"LCD_CS",9:"LCD_DC",10:"LCD_RST",11:"LCD_BL",12:"I2C_SDA",13:"I2C_SCL",14:None,15:"TP_RST"},(352,60),(116,130))
u_key,u_sym=symbol("Interface_Expansion","MCP23008-xSO")
pn={p["name"]:p["number"] for p in getpins(u_sym)}
nets={}
for p in getpins(u_sym):
 name=p["name"].replace("~{","").replace("}","").upper()
 if name in ["VDD"]:net="+3V3_EXT"
 elif name in ["VSS","A0","A1","A2"]:net="GND"
 elif name=="SDA":net="I2C_SDA"
 elif name=="SCL":net="I2C_SCL"
 elif "RESET" in name:net="MCP_RST"
 elif name=="GP0":net=None
 elif name=="GP1":net="TP_RST"
 elif name=="GP2":net="LCD_RST"
 else:net=None
 nets[p["number"]]=net
ufoot=str(child(next(i for i in u_sym if isinstance(i,list) and i[:2]==["property",Q("Footprint")]),"unused","")[1]) if False else str(next(i[2] for i in children(u_sym,"property") if i[1]=="Footprint"))
add("U1","Interface_Expansion","MCP23008-xSO","MCP23008-xSO",ufoot,nets,(200,110),(131,111))
rdefs=[
 ("R0","0R / MESSBRUECKE","+3V3_V6","+3V3_EXT",(100,45),(125,95),0),
 ("R1","4k7","+3V3_EXT","I2C_SDA",(100,85),(133,96),0),
 ("R2","4k7","+3V3_EXT","I2C_SCL",(125,85),(137,96),0),
 ("R3","10k","+3V3_EXT","MCP_RST",(100,125),(130,122),0),
 ("R5","10k","+3V3_EXT","LCD_CS",(100,165),(104,122),0),
 ("R6","10k","+3V3_EXT","LCD_RST",(125,165),(114,122),0),
 ("R7","10k","+3V3_EXT","TP_RST",(150,165),(124,122),0),
 ("R8","33R","SPI_MOSI","LCD_MOSI",(240,45),(105,116),0),
 ("R9","33R","SPI_SCK","LCD_SCK",(265,45),(112,116),0),
 ("R10","10k","+3V3_EXT","SD_CS",(240,165),(118,116),0),
 ("R11","100k","LCD_BL","GND",(265,165),(134,126),0)]
for ref,value,n1,n2,at,bp,rot in rdefs:add(ref,"Device","R",value,"Resistor_SMD:R_0805_2012Metric",{1:n1,2:n2},at,bp,rot)
for ref,value,at,bp in [("C1","100n MCP",(185,185),(136,103.5)),("C2","100n LCD",(215,185),(109,123.5)),("C3","10u LCD",(245,185),(120,126))]:
 add(ref,"Device","C",value,"Capacitor_SMD:C_0805_2012Metric",{1:"+3V3_EXT",2:"GND"},at,bp)
for ref,net,at,bp in [("TP1","+3V3_V6",(95,215),(124,99)),("TP2","+3V3_EXT",(135,215),(132,99)),("TP3","+5V_V6",(175,215),(140,95)),("TP4","GND",(215,215),(100,131))]:
 add(ref,"Connector","TestPoint",net,"TestPoint:TestPoint_Pad_D1.0mm",{1:net},at,bp)
# Rev.0.6: compact, mounted upside down. F = SMD underside; B = headers above.
# Physical 180-degree flip about the longitudinal Y axis: x_mounted=220.32-x.
positions={"J1":(120.32,97.5),"J2":(100,97.5),"J3":(120.32,125),"J4":(101.8,123.8),"U1":(110.16,105),"C1":(115.6,96.8),"C2":(106.2,121),"C3":(114,121),"R0":(104.8,96.8),"R8":(108.4,96.8),"R9":(112,96.8)}
for refs,y in [([1,2,3],116),([5,6,7],120)]:
 for i,x in zip(refs,[108.4,112,115.6]):positions['R'+str(i)]=(x,y)
positions.update({'R10':(108.4,124),'R11':(108.4,128),'C2':(112,132),'C3':(112,128),"TP1":(101.9,95.9),"TP2":(118.5,95.9),"TP3":(108,134.8),"TP4":(112,134.8)})
# Compact the GPIO header from 1x8 to 2x4; logical contact numbering is preserved.
for c in comps:
 if c['ref']=='J4':c['rot']=270
 if c['ref']=='J3':
  c['lib_id'],c['symbol']=symbol(con,'Conn_02x04_Odd_Even');c['footprint']='Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical'
 if c['ref'] in positions:c['boardat']=positions[c['ref']]
assert not any(c["ref"] in {"J5","R4","S1"} for c in comps)
# The upper mating contacts of the stack sockets are the external W5500 module.
# Show them explicitly in the complete schematic, with no extra PCB footprint.
for ref,source,at in [('J6','J1',(280,55)),('J7','J2',(280,95))]:
 original=next(c for c in comps if c['ref']==source)
 add(ref,con,'Conn_01x06','USR-ES1 Modul / externe Gegenkontakte','',original['nets'],at,(0,0))
# Readable schematic positions; PCB positions remain independent.
sch_positions={'J1':(43.18,57.15),'J2':(43.18,110.49),'J6':(104.14,57.15),'J7':(104.14,110.49),'J3':(66.04,181.61),'J4':(353.06,88.9),'U1':(204.47,144.78),'R0':(151.13,57.15),'C1':(184.15,57.15),'C2':(217.17,57.15),'C3':(250.19,57.15),'R1':(151.13,214.63),'R2':(184.15,214.63),'R3':(217.17,214.63),'R5':(250.19,214.63),'R6':(151.13,250.19),'R7':(184.15,250.19),'R10':(217.17,250.19),'R11':(250.19,250.19),'R8':(320.04,241.3),'R9':(377.19,241.3),'TP1':(25.4,238.76),'TP2':(57.15,238.76),'TP3':(88.9,238.76),'TP4':(114.3,238.76)}
short_values={'J1':'V6 / Reihe 1','J2':'V6 / Reihe 2','J6':'W5500 / Reihe 1','J7':'W5500 / Reihe 2','J3':'GPIO / 2x4','J4':'Display / GH15','R0':'0R Messbruecke','C1':'100n MCP','C2':'100n Display','C3':'10u Display'}
for c in comps:
 if c['ref'] in sch_positions:c['at']=sch_positions[c['ref']]
 if c['ref'] in short_values:c['value']=short_values[c['ref']]
 c['schrot']=90 if c['ref'] in ['R8','R9'] else 0
if VOLTAGE:
 exec(compile((ROOT/'tools/voltage_monitor_design.py').read_text(encoding='utf8'),'voltage_monitor_design.py','exec'),globals())
# One complete schematic sheet: labels connect every instance of a named net.
schid=uid()
sch=["kicad_sch",["version",20250114],["generator",Q("eeschema")],["uuid",Q(schid)],["paper",Q("A3")],
 ["title_block",["title",Q("HeishaMon V6 Touch - vollstaendiger Schaltplan")],["rev",Q("0.6 DRAFT")],
 ["comment",1,Q("3V3 aus V6; kein Zusatzregler; V6-Steckerpositionen und Reserve pruefen")],
 ["comment",2,Q("J1/J2: USR-ES1 Herstellerreferenz; Raster 2.54, Reihenabstand 20.32 mm")],
 ["comment",3,Q("Keine Fertigungsfreigabe. V6-Mechanik und Stromreserve sind noch nicht bestaetigt.")]]]
if VOLTAGE:
 child(sch,'paper')[1]=Q('A2')
 child(child(sch,'title_block'),'rev')[1]=Q('0.7 DRAFT')
libs=["lib_symbols"]
for key,orig in cache.items():
 if key not in {c["lib_id"] for c in comps}:continue
 x=copy.deepcopy(orig);x[1]=Q(key);libs.append(x)
sch.append(libs)
def wirelabel(x,y,dx,dy,net,typ="passive"):
 endx=x+dx;endy=y+dy
 sch.append(["wire",["pts",["xy",x,y],["xy",endx,endy]],["stroke",["width",0],["type","default"]],["uuid",Q(uid())]])
 # Local label keeps the complete netlist on this single sheet.
 sch.append(["label",Q(net),["at",endx,endy,0],effects(1.27,"right" if dx<0 else "left"),["uuid",Q(uid())]])
for c in comps:
 x,y=[round(float(v)/1.27)*1.27 for v in c["at"]]
 instance=["symbol",["lib_id",Q(c["lib_id"])],["at",x,y,c.get("schrot",0)],["unit",1],
 ["in_bom","yes"],["on_board","yes" if c["footprint"] else "no"],["dnp","no"],["uuid",Q(c["uuid"])],
 ["property",Q("Reference"),Q(c["ref"]),["at",x+5,y-1.5,0],effects(1.0)],
 ["property",Q("Value"),Q(c["value"]),["at",x+5,y+1,0],effects(.85)],
 ["property",Q("Footprint"),Q(c["footprint"]),["at",x,y,0],effects(.8,hide=True)],
 ["instances",["project",Q("HeishaMon_V6_Touch_Adapter"),
 ["path",Q("/"+schid),["reference",Q(c["ref"])],["unit",1]]]]]
 for p in getpins(c["symbol"]):
  num=p["number"];instance.append(["pin",Q(num),["uuid",Q(uid())]])
  theta=math.radians(c["schrot"]);px=round(x+p["x"]*math.cos(theta)-p["y"]*math.sin(theta),6);py=round(y-p["x"]*math.sin(theta)-p["y"]*math.cos(theta),6);net=c["nets"].get(num)
  if not net:
   sch.append(["no_connect",["at",px,py],["uuid",Q(uid())]])
  else:
   # Follow the pin's external direction.
   angle=(p["angle"]+c["schrot"])%360
   dx,dy={0:(-7.62,0),180:(7.62,0),90:(0,5.08),270:(0,-5.08)}.get(angle,(-7.62,0))
   wirelabel(px,py,dx,dy,net,p["type"])
 for prop in children(instance,"property"):
  if prop[1] not in ["Reference","Value"]:continue
  if c["ref"]=="J3":
   child(prop,"at")[1:]=[x,y-12.7 if prop[1]=="Reference" else y-10.16,0]
   prop[-1]=effects(1.27)
  elif c['ref']=='J4':
   child(prop,'at')[1:]=[x,y-23 if prop[1]=='Reference' else y-20,0]
   prop[-1]=effects(1.1 if prop[1]=='Reference' else .95)
  elif c['ref'] in ['R8','R9']:
   child(prop,'at')[1:]=[x,y-4 if prop[1]=='Reference' else y+4,90]
   prop[-1]=effects(1.0)
  elif c["ref"].startswith("J"):
   child(prop,"at")[1:]=[x,y-14 if prop[1]=="Reference" else y-11,0]
   prop[-1]=effects(1.0 if prop[1]=="Reference" else .85)
  elif c["ref"]=="U1":
   child(prop,"at")[1:]=[x,y-30 if prop[1]=="Reference" else y-27,0]
  elif c['ref'] in ['U2','U3','U4']:
   libprop=next(v for v in children(c['symbol'],'property') if v[1]==prop[1])
   at=child(libprop,'at')
   child(prop,'at')[1:]=[x+at[1],y-at[2],0]
   prop[-1]=effects(1.27 if prop[1]=='Reference' else 1.1)
 sch.append(instance)
# Power flags are explicit declarations of external power supplied by V6.
key,pflag=symbol("power","PWR_FLAG");pf=copy.deepcopy(pflag);pf[1]=Q(key);libs.append(pf)
for idx,(net,x,y) in enumerate([("+3V3_V6",151.13,278.13),("+3V3_EXT",194.31,278.13),("GND",237.49,278.13)]):
 x=round(x/1.27)*1.27;y=round(y/1.27)*1.27
 ref="#FLG0"+str(idx+1)
 sch.append(["symbol",["lib_id",Q(key)],["at",x,y,0],["unit",1],["in_bom","no"],["on_board","no"],["dnp","no"],["uuid",Q(uid())],
 ["property",Q("Reference"),Q(ref),["at",x,y,0],effects(1,hide=True)],
 ["property",Q("Value"),Q("PWR_FLAG"),["at",x,y-4,0],effects(1)],
 ["instances",["project",Q("HeishaMon_V6_Touch_Adapter"),["path",Q("/"+schid),["reference",Q(ref)],["unit",1]]]]])
 wirelabel(x,y,0,5.08,net)
# Functional groups with plenty of room for net labels and pin names.
for title,x1,y1,x2,y2 in [('1  Ethernet / V6 - W5500',10,28,123,147),('2  Zusaetzliche GPIOs',10,154,123,207),('3  Messpunkte',10,215,123,268),('4  Versorgung / Entkopplung',130,28,278,87),('5  I2C-Portexpander / Reset',130,94,278,183),('6  Pull-ups / Backlight-Pulldown',130,190,278,268),('7  Display / Touch',285,28,409,216),('8  SPI-Serienwiderstaende',285,222,409,251)]:
 sch.append(['rectangle',['start',x1,y1],['end',x2,y2],['stroke',['width',.254],['type','default']],['fill',['type','none']],['uuid',Q(uid())]])
 sch.append(['text',Q(title),['at',x1+3,y1+5,0],effects(1.8,'left'),['uuid',Q(uid())]])
for c in comps:
 if c['ref']!='J4':continue
 x,y=c['at'];names=['VCC (3.3V)','3V3 (frei)','GND','MISO (frei)','MOSI','SCLK','SD_CS','LCD_CS','LCD_DC','LCD_RST','LCD_BL','TP_SDA','TP_SCL','TP_INT (frei)','TP_RST']
 for pin in getpins(c['symbol']):
  sch.append(['text',Q(names[int(pin['number'])-1]),['at',x+5.08,y-pin['y'],0],effects(1.27,'left'),['uuid',Q(uid())]])
for text,x,y,size in [
 ('Gleichnamige Netze sind auf diesem Blatt elektrisch verbunden.',12,15,1.4),
 ('23 x 41 mm / 2 Lagen / GH Side Entry / Touch-Betriebsart im ESP32 gespeichert',12,21,1.1),
 ('J6/J7: externe Gegenkontakte am W5500, keine weiteren PCB-Stecker.',13,139,1.0),
 ('J3 ist Adapterbelegung; V6-GPIOs vor Anschluss messen.',13,201,1.0),
 ('GPIO33 CS / 34 DC / 35 BL / 36 SDA / 37 SCL',13,195,1.0),
 ('VCC an J4.1 = 3.3V; J4.2 bleibt offen.',290,137,1.1),
 ('Touch per I2C-Polling (30 ms); kein TP_INT erforderlich.',290,144,1.0),
 ('Kein LCD-Readback, keine SD-Nutzung: MISO offen.',290,151,1.0),
 ('SD_CS mit Pull-up deaktiviert; 5V nur Reserve.',290,158,1.0),
 ('Kabel: GH15 beidseitig, elektrisch 1:1.',290,171,1.0),
 ('MCP23008: Adresse 0x20; Touch: 0x38.',137,175,1.0),
 ('R0 entfernbar zur Strommessung; kein Zusatzregler.',137,80,1.0),
 ('V6-Belegung / Hoehen / Stromreserve praktisch pruefen.',12,278,1.0),
 ('Keine Fertigungsfreigabe ohne Hardwarepruefung.',12,284,1.0)]:
 sch.append(['text',Q(text),['at',x,y,0],effects(max(size,1.27),'left'),['uuid',Q(uid())]])
if VOLTAGE:voltage_annotations(sch)
schpath=OUT/"HeishaMon_V6_Touch_Adapter.kicad_sch"
schpath.write_text(emit(sch)+"\n",encoding="utf8")
# PCB: compact two-layer component placement, deliberately unrouted.
board=pcb.BOARD();board.SetCopperLayerCount(2)
board.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.6))
board.GetDesignSettings().SetAuxOrigin(pcb.VECTOR2I(pcb.FromMM(98.66),pcb.FromMM(136)))
netnames=sorted({net for c in comps for net in c["nets"].values() if net})
nets={}
for name in netnames:
 n=pcb.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
for c in comps:
 if not c["footprint"]:continue
 library,fpname=c["footprint"].split(":")
 fp=pcb.FootprintLoad(str(LIB/"footprints"/(library+".pretty")),fpname)
 if not fp:raise RuntimeError("Missing footprint "+c["footprint"])
 fp.SetReference(c["ref"]);fp.SetValue(c["value"])
 fp.SetPath(pcb.KIID_PATH("/"+schid+"/"+c["uuid"])) if hasattr(pcb,"KIID_PATH") else None
 # Round Rev07 coordinates to integer nanometres; SWIG FromMM truncates some
 # decimal floats by 1 nm, while the DSN/SES round trip rounds them back.
 if VOLTAGE:fp.SetPosition(pcb.VECTOR2I(int(round(c['boardat'][0]*1000000)),int(round(c['boardat'][1]*1000000))))
 else:fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(c["boardat"][0]),pcb.FromMM(c["boardat"][1])))
 fp.SetOrientationDegrees(c["rot"])

 fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(1.0),pcb.FromMM(1.0)))
 fp.Reference().SetVisible(False)
 fp.Reference().SetTextThickness(pcb.FromMM(.12))
 fp.Value().SetVisible(False)
 if c["ref"] in ["J1","J2","J3"] or c["ref"].startswith("TP"):
  fp.SetAttributes(fp.GetAttributes() | pcb.FP_EXCLUDE_FROM_POS_FILES | pcb.FP_EXCLUDE_FROM_BOM)
 for pad in fp.Pads():
  net=c["nets"].get(pad.GetNumber())
  if net:pad.SetNet(nets[net])
 board.Add(fp)
 if c["ref"].startswith("J") and c["ref"]!="J4":fp.Flip(fp.GetPosition(),pcb.FLIP_DIRECTION_LEFT_RIGHT)
 # Trim only printed outlines to the narrow PCB; copper, Fab and courtyard stay native.
 for graphic in fp.GraphicalItems():
  if graphic.GetLayer() not in [pcb.F_SilkS,pcb.B_SilkS] or not isinstance(graphic,pcb.PCB_SHAPE):continue
  for getter,setter in [(graphic.GetStart,graphic.SetStart),(graphic.GetEnd,graphic.SetEnd)]:
   v=getter();lo=99.55 if c['ref']=='J4' else 98.86;hi=121.46
   v.x=max(pcb.FromMM(lo),min(pcb.FromMM(hi),v.x));setter(v)
 print("Placed",c["ref"],flush=True)
# Small edge recess aligns the GH mating face x=101.8-2.45=99.35 with Edge.Cuts.
# End lands remain at x=98.66 to support the original manufacturer's MP pads.
outline=[(98.66,95),(121.66,95),(121.66,136),(98.66,136),(98.66,133.5),(99.35,133.5),(99.35,114.1),(98.66,114.1)]
for (x1,y1),(x2,y2) in zip(outline,outline[1:]+outline[:1]):
 edge=pcb.PCB_SHAPE();edge.SetShape(pcb.SHAPE_T_SEGMENT);edge.SetStart(pcb.VECTOR2I(pcb.FromMM(x1),pcb.FromMM(y1)));edge.SetEnd(pcb.VECTOR2I(pcb.FromMM(x2),pcb.FromMM(y2)));edge.SetLayer(pcb.Edge_Cuts);edge.SetWidth(pcb.FromMM(.05));board.Add(edge)
def boardtext(text,x,y,size=.8,layer=pcb.F_SilkS):
 t=pcb.PCB_TEXT(board);t.SetText(text);t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));size=max(size,1.0);t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)));t.SetTextThickness(pcb.FromMM(.12));t.SetLayer(layer);board.Add(t)
if not VOLTAGE:boardtext("HMX R06",110.16,122,1)
if not VOLTAGE:boardtext("SMD UNTEN",110.16,130,1)
boardtext("180 DEG FLIP / V6 FIT UNVERIFIED",110,139,1,pcb.Cmts_User)
# Back silkscreen is readable from the header side after the physical flip.
def backtext(label,x,y,size=.8):
 t=pcb.PCB_TEXT(board);t.SetText(label);t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size)));t.SetTextThickness(pcb.FromMM(.12));t.SetLayer(pcb.B_SilkS);t.SetMirrored(True);board.Add(t)
backtext("HMX V6 R07 / OBEN" if VOLTAGE else "HMX V6 R06 / OBEN",110.16,95.9,.85)
if not VOLTAGE:backtext("GPIO",112,134.7,1)
backtext("TOUCH MODE",110.16,112.5,1)
backtext("1",115,123.7,1)
backtext("LCD RECHTS UNTEN",110.16,117,0.8)

backtext("1CS 2DC",110.16,102,1)
backtext("3BL 4SDA",110.16,104.5,1)
backtext("5SCL 6+3V3",110.16,107,1)
backtext("7+5V 8GND",110.16,109.5,1)
# Module outline in the SMD-view coordinate system; the two rows are reflected.
for xa,ya,xb,yb in [(98.66,94.3,121.66,94.3),(121.66,94.3,121.66,120.5),(121.66,120.5,98.66,120.5),(98.66,120.5,98.66,94.3)]:
 sh=pcb.PCB_SHAPE();sh.SetShape(pcb.SHAPE_T_SEGMENT);sh.SetStart(pcb.VECTOR2I(pcb.FromMM(xa),pcb.FromMM(ya)));sh.SetEnd(pcb.VECTOR2I(pcb.FromMM(xb),pcb.FromMM(yb)));sh.SetLayer(pcb.Dwgs_User);sh.SetWidth(pcb.FromMM(.1));board.Add(sh)
if VOLTAGE:
 for text in board.GetDrawings():
  if isinstance(text,pcb.PCB_TEXT) and text.GetLayer()==pcb.F_SilkS:text.SetLayer(pcb.F_Fab)
 for c in comps:
  if c['ref'] in ['TP5','TP6']:
   x,y=c['boardat'];backtext('+12V' if c['ref']=='TP5' else 'GND',x,y-1.7,.8)
 (OUT/'HeishaMon_V6_Touch_Adapter.kicad_dru').write_text((ROOT/'hardware/HeishaMon_V6_Touch_Adapter.kicad_dru').read_text().replace('track_width (min 0.2mm)','track_width (min 0.15mm)').replace('clearance (min 0.2mm)','clearance (min 0.15mm)').replace('hole_size (min 0.3mm)','hole_size (min 0.2mm)'))
pcb.SaveBoard(str(OUT/"HeishaMon_V6_Touch_Adapter.kicad_pcb"),board)
(OUT/"HeishaMon_V6_Touch_Adapter.kicad_pro").write_text(json.dumps({"meta":{"version":1},"board":{},"schematic":{},"net_settings":{"meta":{"version":3}}},indent=2))
(OUT/"fp-lib-table").write_text('(fp_lib_table (version 7))\n')
manifest=[{k:v for k,v in c.items() if k not in ["symbol","uuid"]} for c in comps]
(OUT/"netlist_design.json").write_text(json.dumps({"board_mm":[23,41],"layout_revision":"0.6","mounting":"F underside, B headers on top; physical flip about Y","mounted_transform":"x_mounted=220.32-x_smd; y_mounted=y_smd+2.5","side_header_policy":"23mm width; V6 2x5 location still unverified","layers":2,"status":"PLACEMENT; NOT ROUTED; MECHANICS UNVERIFIED","vendor_reference":"USR-ES1 2x6 rows; 2.54 pitch; row spacing 20.32mm","components":manifest},indent=2),encoding="utf8")
print("Generated",len(comps),"components;",len(netnames),"nets; KiCad schematic + placement draft")
if VOLTAGE:
 meta=json.loads((OUT/'netlist_design.json').read_text());meta['layout_revision']='0.7';meta['measurement']=measurement_spec
 (OUT/'netlist_design.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
