"""Export a single-board JLCPCB prototype package with SMD-only BOM/CPL.
Run with KiCad's Python. Does not upload or place an order.
"""
from pathlib import Path
import json,csv,subprocess,zipfile,hashlib,re,sys
import pcbnew as p
R=Path(__file__).resolve().parents[1];H=R/'hardware';O=R/'manufacturing/JLCPCB/Rev06';G=O/'gerber';G.mkdir(parents=True,exist_ok=True)
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe');boardfile=H/'HeishaMon_V6_Touch_Adapter.kicad_pcb'
drc=json.loads((H/'DRC.json').read_text());erc=json.loads((H/'ERC.json').read_text())
assert not drc['violations'] and not drc['unconnected_items'],'DRC must be clean before manufacturing export'
assert not any(s.get('violations') for s in erc.get('sheets',[])),'ERC must be clean'
cat=json.loads((H/'parts_catalogue.json').read_text(encoding='utf8'));board=p.LoadBoard(str(boardfile));mm=p.ToMM
fps={fp.GetReference():fp for fp in board.GetFootprints()};lookup={ref:part for part in cat['parts'] for ref in part['refs']}
assert set(lookup)=={ref for ref in fps if ref.startswith(('R','C')) or ref in ['U1','J4']}
assert len(lookup)==16 and not any(ref in lookup for ref in ['J1','J2','J3','J5','R4'])
origin=board.GetDesignSettings().GetAuxOrigin();assert abs(mm(origin.x)-98.66)<.001 and abs(mm(origin.y)-136)<.001

