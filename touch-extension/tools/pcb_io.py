"""KiCad PCB copper geometry export and routed copper import."""
from pathlib import Path
import json,sys
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];file=ROOT/'hardware/HeishaMon_V6_Touch_Adapter.kicad_pcb'
b=p.LoadBoard(str(file));mm=p.ToMM
if sys.argv[1]=='export':
 pads=[]
 for fp in b.GetFootprints():
  for pad in fp.Pads():
   if not pad.GetNetCode():net='NC:'+fp.GetReference()+'.'+pad.GetNumber()
   else:net=pad.GetNetname()
   size=pad.GetSize();pos=pad.GetPosition()
   w,h=mm(size.x),mm(size.y)
   if round(pad.GetOrientationDegrees())%180==90:w,h=h,w
   pads.append(dict(ref=fp.GetReference(),pin=pad.GetNumber(),net=net,x=mm(pos.x),y=mm(pos.y),w=w,h=h,layers=[i for i,layer in enumerate([p.F_Cu,p.B_Cu]) if pad.IsOnLayer(layer)],shape=str(pad.GetShape())))
 (ROOT/'tmp/pcb_geometry.json').write_text(json.dumps(pads))
else:
 assert not list(b.GetTracks()), 'Regenerate the placement with design_adapter.py before importing routed copper'
 data=json.loads((ROOT/'tmp/routed_copper.json').read_text())
 nets={n.GetNetname():n.GetNetCode() for n in b.GetNetsByNetcode().values()}
 for r in data['segments']:
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(r['a'][0]),p.FromMM(r['a'][1])));t.SetEnd(p.VECTOR2I(p.FromMM(r['b'][0]),p.FromMM(r['b'][1])));t.SetWidth(p.FromMM(r['width']));t.SetLayer([p.F_Cu,p.B_Cu][r['layer']]);t.SetNetCode(nets[r['net']]);b.Add(t)
 for r in data['vias']:
  v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(r['x']),p.FromMM(r['y'])));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(nets[r['net']]);b.Add(v)
 for zone in list(b.Zones()):b.Remove(zone)
 for layer in [p.F_Cu,p.B_Cu]:
  z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(nets['GND']);z.SetLocalClearance(p.FromMM(.25));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.35));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
  outline=z.Outline();outline.NewOutline()
  for x,y in [(99.16,95.5),(121.16,95.5),(121.16,135.5),(99.16,135.5)]:outline.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 filler=p.ZONE_FILLER(b);filler.Fill(b.Zones())
 for drawing in b.GetDrawings():
  if isinstance(drawing,p.PCB_TEXT) and 'UNROUTED' in drawing.GetText():drawing.SetText('ROUTED / V6 FIT NOT VERIFIED')
 p.SaveBoard(str(file),b)
 pads_audit=[dict(ref=fp.GetReference(),pin=pad.GetNumber(),net=pad.GetNetname(),x=mm(pad.GetPosition().x),y=mm(pad.GetPosition().y),side='B' if fp.GetLayer()==p.B_Cu else 'F') for fp in b.GetFootprints() for pad in fp.Pads() if pad.GetNetCode()]
 j4=next(fp for fp in b.GetFootprints() if fp.GetReference()=='J4')
 edge_segments=[[[mm(d.GetStart().x),mm(d.GetStart().y)],[mm(d.GetEnd().x),mm(d.GetEnd().y)]] for d in b.GetDrawings() if isinstance(d,p.PCB_SHAPE) and d.GetLayer()==p.Edge_Cuts]
 connector_geometry=dict(footprint=str(j4.GetFPID().GetLibItemName()),rotation=j4.GetOrientationDegrees(),origin=[mm(j4.GetPosition().x),mm(j4.GetPosition().y)],mating_face_x=mm(j4.GetPosition().x)-2.45,edge_segments=edge_segments)
 counts=dict(connector_geometry=connector_geometry,tracks=sum(1 for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)),vias=sum(1 for t in b.GetTracks() if isinstance(t,p.PCB_VIA)),zones=len(list(b.Zones())))
 (ROOT/'hardware/pcb_audit.json').write_text(json.dumps(dict(pads=pads_audit,**counts),indent=2))
 manifest=ROOT/'hardware/netlist_design.json';meta=json.loads(manifest.read_text());meta['status']='ROUTED PROTOTYPE; V6 FIT UNVERIFIED';manifest.write_text(json.dumps(meta,indent=2))
 print(len(data['segments']),'tracks',len(data['vias']),'vias imported')
