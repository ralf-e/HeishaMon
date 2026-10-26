"""Export complete connection matrix; independently check the KiCad netlist."""
from pathlib import Path
import json,re,collections,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3,landscape
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/"hardware"
# No pcbnew dependency here; parse only the KiCad netlist.
def parse(s):
 toks=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s);st=[]
 for t in toks:
  if t=="(":
   x=[]
   if st:st[-1].append(x)
   st.append(x)
  elif t==")":
   x=st.pop()
   if not st:return x
  else:st[-1].append(json.loads(t) if t.startswith('"') else t)
def c(x,k):return next((v for v in x if isinstance(v,list) and v and v[0]==k),None)
design=json.loads((HW/"netlist_design.json").read_text())
expected=collections.defaultdict(set);nc=[]
for comp in design["components"]:
 for pin,net in comp["nets"].items():
  if net:expected[net].add((comp["ref"],pin))
  else:nc.append(comp["ref"]+"."+pin)
netroot=c(parse((HW/"KiCad_Netzliste.net").read_text(encoding="utf8")),"nets")
actual={}
for node in netroot[1:]:
 if not isinstance(node,list) or node[0]!="net":continue
 name=c(node,"name")[1].lstrip("/")
 if name.startswith("unconnected-"):continue
 actual[name]={tuple([c(v,"ref")[1],c(v,"pin")[1]]) for v in node if isinstance(v,list) and v and v[0]=="node" and not c(v,"ref")[1].startswith("#")}
assert set(expected)==set(actual),(set(expected)-set(actual),set(actual)-set(expected))
board_refs={comp["ref"] for comp in design["components"] if comp["footprint"]}
for net,pins in expected.items():
 boardpins={pair for pair in pins if pair[0] in board_refs}
 assert boardpins==actual[net],(net,boardpins,actual[net])
erc=json.loads((HW/"ERC.json").read_text());violations=[v for sheet in erc.get("sheets",[]) for v in sheet.get("violations",[])]
assert not violations,violations
drc=json.loads((HW/"DRC.json").read_text())
assert not drc.get("violations"),drc["violations"]
unrouted=len(drc.get("unconnected_items",[]))
assert unrouted==0, "PCB still contains open connections"
audit=json.loads((HW/"pcb_audit.json").read_text())
boardactual=collections.defaultdict(set)
for pad in audit["pads"]:boardactual[pad["net"]].add((pad["ref"],pad["pin"]))
for net,pins in expected.items():
 assert boardactual[net]=={pair for pair in pins if pair[0] in board_refs}, (net,"PCB mismatch")
# Independently verify the physical 180-degree mounting transform against V6 reference.
for ref,expected_x in [('J1',100.0),('J2',120.32)]:
 for pad in audit['pads']:
  if pad['ref']!=ref:continue
  assert pad['side']=='B', (ref,'not on header side')
  assert abs((220.32-pad['x'])-expected_x)<.001,(ref,'mounted column mirrored incorrectly')
  assert abs(pad['y']-(97.5+(int(pad['pin'])-1)*2.54))<.001,(ref,'mounted pin row reversed')
for pad in audit['pads']:
 if pad['ref'] in ['J3']:assert pad['side']=='B'
 if pad['ref'] in ['J4','U1'] or pad['ref'].startswith(('R','C')):assert pad['side']=='F'
