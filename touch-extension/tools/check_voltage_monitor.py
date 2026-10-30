"""Independent Rev07 netlist, pin assignment, geometry and divider verification.

Run after KiCad ERC/DRC and a kicadxml netlist export. Requires pcbnew.
"""
from pathlib import Path
import itertools,json,math,xml.etree.ElementTree as ET
import pcbnew as p
R=Path(__file__).resolve().parents[1];H=R/'hardware/Rev07'
design=json.loads((H/'netlist_design.json').read_text())
spec=json.loads((H/'voltage_monitor.json').read_text())
expected={};expected_schematic={}
for c in design['components']:
 for pin,net in c['nets'].items():
  if net:
   expected_schematic.setdefault(net,set()).add((c['ref'],pin))
   if c['footprint']:expected.setdefault(net,set()).add((c['ref'],pin))
tree=ET.parse(H/'KiCad_Netzliste.xml')
actual={n.attrib['name'].lstrip('/'):{(v.attrib['ref'],v.attrib['pin']) for v in n.findall('node')} for n in tree.findall('./nets/net') if not n.attrib['name'].startswith('unconnected-')}
assert expected_schematic==actual,[(n,expected_schematic.get(n,set())^actual.get(n,set())) for n in expected_schematic.keys()|actual.keys() if expected_schematic.get(n)!=actual.get(n)]
b=p.LoadBoard(str(H/'HeishaMon_V6_Touch_Adapter.kicad_pcb'))
boardnets={}
for fp in b.GetFootprints():
 for pad in fp.Pads():
  if pad.GetNetCode():boardnets.setdefault(pad.GetNetname(),set()).add((fp.GetReference(),pad.GetNumber()))
assert boardnets==expected,'Schematic and actual PCB pad nets differ'
u2=next(c for c in design['components'] if c['ref']=='U2')['nets']
assert u2=={'1':'GND','2':None,'3':'GND','4':'ADC_A0','5':'ADC_A1','6':'ADC_A2','7':'ADC_A3','8':'+3V3_EXT','9':'I2C_SDA','10':'I2C_SCL'}
u3=next(c for c in design['components'] if c['ref']=='U3')['nets']
for i,(s,d) in enumerate([(2,3),(5,6),(9,8),(12,11)]):assert u3[str(s)]=='DIV'+str(i) and u3[str(d)]=='ISO'+str(i)
assert all(u3[str(pin)]=='ADC_ENABLE' for pin in [1,4,10,13])
u4=next(c for c in design['components'] if c['ref']=='U4')['nets']
assert u4=={'1':'GND','2':'ADC_ENABLE','3':'+3V3_EXT'}
assert ('U1','12') in actual['ADC_ENABLE']
old=p.LoadBoard(str(R/'hardware/HeishaMon_V6_Touch_Adapter.kicad_pcb'))
for ref in ['J1','J2','J3','J4']:
 a=next(f for f in old.GetFootprints() if f.GetReference()==ref);c=next(f for f in b.GetFootprints() if f.GetReference()==ref)
 assert a.GetPosition()==c.GetPosition() and a.GetLayer()==c.GetLayer() and a.GetOrientationDegrees()==c.GetOrientationDegrees(),ref+' mating geometry changed'
assert b.GetCopperLayerCount()==2
bb=b.GetBoardEdgesBoundingBox()
assert abs(p.ToMM(bb.GetWidth())-23)<.1 and abs(p.ToMM(bb.GetHeight())-41)<.1
erc=json.loads((H/'ERC.json').read_text());drc=json.loads((H/'DRC.json').read_text())
assert not [v for s in erc['sheets'] for v in s['violations']], 'ERC is not clean'
assert not drc['violations'] and not drc['unconnected_items'],'DRC / connectivity is not clean'
nominal=[3.3,3.3,5,12];results=[]
for c,v in zip(spec['channels'],nominal):
 top=c['r_top_ohm'];bottom=c['r_bottom_ohm'];series=c['r_series_ohm'];load=c['r_pulldown_ohm']
 def gain(t,b,s,l,ron=2):return b/(t+b)*l/(l+s+ron+t*b/(t+b))
 g=gain(top,bottom,series,load)
 worst=max(gain(top*a,bottom*z,series*q,load*r,ron=0) for a,z,q,r in itertools.product([.999,1.001],repeat=4))
 max_v=worst*c['max_source_v']
 assert max_v<2.9,'Input exceeds minimum enabled supply margin'
 assert max_v<3.6,'TMUX powered-off input rating exceeded'
 # Full-temperature powered-off specification: up to 2 uA (TMUX1511,
 # electrical characteristics). Conservatively assign all leakage to ADC.
 # The old 1-Mohm discharge path allowed 2 V and did not meet this bound.
 leakage_bound_v=2e-6*load*1.001
 assert leakage_bound_v < .3,'Powered-off ADC voltage not bounded below GND+0.3 V'
 unloaded_divider_v=c['max_source_v']*(bottom*1.001)/(top*.999+bottom*1.001)
 assert unloaded_divider_v < 3.6,'Open-switch source input exceeds powered-off rating'
 # Conservative top resistor bound: downstream load can lower the divider
 # node; Vsource^2/Rtop is safe even for a shorted lower branch.
 max_power=c['max_source_v']**2/(top*.999)
 assert max_power<.05
 results.append(dict(channel=c['channel'],rail=c['rail'],nominal_source_v=v,nominal_adc_v=v*g,source_per_adc_v=1/g,worst_adc_v=max_v,max_top_resistor_w=max_power,
  powered_off_adc_leakage_bound_v=leakage_bound_v,powered_off_switch_source_max_v=unloaded_divider_v,
  nominal_source_current_ua=v/(top+1/(1/bottom+1/(load+series+2)))*1e6,
  filter_time_constant_ms=(top*bottom/(top+bottom))*100e-9*1000,
  notes='Static leakage calculation is conservative; power-transition transients, ADC input impedance and real calibration still require hardware verification'))
report=dict(revision='0.7',board_mm=[23,41],layers=2,nets_verified=len(expected),pcb_components=len(list(b.GetFootprints())),erc_violations=0,drc_violations=0,unconnected_items=0,
 tracks=sum(not isinstance(x,p.PCB_VIA) for x in b.GetTracks()),vias=sum(isinstance(x,p.PCB_VIA) for x in b.GetTracks()),mating_connectors_unchanged=True,hardware_tested=False,manufacturing_release=False,channels=results)
(H/'validation_summary.json').write_text(json.dumps(report,indent=2)+'\n')
design['status']='ROUTED PROTOTYPE; ERC/DRC clean; hardware and manufacturing review pending'
(H/'netlist_design.json').write_text(json.dumps(design,indent=2)+'\n')
print(json.dumps(report))
