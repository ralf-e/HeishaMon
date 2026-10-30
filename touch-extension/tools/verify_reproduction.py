"""Verify that source generation + final copper reproduces the delivered PCB audit.
Run with KiCad Python. Never modifies the delivered hardware files.
"""
from pathlib import Path
import tempfile,shutil,subprocess,json,sys
R=Path(__file__).resolve().parents[1];tmp=R/'tmp';tmp.mkdir(exist_ok=True)
if '--voltage' in sys.argv:
 import pcbnew as pcb
 with tempfile.TemporaryDirectory(prefix='voltage-reproduction-',dir=tmp) as directory:
  t=Path(directory).resolve();assert t.is_relative_to(tmp.resolve())
  (t/'tools').mkdir();(t/'hardware/Rev07').mkdir(parents=True)
  for name in ['design_adapter.py','voltage_monitor_design.py','route_voltage_monitor.py']:
   shutil.copyfile(R/'tools'/name,t/'tools'/name)
  shutil.copyfile(R/'hardware/HeishaMon_V6_Touch_Adapter.kicad_dru',t/'hardware/HeishaMon_V6_Touch_Adapter.kicad_dru')
  for name in ['component_placement.json','routed_copper.json']:
   shutil.copyfile(R/'hardware/Rev07'/name,t/'hardware/Rev07'/name)
  for name,args in [('design_adapter.py',['--voltage']),('route_voltage_monitor.py',['restore'])]:
   result=subprocess.run([sys.executable,str(t/'tools'/name),*args],capture_output=True,text=True)
   assert result.returncode==0,result.stdout+result.stderr
  def geometry(board):
   pads=sorted((fp.GetReference(),pad.GetNumber(),pad.GetNetname(),pad.GetPosition().x,pad.GetPosition().y,pad.GetSize().x,pad.GetSize().y,fp.GetLayer()) for fp in board.GetFootprints() for pad in fp.Pads())
   copper=[]
   for track in board.GetTracks():
    if isinstance(track,pcb.PCB_VIA):
     copper.append(('via',track.GetNetname(),track.GetPosition().x,track.GetPosition().y,track.GetWidth(pcb.F_Cu),track.GetDrillValue()))
    else:
     a=(track.GetStart().x,track.GetStart().y);b=(track.GetEnd().x,track.GetEnd().y)
     copper.append(('track',track.GetNetname(),track.GetLayer(),*min(a,b),*max(a,b),track.GetWidth()))
   return pads,sorted(copper),len(list(board.Zones()))
  filename='HeishaMon_V6_Touch_Adapter.kicad_pcb'
  expected_geometry=geometry(pcb.LoadBoard(str(R/'hardware/Rev07'/filename)))
  actual_geometry=geometry(pcb.LoadBoard(str(t/'hardware/Rev07'/filename)))
  if expected_geometry!=actual_geometry:
   for kind,expected_items,actual_items in zip(['pads','copper'],expected_geometry[:2],actual_geometry[:2]):
    print(kind,'missing',list(set(expected_items)-set(actual_items))[:8],'extra',list(set(actual_items)-set(expected_items))[:8],flush=True)
   raise AssertionError('Rev07 pad or copper geometry changed')
  report=t/'DRC.json'
  result=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--output',str(report),str(t/'hardware/Rev07'/filename)],capture_output=True,text=True)
  assert result.returncode==0,result.stdout+result.stderr
  drc=json.loads(report.read_text());assert not drc['violations'] and not drc['unconnected_items'],drc
 print('Rev07 reproduction OK: source + final copper; exact pads/tracks/vias; DRC 0 and 0 unconnected')
 raise SystemExit(0)
with tempfile.TemporaryDirectory(prefix='reproduction-',dir=tmp) as d:
 t=Path(d).resolve();assert t.is_relative_to(tmp.resolve())
 (t/'tools').mkdir();(t/'tmp').mkdir()
 for name in ['design_adapter.py','pcb_io.py']:shutil.copyfile(R/'tools'/name,t/'tools'/name)
 shutil.copyfile(R/'hardware/routed_copper.json',t/'tmp/routed_copper.json')
 for name,args in [('design_adapter.py',[]),('pcb_io.py',['import'])]:
  result=subprocess.run([sys.executable,str(t/'tools'/name),*args],capture_output=True,text=True,check=True)
 expected=json.loads((R/'hardware/pcb_audit.json').read_text());actual=json.loads((t/'hardware/pcb_audit.json').read_text())
 def pins(a):return sorted((p['ref'],p['pin'],p['net'],round(p['x'],6),round(p['y'],6),p['side']) for p in a['pads'])
 assert pins(expected)==pins(actual),'Pad/net/side or position changed during reproduction'
 for field in ['tracks','vias','zones','connector_geometry']:assert expected[field]==actual[field],field
 print('PCB reproduction OK: pads, nets, sides, coordinates, tracks, vias and zones match')
