"""Compare numbered supplier pads with actual KiCad pads, without generic rules.

Run using KiCad Python after fetch_voltage_monitor_parts.py. A library comparison
does not prove the rotation/centering of the assembler's separate machine model.
"""
from pathlib import Path
import csv
import itertools
import json
import math
import sys
import pcbnew as p

R = Path(__file__).resolve().parents[1]
H = R / 'hardware/Rev07'
M = R / 'manufacturing/JLCPCB/Rev07'
b = p.LoadBoard(str(H / 'HeishaMon_V6_Touch_Adapter.kicad_pcb'))
fps = {f.GetReference(): f for f in b.GetFootprints()}
packages = json.loads((H / 'supplier_package_facts.json').read_text())['packages']

def rotate(x, y, degrees):
    a = math.radians(degrees)
    # CAD screen coordinates: +y down; CPL angles counterclockwise.
    return (x*math.cos(a)+y*math.sin(a), -x*math.sin(a)+y*math.cos(a))

rows = []
panels = []
for index, package in enumerate(packages):
    ref = package['ref']
    fp = fps[ref]
    k = {pad.GetNumber(): (p.ToMM(pad.GetPosition().x-fp.GetPosition().x),
                           p.ToMM(pad.GetPosition().y-fp.GetPosition().y)) for pad in fp.Pads() if pad.GetNumber() != 'MP'}
    supplier = {pad['number']: (pad['x_mm'], pad['y_mm']) for pad in package['pads']}
    common = sorted(k.keys() & supplier.keys(), key=int)
    assert len(common) == len(k), (ref, common)
    candidates = []
    for correction in [0, 90, 180, 270]:
        angle = (fp.GetOrientationDegrees()+correction) % 360
        moved = {n: rotate(*supplier[n], angle) for n in common}
        dx = sum(k[n][0]-moved[n][0] for n in common)/len(common)
        dy = sum(k[n][1]-moved[n][1] for n in common)/len(common)
        rms = math.sqrt(sum((k[n][0]-moved[n][0]-dx)**2 +
                            (k[n][1]-moved[n][1]-dy)**2 for n in common)/len(common))
        candidates.append((rms, correction, angle, dx, dy))
    candidates.sort()
    rms, correction, angle, dx, dy = candidates[0]
    assert rms < .1 and candidates[1][0] > rms+.5, (ref, candidates)
    if ref == 'J4':
        # Additional check: mounting pads on the correct side of numbered pads.
        mps = [(p.ToMM(pad.GetPosition().x-fp.GetPosition().x), p.ToMM(pad.GetPosition().y-fp.GetPosition().y))
               for pad in fp.Pads() if pad.GetNumber() == 'MP']
        smps = [rotate(*supplier[n], angle) for n in ['16', '17']]
        assert min(max(math.dist(a, (c[0]+dx, c[1]+dy)) for a, c in zip(mps, order))
                   for order in itertools.permutations(smps)) < .3
    rows.append(dict(ref=ref, code=package['code'], kicad_degrees=fp.GetOrientationDegrees()%360,
                     correction_degrees=correction, cpl_degrees=angle,
                     numbered_pads_compared=len(common), centered_pad_rms_mm=round(rms, 6),
                     comparison_translation_mm=[round(dx, 6), round(dy, 6)],
                     translation_applied_to_cpl=False, library_orientation_verified=True,
                     assembler_preview_verified=False, source_url=package['source_url']))
    # Independent visual reference, viewed from the assembled F side.
    cx = 160 + index*310
    cy = 260
    scale = min(34, 170/max(max(abs(x), abs(y)) for x,y in k.values()))
    panel = [f'<text x="{cx}" y="55" text-anchor="middle">{ref} / {package["code"]}</text>',
             f'<text x="{cx}" y="83" text-anchor="middle">CPL {angle:g}°; Korrektur +{correction}°</text>']
    for n in common:
        x, y = k[n]
        sx, sy = rotate(*supplier[n], angle)
        px, py = cx+x*scale, cy+y*scale
        panel += [f'<rect x="{px-7}" y="{py-5}" width="14" height="10" fill="#d0d7de" stroke="#24292f"/>',
                  f'<circle cx="{cx+(sx+dx)*scale}" cy="{cy+(sy+dy)*scale}" r="3" fill="#00824b"/>',
                  f'<text x="{px+12}" y="{py+4}" font-size="11">{n}</text>']
    panel += [f'<text x="{cx}" y="470" text-anchor="middle">{len(common)} Signalpads; RMS {rms:.3f} mm</text>']
    panels.extend(panel)

report = dict(revision='0.7', source='JLCEDA/EasyEDA Official Library',
              homepages=['https://lceda.cn/', 'https://easyeda.com/'],
              method='All numbered pads, four quarter turns, centered least-squares comparison; J4 mounting side checked.',
              limitation='Supplier library is not the JLC order-specific placement/3D model. Translation is comparison-only; no automatic CPL position offset.',
              assembler_preview_verified=False, parts=rows)
(H / 'assembly_orientation_audit.json').write_text(json.dumps(report, indent=2)+'\n')
svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1570" height="620" viewBox="0 0 1570 620">
<rect width="1570" height="620" fill="white"/><g font-family="Arial,sans-serif" font-size="17" fill="#24292f">
'''+''.join(panels)+'''
<text x="35" y="520">Rev.0.7: Grau = echte KiCad-Pads; Grün = Lieferanten-Padmitten nach Rotation und Zentrierung.</text>
<text x="35" y="550">Quelle: JLCEDA/EasyEDA Official Library — https://lceda.cn/ / https://easyeda.com/</text>
<text x="35" y="580">Geometrieabgleich bestanden. Auftragsbezogenes JLC-Preview / Bauteilzentrierung noch zu bestätigen.</text>
</g></svg>'''
(H / 'Bestueckungsrotationen.svg').write_text(svg, encoding='utf-8')
if '--check-cpl' in sys.argv:
    with (M/'CPL_JLCPCB_REVIEW.csv').open(encoding='utf-8-sig') as f:
        cpl = {r['Designator']: r for r in csv.DictReader(f)}
    for row in rows:
        assert abs(float(cpl[row['ref']]['Rotation'])-row['cpl_degrees']) < .01, row['ref']
        assert cpl[row['ref']]['Layer'] == 'Top'
print(json.dumps(rows, indent=2))
