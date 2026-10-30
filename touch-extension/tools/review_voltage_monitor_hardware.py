"""Generate a traceable Rev07 design review and blank physical test record.

No result from this script is a live V6-board measurement. Requires KiCad Python.
"""
from pathlib import Path
import csv
import html
import json
import pcbnew as p

R=Path(__file__).resolve().parents[1]; H=R/'hardware/Rev07'
v=json.loads((H/'validation_summary.json').read_text())
s=json.loads((H/'stock_snapshot.json').read_text(encoding='utf-8'))
a=json.loads((H/'assembly_orientation_audit.json').read_text())
assert v['erc_violations']==v['drc_violations']==v['unconnected_items']==0
b=p.LoadBoard(str(H/'HeishaMon_V6_Touch_Adapter.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
stock_by_code={q['code']:q for q in s['parts']}
limiting=min(s['parts'],key=lambda q:q['available_order_quantity']//len(q['refs']))
rows=[]
for ref in ['J1','J2','J3']:
 for pad in sorted(fps[ref].Pads(),key=lambda x:int(x.GetNumber())):
  x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)
  rows.append([ref,pad.GetNumber(),pad.GetNetname() or 'NC',f'{220.32-x:.3f}',f'{y+2.5:.3f}','','','OFFEN'])
contact_file=H/'V6_Kontaktpruefung.csv'
if contact_file.exists():
 with contact_file.open(encoding='utf-8-sig') as f: previous=list(csv.reader(f))[1:]
 assert [q[:5] for q in previous]==[q[:5] for q in rows], 'Existing physical test template geometry differs; review manually'
 # Preserve any user-entered measurements on repeated documentation runs.
 rows=previous
else:
 with contact_file.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['Stecker','Pin','Sollnetz aus Entwurf','Referenz X montiert mm','Referenz Y montiert mm','Istnetz am V6','Messwert/Abstand','Ergebnis']);w.writerows(rows)

# Physical placement reference: flipped adapter as seen from above the V6.
# Fixed 1:1 dimensions in millimetres, with separate calibration bar.
shapes=[]
for edge in b.GetDrawings():
 if edge.GetLayer()!=p.Edge_Cuts:continue
 assert edge.GetShape()==p.SHAPE_T_SEGMENT
 def point(v):return 25+(220.32-p.ToMM(v.x))-98.66,35+(p.ToMM(v.y)+2.5)-97.5
 x1,y1=point(edge.GetStart());x2,y2=point(edge.GetEnd())
 shapes.append(f'<path d="M {x1},{y1} L {x2},{y2}" fill="none" stroke="black" stroke-width="0.2"/>')
for ref,pin,net,x,y,*_ in rows:
 px=25+float(x)-98.66;py=35+float(y)-97.5
 left=ref=='J1' or (ref=='J3' and int(pin)%2==1)
 tx=px-1 if left else px+1
 anchor='end' if left else 'start'
 shapes += [f'<circle cx="{px}" cy="{py}" r="0.5" fill="white" stroke="black" stroke-width="0.12"/>',
            f'<text x="{tx}" y="{py+.5}" text-anchor="{anchor}" font-size="1.5">{ref}.{pin}</text>']
shapes += ['<path d="M 65,80 h 50 M 65,78 v 4 M 115,78 v 4" fill="none" stroke="black" stroke-width="0.2"/>',
           '<text x="65" y="86" font-size="3">Kontrollstrecke 50 mm</text>']
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">
<rect width="210" height="297" fill="white"/><g font-family="Arial,sans-serif" fill="black">
<text x="20" y="20" font-size="5">Rev.0.7 — V6-Passschablone 1:1</text>
<text x="20" y="28" font-size="3">Einbauansicht von oben; Adapter bereits umgedreht.</text>
'''+''.join(shapes)+'''
<text x="20" y="100" font-size="3">Kontur 23 × 41 mm; J1/J2 Reihenabstand 20,32 mm; Raster 2,54 mm.</text>
<text x="20" y="108" font-size="3">100 % / tatsächliche Größe drucken; Kontrollstrecke nachmessen.</text>
<text x="20" y="116" font-size="3">Sollgeometrie des Entwurfs, keine Bestätigung der realen V6-Platine.</text>
<text x="20" y="124" font-size="3">J3-Lage separat prüfen. Schablone nicht zum elektrischen Anschließen nutzen.</text>
</g></svg>'''
(H/'V6_Passschablone_1zu1.svg').write_text(svg,encoding='utf-8')

lines=['# Rev.0.7 – Bestellprüfung vom 30.10.2026','',
'Die lokale Entwurfsprüfung und der aktuelle Lieferantenabgleich sind durchgeführt. Ein physischer Aufbau war nicht verfügbar. Hersteller-Preview und reale V6-Passform sind noch nicht bestätigt; es besteht keine Fertigungsfreigabe.','',
'## Behobene Befunde','',
'- **U4-Rotation:** statt CPL 0° jetzt **180°**, aus allen drei nummerierten Lieferanten-Pads ermittelt. U1/U2/U3 bleiben 270°, J4 bleibt 270°.','- **R15/R19/R23/R27:** statt 1 MΩ jetzt **100 kΩ, 0,1 %, 0603**, Yageo RT0603BRD07100KL / C122538. Das TMUX1511-Datenblatt nennt bis zu 2 µA Powered-off-Leckstrom. Konservativ vollständig am ADC angesetzt ergäben 1 MΩ bis zu 2,002 V; 100 kΩ begrenzen dies rechnerisch auf 0,2002 V. Der quasistatische Nachweis ersetzt keine Messung beim Ein-/Ausschalten.','- Footprints, Steckerpositionen, Endkontur und gespeicherte Kupfergeometrie bleiben erhalten. Schaltplan, BOM und Umrechnungsfaktoren sind aktualisiert.','',
'## Teileverfügbarkeit','',
'Direkte JLCPCB-API-Abfrage, UTC-Zeit pro Position in `stock_snapshot.json`. Keine Reservierung. Die angegebene bestellbare Menge ist nicht nur der Lagerbestand; auftragsbezogenen Teilezuschlag und Mindestmengen in der Kalkulation berücksichtigen. Drei manuelle Steckleisten sind nicht Teil dieser SMD-Prüfung.','',
'| Referenzen | JLC-Nummer | MPN | Bestellbare Stück |','| --- | --- | --- | ---: |']
lines += ['| '+', '.join(q['refs'])+' | ['+q['code']+']('+q['source_url']+') | '+q['mpn']+' | '+str(q['available_order_quantity'])+' |' for q in s['parts']]
lines += ['',f"Engpass: {limiting['refs'][0]} / {limiting['code']}, {limiting['available_order_quantity']} Stück. Das entspricht rechnerisch {limiting['available_order_quantity']//len(limiting['refs'])} Platinen vor eventuellen Fertigungszuschlägen; keine Lieferzusage.",'',
'## Bestückungsorientierung','',
'Quelle: **JLCEDA/EasyEDA Official Library**, [JLCEDA](https://lceda.cn/) / [EasyEDA](https://easyeda.com/). Alle nummerierten Pads der konkreten Lieferantenteile wurden gegen die echten KiCad-Pads verglichen; bei J4 zusätzlich die Seite der Haltepads. Widerstände und MLCC sind ungepolt.','',
'| Referenz | KiCad | Korrektur | CPL | Geprüfte Signalpads |','| --- | ---: | ---: | ---: | ---: |']
lines += [f"| {q['ref']} | {q['kicad_degrees']:g}° | +{q['correction_degrees']}° | {q['cpl_degrees']:g}° | {q['numbered_pads_compared']} |" for q in a['parts']]
lines += ['', '![Padvergleich](Bestueckungsrotationen.svg)','',
'`assembly_orientation_audit.json` dokumentiert die Rechenprüfung. Der kleine Restfehler stammt unter anderem aus unterschiedlichen Landpatterns. Die Zentrierung in der Vergleichsgrafik ist **kein** automatisch angewendeter CPL-Positionsversatz. Bei J4 unterscheiden sich die Referenzen um etwa 0,375 mm quer zur Signalpadreihe; Haltepad-Landpatterns weichen ebenfalls ab. Deshalb im Auftrags-Preview sowohl Signalpads als auch Haltepads und nach außen gerichtete Kabelöffnung prüfen. Eine generische Korrektur um +180° für J4 wäre hier falsch.','',
'Das öffentliche Bibliotheksmodell ist kein Nachweis des konkreten Bestückautomaten-Modells. Die REVIEW-Dateinamen bleiben bis zur Sichtprüfung im auftragsbezogenen JLC-Preview erhalten. Noch kein Upload und keine Bestellung ausgeführt.','',
'## Elektrische und geometrische Entwurfsprüfung','',
f"ERC **0**, DRC **0**, offene Verbindungen **0**. {v['nets_verified']} Netze gegen echte PCB-Pads geprüft. {v['pcb_components']} Footprints, 42 SMD-Referenzen in BOM/CPL, {v['tracks']} Leiterbahnsegmente und {v['vias']} Vias. Steckerpositionen identisch zu Rev.0.6; Kontur 23 × 41 mm / zwei Lagen.",
'','ADS1115: VSSOP-10, 0x48; MCP23008: SSOP-20, 0x20; Touch: 0x38. ADS/TMUX/Supervisor-Pinbelegungen sind explizit im unabhängigen Prüfskript kontrolliert. GP0 bleibt Eingang: die aktuelle dev.7 konfiguriert nur GP1/GP2 als Ausgänge. Künftige ADC-Firmware darf GP0 nicht gegen den Supervisor treiben.','',
'| Kanal | Quelle nominal | ADC nominal | Faktor Quelle/ADC | ADC maximal im vorgesehenen Bereich | Teilerstrom nominal |','| --- | ---: | ---: | ---: | ---: | ---: |']
lines += [f"| AIN{q['channel']} / {q['rail']} | {q['nominal_source_v']:g} V | {q['nominal_adc_v']:.4f} V | {q['source_per_adc_v']:.6f} | {q['worst_adc_v']:.4f} V | {q['nominal_source_current_ua']:.1f} µA |" for q in v['channels']]
lines += ['',
'Die Rechnung berücksichtigt unabhängige ±0,1-%-Widerstandstoleranzen und die zusätzliche Belastung durch 1 kΩ/100 kΩ. Höchste Spannung am offenen TMUX-Eingang: 2,312 V bei 18 V an TP5; damit unter 3,6 V Powered-off-Grenze. Konservative obere Schranke der Leistung des obersten Teilerwiderstands: unter 4,8 mW gegenüber 100 mW Nennleistung. Unbelastete Filterzeitkonstanten: 0,50 / 0,50 / 0,67 / 0,87 ms.','',
'Die beiden 3,3-V-Teiler belasten dieselbe Ursprungsversorgung gemeinsam mit rund 346 µA. Dazu kommen ADC, Schalter, Supervisor und die bestehende Display-/Touch-/Ethernet-Last; eine ausreichende V6-Reglerreserve ist daraus nicht nachgewiesen. Der ADC-Eingang ist dynamisch, daher sind die Faktoren Startwerte für den Multimeterabgleich. Die neue dev.7 enthält noch keine ADC-Auswertung.','',
'## Vor Bestellung am vorhandenen V6-Board prüfen','',
'1. **Passform, spannungslos:** `V6_Passschablone_1zu1.svg` mit 100 % drucken, 50-mm-Kontrollstrecke nachmessen. J1/J2: 2,54-mm-Raster, 20,32-mm-Reihenabstand; J3: 2×4, genaue Lage am Board prüfen. Stecker nicht unter Kraft zusammenstecken.','2. **Kontakte:** `V6_Kontaktpruefung.csv` enthält alle 20 Sollkontakte aus den tatsächlichen PCB-Pads und Leerfelder für Istbelegung/Messwerte. Jede 3,3-V-/5-V-/GND-Verbindung am konkreten V6 abgleichen, NC nicht verbinden. Signalnetze durch Schaltplan/Leiterbahnverfolgung zuordnen; eine Spannungsmessung allein identifiziert keinen GPIO.','3. **Stapelhöhe:** tatsächliche W5500-, Displaystecker- und Kabelhöhen messen; dann konkrete lange Durchsteck-/Stapelkontakte J1/J2 auswählen. Die generischen KiCad-Stiftleisten bestimmen keine kaufbare Bauhöhe. Kein Kontakt zu Bauteilkörpern, Lötstellen oder Kabelsteckern; für den Prototyp mindestens 1 mm freie mechanische Reserve vorsehen.','4. **12 V:** positiven 12-V-Abgriff, gemeinsame Masse und Maximalspannung am Gerät bestimmen. Bei gemeinsamer V6-/Adaptermasse genügt eine zusätzliche Leitung vom 12-V-Abgriff zu TP5; GND besteht bereits über die Steckkontakte. TP6 ist nur ein optionaler GND-Löt-/Prüfpunkt, etwa für das Multimeter oder einen separaten Prüfaufbau ohne bestehende Masseverbindung. Eine zusätzliche Masseleitung ist im normalen V6-Aufbau nicht erforderlich.','',
'`PCB_3D_Pruefansicht.png` ist eine unvollständige lokale Bestückungsansicht: Für J4 fehlt das native KiCad-3D-Modell, die manuellen Stapelkontakte sind generische Modelle. Weder V6 noch W5500 sind als vermessene Gegenbaugruppe enthalten. Diese Ansicht bestätigt keine Stapelhöhen oder Kabelpassform.','',
'## Hardwareprüfung am ersten Rev.0.7-Prototyp','',
'Diese Prüfungen benötigen eine gefertigte Platine, Labornetzteil, Multimeter und für Versorgungstransienten ein Oszilloskop. Ergebnis bisher jeweils **nicht durchgeführt**.','',
'| Schritt | Durchführung / Soll | Ergebnis |','| --- | --- | --- |',
'| Sichtkontrolle | IC-Markierung/Pin 1 und U4-180° mit Bestückungsplan vergleichen; keine Brücken an 0,5-/0,65-mm-Pins. | Offen |',
'| Durchgang, spannungslos | Alle Kontakte anhand Verbindungsmatrix prüfen. Kein harter Kurzschluss zwischen Versorgungen und GND; Ladung von Kondensatoren berücksichtigen. | Offen |',
'| Versorgung ohne V6/Display | Adapter separat mit 3,3 V und zunächst 20 mA Strombegrenzung versorgen, TP5 offen. Bei Begrenzung/Erwärmung abbrechen und Ursache suchen. Erst danach 5 V am vorgesehenen Kontakt zuführen; nie 5 V auf 3,3 V. | Offen |',
'| I²C / GP0 | 0x20 und 0x48 antworten; GP0 an stabilen 3,3 V High. Touchadresse 0x38 erst mit angeschlossenem Display erwarten. | Offen |',
'| Teiler | Bei 3,3/3,3/5/12 V ungefähr 1,557/1,557/1,548/1,402 V an AIN0..3; gegen GND messen. Zunächst ±1 % als Aufbaukontrolle, danach ADC kalibrieren. | Offen |',
'| 12-V-Kanal | Am vom V6 getrennten Adapter 0/6/12/18 V positiv an TP5 durchfahren; AIN3 bei 18 V nominal ca. 2,103 V. | Offen |',
'| Ein-/Ausschalten | 12 V an TP5, EXT-Versorgung aus; AIN-Pins statisch unter 0,3 V. Ein-/Ausschaltkurven mit Oszilloskop prüfen: kein AIN > momentanes VDD+0,3 V; keine Rückspeisung. | Offen |',
'| Unterspannung | EXT langsam um 2,93 V durchfahren; ADC_ENABLE/GP0 muss entsprechend Datenblatt aus-/einschalten, Verzögerung und Hysterese berücksichtigen. Schnelle Versorgungseinbrüche zusätzlich prüfen. | Offen |',
'| Vollaufbau | Displayhelligkeit maximal, Ethernet aktiv, Touch/Reset testen; 3,3/5 V an Quelle und Adapter beobachten, Strom-/Temperaturgrenzen des realen V6-Reglers einhalten. | Offen |',
'| Messgenauigkeit | Vier Kanäle gegen Referenzmultimeter an mehreren Spannungen abgleichen; nach Aufwärmen wiederholen. Ziel für Versorgungskontrolle festlegen, z. B. ±1 % nach Abgleich. | Offen |',
'', 'Vor den I²C-/ADC-Funktionstests ist eine passende Diagnose-/ADC-Firmware nötig. Die bestehende Rev.0.6-dev.7-Datei prüft den ADS1115 nicht. Ohne erfolgreich gemessene Ergebnisse bleiben `hardware_tested` und `manufacturing_release` auf `false`.','',
'## Auftragsbezogene Herstellerprüfung','',
'Nur `Gerber_HeishaMon_V6_Rev07_PROTOTYPE.zip`, `BOM_JLCPCB_REVIEW.csv` und `CPL_JLCPCB_REVIEW.csv` aus `manufacturing/JLCPCB/Rev07/` verwenden. 23×41 mm, zwei Lagen, 1,6 mm, 1 oz, Bestückung Top/F. Das spätere Überkopf-Montieren ist kein Grund, Bottom zu bestellen.','',
'Im Preview: 42 SMD-Referenzen/18 Typen, keine J1/J2/J3/TP-Bestückung, U1/U2/U3/J4 CPL270, U4 CPL180. Pin 1 aller ICs und J4-Padüberdeckung/Kabelöffnung kontrollieren. Wegen der kompakten Endkontur erforderliche Fertigungsstege/Panelisierung durch den Fertiger prüfen lassen; Endkontur nicht vergrößern. Keine automatische Gehäuse-/Bauteilsubstitution.','',
'## Reproduzierbare Prüfungen','',
'1. `fetch_voltage_monitor_parts.py` mit Netzwerkzugriff aktualisiert den vollständigen JLC-Bestand und die fünf Lieferanten-Padbelegungen.','2. KiCad ERC/DRC/XML-Netzliste erzeugen; `check_voltage_monitor.py` prüft Netze, Pinbelegung und Mess-/Schutzrechnung.','3. `review_voltage_monitor_assembly.py` berechnet die Rotationen; `export_voltage_monitor.py` exportiert BOM/CPL/Gerber.','4. `review_voltage_monitor_assembly.py --check-cpl` prüft die tatsächliche CPL; `review_voltage_monitor_hardware.py` aktualisiert diesen Bericht und die Kontakt-Prüfvorlage.','5. `verify_reproduction.py --voltage` prüft Quelle plus gespeicherte Kupfergeometrie; `package_voltage_monitor.py` erstellt das aktualisierte Paket.','',
'## Primärquellen','',
'- [TMUX1511, elektrische Kennwerte und Powered-off-Schutz](https://www.ti.com/lit/ds/symlink/tmux1511.pdf), insbesondere IPOFF bis ±2 µA über den spezifizierten Temperaturbereich.','- [TLV809E, DCK-Pinbelegung und 2,93-V-Ausführung](https://www.ti.com/lit/ds/symlink/tlv803e.pdf).','- [ADS1115, VSSOP-10-Pinbelegung und Eingangsbeschaltung](https://www.ti.com/lit/ds/symlink/ads1115.pdf).','- [MCP23008, Microchip-Datenblatt](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP23008-MCP23S08-Data-Sheet-20001919F.pdf).','- [JLCPCB Fertigungsgrenzen](https://jlcpcb.com/capabilities/pcb-capabilities/).']
(H/'Bestellpruefung.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
report=dict(revision='0.7',design_review_passed=True,physical_hardware_tested=False,
 stock_snapshot_verified=True,rotation_library_verified=True,assembler_preview_verified=False,
 manual_stack_connector_part_selected=False,real_v6_pinout_verified=False,real_v6_stack_fit_verified=False,
 firmware_adc_support=False,manufacturing_release=False,
 remaining_before_order=['order-specific assembler preview and centering','real V6 contact/geometry verification','select stack headers using measured heights'],
 prototype_validation='Bench test table in Bestellpruefung.md; all physical results pending')
(H/'readiness.json').write_text(json.dumps(report,indent=2)+'\n')
print('Rev07 design review, 20-contact physical test record and 1:1 fit template written')
