"""Package the checked Rev07 prototype separately from Rev06 firmware."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];H=R/'hardware/Rev07';M=R/'manufacturing/JLCPCB/Rev07';O=R/'output';O.mkdir(exist_ok=True)
v=json.loads((H/'validation_summary.json').read_text())
assert v['drc_violations']==v['erc_violations']==v['unconnected_items']==0
tools=['design_adapter.py','voltage_monitor_design.py','place_voltage_monitor.py','route_voltage_monitor.py','check_voltage_monitor.py','document_voltage_monitor.py','export_voltage_monitor.py','verify_reproduction.py','package_voltage_monitor.py','fetch_voltage_monitor_parts.py','review_voltage_monitor_assembly.py','review_voltage_monitor_hardware.py']
records={}
for folder in [H,M]:
 for f in folder.rglob('*'):
  if f.is_file() and f.suffix not in ['.kicad_prl','.lck'] and not f.name.startswith('~') and f.name!='artifact_provenance.json':records[f.relative_to(R).as_posix()]=f
for name in tools:records['tools/'+name]=R/'tools'/name
for name in ['LICENSE','LICENSING.md']:records[name]=R/name
# The old rule file is the base for source regeneration, not Rev07 fabrication.
records['hardware/HeishaMon_V6_Touch_Adapter.kicad_dru']=R/'hardware/HeishaMon_V6_Touch_Adapter.kicad_dru'
report=dict(revision='0.7',board_mm=[23,41],layers=2,hardware_tested=False,manufacturing_release=False,firmware_adc_support=False,
 source_commit_before_changes='d19d5762357ab4ec925b10f54fdad2f6250cf1b7',
 routing=dict(tool='Freerouting',version='2.5.0',jar_sha256='f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7',clearance_mm=.15,track_default_mm=.2,track_minimum_mm=.15,via_diameter_mm=.5,via_drill_mm=.2,edge_clearance_mm=.3,
  note='Local routing; postprocessed two short necks to 0.15 mm and removed a dangling stub; saved final copper is authoritative'),
 reproduction='Verified with tools/verify_reproduction.py --voltage: exact pad/track/via geometry and clean KiCad DRC',
 sha256={name:hashlib.sha256(f.read_bytes()).hexdigest() for name,f in sorted(records.items())})
(H/'artifact_provenance.json').write_text(json.dumps(report,indent=2)+'\n')
records['hardware/Rev07/artifact_provenance.json']=H/'artifact_provenance.json'
target=O/'HeishaMon_V6_Touch_Adapter_Rev07_PROTOTYPE.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
 for name,f in sorted(records.items()):z.write(f,name)
 z.writestr('SHA256SUMS.txt','\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+name for name,f in sorted(records.items()))+'\n')
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print(json.dumps(dict(file=str(target),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),entries=len(records)+1)))
