"""Export/import Rev07 with local Freerouting CLI; KiCad DRC is authoritative.

Run export first; run the portable router with the documented command, then import.
No source or board data are sent to any external routing service.
"""
from pathlib import Path
import sys,json
import pcbnew as p
R=Path(__file__).resolve().parents[1];H=R/'hardware/Rev07';T=R/'tmp/Rev07';T.mkdir(parents=True,exist_ok=True)
file=H/'HeishaMon_V6_Touch_Adapter.kicad_pcb';b=p.LoadBoard(str(file))
def point_nm(xy):return p.VECTOR2I(int(round(xy[0]*1000000)),int(round(xy[1]*1000000)))
if sys.argv[1]=='export':
 for netclass in b.GetAllNetClasses().values():
  netclass.SetClearance(p.FromMM(.15));netclass.SetTrackWidth(p.FromMM(.2));netclass.SetViaDiameter(p.FromMM(.5));netclass.SetViaDrill(p.FromMM(.2))
 assert p.ExportSpecctraDSN(b,str(T/'adapter.dsn'))
 # Explicit edge-band keepouts also work with router versions that assign
 # board outlines the ordinary conductor clearance instead of edge clearance.
 dsn=T/'adapter.dsn';text=dsn.read_text()
 bands=[(98.66,95,98.81,136),(121.51,95,121.66,136),(98.66,95,121.66,95.15),(98.66,135.85,121.66,136),(98.66,114.1,99.5,133.5)]
 keepouts=[]
 for i,(x1,y1,x2,y2) in enumerate(bands):
  for layer in ['F.Cu','B.Cu']:
   keepouts.append(f'    (keepout edge_{i}_{layer} (rect {layer} {x1*1000:g} {-y2*1000:g} {x2*1000:g} {-y1*1000:g}))')
 text=text.replace('    (via ', '\n'.join(keepouts)+'\n    (via ',1)
 dsn.write_text(text)
 print('DSN exported',flush=True)
else:
 if sys.argv[1]=='import':
  assert not list(b.GetTracks()),'Regenerate clean placement before importing'
  assert p.ImportSpecctraSES(b,str(T/'adapter.ses'))
 elif sys.argv[1]=='restore':
  assert not list(b.GetTracks()),'Regenerate clean placement before restoring'
  copper=json.loads((H/'routed_copper.json').read_text())
  netcodes={n.GetNetname():n.GetNetCode() for n in b.GetNetsByNetcode().values()}
  for s in copper['segments']:
   track=p.PCB_TRACK(b);track.SetStart(point_nm(s['a']));track.SetEnd(point_nm(s['b']));track.SetWidth(p.FromMM(s['width']));track.SetLayer(p.F_Cu if s['layer']==0 else p.B_Cu);track.SetNetCode(netcodes[s['net']]);b.Add(track)
  for s in copper['vias']:
   via=p.PCB_VIA(b);via.SetPosition(point_nm([s['x'],s['y']]));via.SetWidth(p.FromMM(s['diameter']));via.SetDrill(p.FromMM(s['drill']));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(netcodes[s['net']]);b.Add(via)
 elif sys.argv[1]=='finish':
  report=json.loads((H/'DRC.json').read_text())
  dangling={v['items'][0]['uuid'] for v in report['violations'] if v['type']=='track_dangling'}
  for track in list(b.GetTracks()):
   if str(track.m_Uuid.AsString()) in dangling:b.RemoveNative(track)
 else:raise SystemExit('Use export, import, restore or finish')
 for track in b.GetTracks():
  if not isinstance(track,p.PCB_VIA) and track.GetWidth()<p.FromMM(.15):track.SetWidth(p.FromMM(.15))
 for zone in list(b.Zones()):b.RemoveNative(zone)
 nets={n.GetNetname():n.GetNetCode() for n in b.GetNetsByNetcode().values()}
 for layer in [p.F_Cu,p.B_Cu]:
  z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(nets['GND']);z.SetLocalClearance(p.FromMM(.2));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.25));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
  outline=z.Outline();outline.NewOutline()
  for x,y in [(99.16,95.5),(121.16,95.5),(121.16,135.5),(99.16,135.5)]:outline.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 for fp in b.GetFootprints():
  for pad in fp.Pads():
   if pad.GetNetname()=='GND' and pad.GetAttribute()==p.PAD_ATTRIB_SMD:pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
 p.ZONE_FILLER(b).Fill(b.Zones())
 p.SaveBoard(str(file),b)
 segments=[];vias=[]
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):vias.append(dict(x=p.ToMM(t.GetPosition().x),y=p.ToMM(t.GetPosition().y),net=t.GetNetname(),diameter=p.ToMM(t.GetWidth(p.F_Cu)),drill=p.ToMM(t.GetDrillValue())))
  else:segments.append(dict(a=[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)],b=[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)],layer=0 if t.GetLayer()==p.F_Cu else 1,net=t.GetNetname(),width=p.ToMM(t.GetWidth())))
 (H/'routed_copper.json').write_text(json.dumps(dict(segments=segments,vias=vias),indent=2)+'\n')
 print('Imported',len(segments),'tracks;',len(vias),'vias')