def run(*args):
 r=subprocess.run([str(CLI),*map(str,args)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 print(r.stdout.strip(),flush=True)
if '--placement-only' not in sys.argv:
 run('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts','--use-drill-file-origin','--disable-aperture-macros','--output',str(G)+ '/',boardfile)
 run('pcb','export','drill','--drill-origin','plot','--excellon-units','mm','--excellon-separate-th','--generate-map','--generate-report','--report-path',O/'drill_report.txt','--output',str(G)+'/',boardfile)
run('pcb','export','pos','--side','front','--format','csv','--units','mm','--use-drill-file-origin','--smd-only','--exclude-fp-th','--exclude-dnp','--output',O/'KiCad_SMD_positions.csv',boardfile)
source=list(csv.DictReader((O/'KiCad_SMD_positions.csv').open(encoding='utf-8-sig')))
assert {row['Ref'] for row in source}==set(lookup),[(r['Ref'],r) for r in source]

def write(name,headers,rows):
 with (O/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(headers);w.writerows(rows)

rows=[];audit=[]
for row in source:
 ref=row['Ref'];fp=fps[ref];part=lookup[ref];x=float(row['PosX']);y=float(row['PosY']);rotation=(float(row['Rot'])+part['rotation'])%360
 assert fp.GetLayer()==p.F_Cu and row['Side'].lower() in ['top','front'],row
 assert abs(x-mm(fp.GetPosition().x-origin.x))<.0001 and abs(y-mm(origin.y-fp.GetPosition().y))<.0001,row
 assert 0<=x<=23 and 0<=y<=41
 if ref=='J4':
  assert part['code']=='C265027' and part['rotation']==0 and abs(rotation-270)<.001,'J4 must use C265027-specific CPL270'
 rows.append([ref,f'{x:.4f}',f'{y:.4f}','Top',f'{rotation:.1f}'])
 audit.append([ref,row['Rot'],part['rotation'],rotation,'SOIC rule +270deg (Fabrication Toolkit)' if ref=='U1' else 'C265027-specific: no generic +180; CPL270 after user JLC 3D feedback; recheck preview' if ref=='J4' else 'No default rotation correction'])
write('CPL_JLCPCB.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],rows)
write('Rotation_Audit.csv',['Designator','KiCad rotation','JLC correction','JLC rotation','Basis'],audit)
pack=lambda part:'SOIC-18-300mil' if part['code']=='C92253' else 'JST_GH_1x15_P1.25_SideEntry' if part['code']=='C265027' else '0805'
write('BOM_JLCPCB.csv',['Comment','Designator','Footprint','LCSC Part #'],[[part['value'],','.join(part['refs']),pack(part),part['code']] for part in cat['parts']])
write('BOM_Detail.csv',['Designators','Quantity','Value/Specification','Manufacturer','MPN','JLCPCB Part','URL'],[[','.join(part['refs']),len(part['refs']),part['value'],part['maker'],part['mpn'],part['code'],part['url']] for part in cat['parts']])
write('Manual_Parts_NOT_IN_ASSEMBLY.csv',['Designator','Quantity','Part','Side','Note'],[['J1',1,'Long stack-through 1x6 socket/header','B','Manual; exact tail and stack height must match V6/W5500'],['J2',1,'Long stack-through 1x6 socket/header','B','Manual; 20.32 mm row spacing'],['J3',1,'2x4 2.54 mm pin header','B','Manual; pin 1 is square pad']])
write('Availability_2026-10-25.csv',['JLCPCB Part','MPN','Stock observed','Orderable observed','Checked','URL'],[[part['code'],part['mpn'],part['stock'],part['orderable'] if part['orderable'] is not None else 'not shown',cat['checked_on'],part['url']] for part in cat['parts']])
write('Alternatives.csv',['Replaces','Alternative','MPN','Stock observed','Comment','URL'],[[part['replaces'],part['code'],part['mpn'],part['stock'],part['note'],part['url']] for part in cat['alternatives']])
# Independent BOM/CPL consistency and manual-parts exclusion.
bom=list(csv.DictReader((O/'BOM_JLCPCB.csv').open(encoding='utf-8-sig')));cpl=list(csv.DictReader((O/'CPL_JLCPCB.csv').open(encoding='utf-8-sig')))
assert {ref for row in bom for ref in row['Designator'].split(',')}=={row['Designator'] for row in cpl}==set(lookup)
assert all(row['Layer']=='Top' for row in cpl)
manual_pads=[pad for ref in ['J1','J2','J3'] for pad in fps[ref].Pads() if pad.GetDrillSize().x>0]
assert len(manual_pads)==20,'Manual header holes must remain in PCB/drill data'
# Verify the exported drill coordinates, not just the PCB's drill-pad count.
pthfile=next(f for f in G.glob('*PTH.drl') if 'NPTH' not in f.name)
holes=[tuple(map(float,xy)) for xy in re.findall(r'^X([-0-9.]+)Y([-0-9.]+)$',pthfile.read_text(),re.M)]
manual_holes=[]
for ref in ['J1','J2','J3']:
 for pad in fps[ref].Pads():
  x=mm(pad.GetPosition().x-origin.x);y=mm(origin.y-pad.GetPosition().y)
  assert any(abs(x-u)<.001 and abs(y-v)<.001 for u,v in holes),(ref,pad.GetNumber(),'drill missing')
  manual_holes.append([ref,pad.GetNumber(),f'{x:.4f}',f'{y:.4f}','present'])
write('Manual_Header_Holes_Verified.csv',['Reference','Pin','X mm','Y mm','PTH export'],manual_holes)
pins=[]
for ref in ['U1','J4']:
 pad=next(pad for pad in fps[ref].Pads() if pad.GetNumber()=='1')
 pins.append([ref,f'{mm(pad.GetPosition().x-origin.x):.4f}',f'{mm(origin.y-pad.GetPosition().y):.4f}','Compare this physical pin 1 against JLC preview'])
write('Pin1_Reference.csv',['Reference','Pin1 X mm','Pin1 Y mm','Check'],pins)
gerbers=[f for f in G.iterdir() if f.suffix.lower() in ['.gbr','.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gm1','.gko','.gbrjob','.drl']]
assert any('Edge_Cuts' in f.name or f.suffix in ['.gm1','.gko'] for f in gerbers),'Missing board outline'
assert len(gerbers)>=10,[f.name for f in G.iterdir()]
assert any('PTH' in f.name and f.suffix=='.drl' for f in gerbers)
with zipfile.ZipFile(O/'Gerber_HeishaMon_V6_Rev06.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in gerbers:z.write(f,f.name)
report=dict(board_mm=[23,41],layers=2,thickness_mm=1.6,assembly_design_side='Top/F',mounted_side='underside after 180deg flip',smd_placements=len(cpl),bom_groups=len(bom),manual_headers=['J1','J2','J3'],manual_header_drill_holes=len(manual_pads),exported_manual_holes_verified=True,bom_cpl_designators_match=True,gerber_origin='lower left: KiCad (98.66,136), exported (0,0)',rotation_source='Fabrication Toolkit transformations.csv blob 40878ad04b8f0ac427e48085c2440ea26bbd99a9; SOIC +270deg; C265027 specific offset 0deg (generic JST_GH_SM rule overridden after user 3D review)',pcb_sha256=hashlib.sha256(boardfile.read_bytes()).hexdigest(),mechanical_verification=False,uploaded_to_manufacturer=False)
(O/'export_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
