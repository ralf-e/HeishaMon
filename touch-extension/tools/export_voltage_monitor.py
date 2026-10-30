"""Export Rev07 prototype manufacturing files only after independent clean checks.

No upload/order. CPL rotations for changed IC packages remain review candidates.
"""
from pathlib import Path
import collections,csv,json,subprocess,zipfile,hashlib
import pcbnew as p
R=Path(__file__).resolve().parents[1];H=R/'hardware/Rev07';O=R/'manufacturing/JLCPCB/Rev07';O.mkdir(parents=True,exist_ok=True)
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
v=json.loads((H/'validation_summary.json').read_text())
assert v['drc_violations']==v['erc_violations']==v['unconnected_items']==0
b=p.LoadBoard(str(H/'HeishaMon_V6_Touch_Adapter.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
old=json.loads((R/'hardware/parts_catalogue.json').read_text())
parts=[]
for part in old['parts']:
 if 'U1' in part['refs']:continue
 q=dict(part);q['stock_checked_on']=old['checked_on'];q['stock_status']='historical; recheck before order';parts.append(q)
def add(refs,mpn,maker,code,value,rotation=0):
 parts.append(dict(refs=refs,mpn=mpn,maker=maker,code=code,value=value,rotation=rotation,stock=None,orderable=None,stock_status='not reverified for assembly; recheck before order',url='https://www.lcsc.com/product-detail/'+code+'.html'))
add(['U1'],'MCP23008-E/SS','Microchip','C148011','MCP23008 SSOP20',270)
add(['U2'],'ADS1115IDGSR','TI','C37593','ADS1115 VSSOP10',270)
add(['U3'],'TMUX1511PWR','TI','C2866750','TMUX1511 TSSOP14',270)
add(['U4'],'TLV809EA29DCKR','TI','C2861006','2.93V supervisor SC70',180)
for value,refs,mpn,code in [
 ('10k 0.1%',[12,13,16,17,21,25],'RT0603BRD0710KL','C95204'),
 ('20k 0.1%',[20],'RT0603BRD0720KL','C723637'),
 ('68k 0.1%',[24],'RT0603BRD0768KL','C705793'),
 ('1k 0.1%',[14,18,22,26],'RT0603BRD071KL','C110776'),
 ('100k 0.1%',[15,19,23,27],'RT0603BRD07100KL','C122538')]:
 add(['R'+str(x) for x in refs],mpn,'Yageo',code,value)
add(['C'+str(x) for x in range(4,11)],'CL10B104KB8NNNC','Samsung','C1591','100n X7R 50V 10%')
stock=json.loads((H/'stock_snapshot.json').read_text(encoding='utf-8'))
stock_by_code={q['code']:q for q in stock['parts']}
orientation=json.loads((H/'assembly_orientation_audit.json').read_text())
orientation_by_ref={q['ref']:q for q in orientation['parts']}
for part in parts:
 s=stock_by_code[part['code']]
 assert s['mpn']==part['mpn'] and s['component_status']=='yes' and s['assembly_process']=='SMT'
 assert s['available_order_quantity'] >= len(part['refs'])
 part.update(stock=s['warehouse_stock'],orderable=s['available_order_quantity'],stock_checked_on=s['checked_at'],
  stock_status='available at snapshot; not reserved',stock_source=s['source_url'])
 if part['refs'][0] in orientation_by_ref:
  a=orientation_by_ref[part['refs'][0]]
  assert part['rotation']==a['correction_degrees'],part['refs']
  part['rotation_basis']='Exact numbered supplier-pad comparison; order-specific placement preview pending'
lookup={ref:part for part in parts for ref in part['refs']}
expected={ref for ref in fps if ref not in ['J1','J2','J3'] and not ref.startswith('TP')}
assert set(lookup)==expected and len(expected)==42,(set(lookup)^expected,len(expected))
(H/'parts_catalogue.json').write_text(json.dumps(dict(revision='0.7',identities_checked_on='2026-10-30',stock_snapshot_verified=True,stock_recheck_required_at_order=True,rotation_library_verified=True,rotation_review_required=['U1','U2','U3','U4','J4'],parts=parts),indent=2)+'\n')
def write(name,header,rows):
 with (O/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(rows)
write('BOM_JLCPCB_REVIEW.csv',['Comment','Designator','Footprint','LCSC Part #'],[(part['value'],','.join(part['refs']),str(fps[part['refs'][0]].GetFPID().GetLibItemName()),part['code']) for part in parts])
write('BOM_Detail.csv',['References','MPN','Manufacturer','LCSC','Specification','Orderable at snapshot','Checked UTC','Availability'],[(','.join(q['refs']),q['mpn'],q['maker'],q['code'],q['value'],q['orderable'],q['stock_checked_on'],q['stock_status']) for q in parts])
origin=b.GetDesignSettings().GetAuxOrigin()
rows=[]
for ref,q in sorted(lookup.items()):
 fp=fps[ref];assert fp.GetLayer()==p.F_Cu
 rows.append((ref,f'{p.ToMM(fp.GetPosition().x-origin.x):.4f}',f'{p.ToMM(origin.y-fp.GetPosition().y):.4f}','Top',f'{(fp.GetOrientationDegrees()+q["rotation"])%360:.1f}'))
write('CPL_JLCPCB_REVIEW.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],rows)
write('Rotation_REVIEW.csv',['References','Correction from KiCad','Review'],[(','.join(q['refs']),q['rotation'],'Numbered supplier pads verified; order-specific preview/centering pending' if q['refs'][0] in orientation_by_ref else 'Nonpolar resistor/MLCC; 180-degree equivalence') for q in parts])
write('Manual_parts.csv',['References','Description'],[['J1,J2','Existing long stack-through 1x6 contacts; unchanged positions'],['J3','Existing 2x4 GPIO header; unchanged position'],['TP5','One extra +12V measurement wire; existing V6/adapter connector GND is the reference; not a power input'],['TP6','Optional GND solder/test point; no extra ground wire needed when V6 and adapter already share GND'],['TP1,TP2,TP3,TP4','Bare measurement pads; do not assemble a component']])
def run(*args):
 result=subprocess.run([CLI,*map(str,args)],capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 print(result.stdout.strip(),flush=True)
G=O/'gerber';G.mkdir(exist_ok=True)
run('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts','--use-drill-file-origin','--disable-aperture-macros','--output',str(G)+'/',H/'HeishaMon_V6_Touch_Adapter.kicad_pcb')
run('pcb','export','drill','--drill-origin','plot','--excellon-units','mm','--excellon-separate-th','--generate-map','--generate-report','--report-path',O/'drill_report.txt','--output',str(G)+'/',H/'HeishaMon_V6_Touch_Adapter.kicad_pcb')
with zipfile.ZipFile(O/'Gerber_HeishaMon_V6_Rev07_PROTOTYPE.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in G.iterdir():
  if f.is_file():z.write(f,f.name)
(O/'README.md').write_text('''# Rev.0.7 - Prototypdaten, keine Bestellfreigabe

23 x 41 mm, 2 Kupferlagen, 1,6 mm, 1 oz. SMD auf Top/F (eingebaut unten), Stiftleisten manuell auf B. Gegenueber Rev.0.6 neuer ADC, Schutzschalter, Supervisor und MCP23008 im SSOP-20-Gehaeuse.

42 SMD-Referenzen in BOM und CPL, drei manuelle Stiftleisten sowie sechs unbestueckte Mess-/Loetpads. Keine Dateien mit Rev06 mischen.

Gepruefte Designregeln: Leiterbahnen mindestens 0,15 mm, Kupferabstand mindestens 0,15 mm, Vias 0,50 mm mit 0,20-mm-Bohrung, Kantenabstand mindestens 0,30 mm. Diese Werte muessen zur bestellten Kupferstaerke und Fertigungsoption passen.

Alle 18 SMD-Typen sind im direkten JLCPCB-Abgleich vom 30.10.2026 verfuegbar; die zuvor fraglichen Praezisionswiderstaende muessen nicht ersetzt werden. Engpass U4: 20 bestellbare Stueck, ohne Reservierung oder Beruecksichtigung auftragsbezogener Zuschlaege. Aktuelle Zahlen und UTC-Zeit stehen in BOM_Detail.csv und hardware/Rev07/stock_snapshot.json. Vor tatsaechlicher Bestellung erneut abgleichen.

Die Pin-1-/Rotationspruefung anhand aller nummerierten Lieferanten-Pads ist bestanden: U1/U2/U3 CPL270, U4 korrigiert auf CPL180, J4 CPL270. Quelle: JLCEDA/EasyEDA Official Library (https://lceda.cn/ und https://easyeda.com/). Widerstaende/MLCC sind ungepolt. Eine ausfuehrliche Pruefung und Grafik liegen in hardware/Rev07/Bestellpruefung.md und Bestueckungsrotationen.svg.

Die mit REVIEW benannten BOM/CPL behalten ihren Namen: Das auftragsbezogene Hersteller-Preview muss die tatsaechlichen Maschinenmodelle, Pin 1 und die Zentrierung bestaetigen. Insbesondere J4 hat zwischen den Bibliotheken unterschiedliche Bezugspunkte; kein automatischer Positionsversatz wurde angewendet. Ein Bibliotheksvergleich ersetzt diesen letzten Schritt nicht.

TP5 ist nur fuer positive 12-V-Messung bis zum vorgesehenen Bereich 18 V. Bei gemeinsamer V6-/Adaptermasse genuegt eine zusaetzliche Leitung vom 12-V-Abgriff zu TP5; GND besteht bereits ueber die Steckkontakte. TP6 ist ein optionaler GND-Loet-/Pruefpunkt, keine zusaetzlich erforderliche Masseleitung. Keine Einspeisung, keine 24 V. V6-Kontakte, Stromreserve und reale Passform sind noch ungetestet.

Die Firmware dev.7 liest den ADC noch nicht aus. Rev06-Software bleibt getrennt erhaeltlich.

Hersteller-Fertigungsgrenzen: https://jlcpcb.com/capabilities/pcb-capabilities/
''',encoding='utf-8')
files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in O.iterdir() if f.is_file() and f.name!='export_validation.json'}
(O/'export_validation.json').write_text(json.dumps(dict(revision='0.7',smd_references=len(lookup),bom_cpl_equal=True,hardware_tested=False,manufacturing_release=False,rotation_library_verified=True,rotation_review_required=True,stock_snapshot_verified=True,stock_recheck_required_at_order=True,sha256=files),indent=2)+'\n')
print('Rev07 prototype exports complete')
