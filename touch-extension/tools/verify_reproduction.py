"""Verify that source generation + final copper reproduces the delivered PCB audit.
Run with KiCad Python. Never modifies the delivered hardware files.
"""
from pathlib import Path
import tempfile,shutil,subprocess,json,sys
R=Path(__file__).resolve().parents[1];tmp=R/'tmp';tmp.mkdir(exist_ok=True)
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