# Revision 05 connector placement, verified in board coordinates.
j4=[p for p in audit['pads'] if p['ref']=='J4'];j3=[p for p in audit['pads'] if p['ref']=='J3']
assert all(p['side']=='F' and p['x']<105 for p in j4),'GH must be on left F edge'
assert all(p['side']=='B' and p['x']>117 and p['y']>=125 for p in j3),'GPIO must be on opposite B side at lower end'
g=audit['connector_geometry']
assert g['footprint']=='JST_GH_SM15B-GHS-TB_1x15-1MP_P1.25mm_Horizontal' and g['rotation']%360==270
assert abs(g['mating_face_x']-99.35)<.001
assert any(abs(a[0]-g['mating_face_x'])<.001 and abs(b[0]-g['mating_face_x'])<.001 and {round(a[1],1),round(b[1],1)}=={114.1,133.5} for a,b in g['edge_segments']),'GH mating face is not on edge recess'
report={"nets_verified":len(expected),"components":len(design["components"]),"erc_violations":0,
"placement_clearance_violations":0,"unconnected_groups":unrouted,"routing_complete":True,"tracks":audit["tracks"],"vias":audit["vias"],"ground_zones":audit["zones"],"layout_revision":"0.6","manufacturing_release":False,"mounting_transform_verified":True,"board_mm":[23,41]}
(HW/"validation_summary.json").write_text(json.dumps(report,indent=2))
# Complete electrical wiring matrix as a single A3 page.
font="Helvetica";body=ParagraphStyle("body",fontName=font,fontSize=10,leading=14)
head=ParagraphStyle("head",fontName="Helvetica-Bold",fontSize=19,leading=24,spaceAfter=12)
small=ParagraphStyle("small",fontName=font,fontSize=9,leading=12,spaceAfter=8)
story=[Paragraph("Gesamtverdrahtungsplan - alle Verbindungen",head),
 Paragraph("HeishaMon V6 Touch Rev.0.6 | 21 Netze | J1/J2: USR-ES1-Herstellerreferenz, nicht am V6-Board bestaetigt.",small)]
rows=[["Netz","Alle elektrisch verbundenen Anschlusspunkte (Ref.Pin)"]]
for net,pins in sorted(expected.items()):
 rows.append([Paragraph(html.escape(net),body),Paragraph(", ".join(ref+"."+pin for ref,pin in sorted(pins)),body)])
t=Table(rows,colWidths=[155,950],repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dcecf2")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),11),("GRID",(0,0),(-1,-1),.3,colors.HexColor("#a8bac5")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
story+=[t,Spacer(1,12),Paragraph("Bewusst unbeschaltet: "+", ".join(nc)+". J6/J7 stellen die externen Gegenkontakte am W5500-Modul dar; keine weiteren PCB-Stecker.",small),
Paragraph("J3: 1=GPIO33/CS; 2=GPIO34/DC; 3=GPIO35/BL; 4=GPIO36/SDA; 5=GPIO37/SCL; 6=3V3_V6; 7=5V_V6; 8=GND. Dies ist die neue Adapterbelegung.",small),
Paragraph("J1: GND, GND, MOSI(GPIO11), SCK(GPIO12), ETH_CS(GPIO10), ETH_IRQ(GPIO15). J2: GND, 3V3, 3V3, NC, ETH_RST(GPIO14), MISO(GPIO13).",small),
Paragraph("R0: 0-Ohm-Messbruecke. 5V ist nur Reserve; keine Verbindung zu 3V3_EXT. Kein zusaetzlicher Regler. Alle Punkte je Zeile sind verbunden; verschiedene Zeilen sind getrennt.",small)]
SimpleDocTemplate(str(HW/"Gesamtverdrahtung_rev06.pdf"),pagesize=landscape(A3),leftMargin=40,rightMargin=40,topMargin=30,bottomMargin=25).build(story)
# Include the same complete matrix in the Markdown manual.
md=["## Anhang A. Vollständige Verbindungsliste","",
"Jeder Eintrag bezeichnet **Bauteilreferenz.Kontaktnummer** des neuen Adapters. Alle Punkte einer Zeile sind elektrisch verbunden. Die Netzliste wurde unabhängig für die Platinenbauteile mit dem KiCad-Export abgeglichen. J6/J7 zeigen die externen Gegenkontakte des W5500-Moduls; diese erhalten keinen zusätzlichen PCB-Footprint.","",
"| Netz | Sämtliche Anschlusspunkte |","| --- | --- |"]
md += ["| "+net+" | "+", ".join(ref+"."+pin for ref,pin in sorted(pins))+" |" for net,pins in sorted(expected.items())]
md+=["","Bewusst unbeschaltet: "+", ".join(nc)+". J6/J7 liegen extern am Ethernetmodul.","",
"**Prüfstand:** ERC 0 Verstöße; Geroutete Platine 0 DRC-Verstöße; "+str(unrouted)+" offene Verbindungen. Mechanische Passung und Hardwaretest stehen aus; keine Fertigungsfreigabe."]
(ROOT/"docs/connection_matrix.md").write_text("\n".join(md)+"\n",encoding="utf8")
print(json.dumps(report))
