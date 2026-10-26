# JLCPCB – Fertigung und Bestückung, Hardware Rev.0.6

Stand: 25.10.2026. Prototyp: mechanische V6-Passung und Funktion noch nicht am realen Aufbau bestätigt.

## Dateien für den Upload

- Gerber_HeishaMon_V6_Rev06.zip: Platinenlagen und PTH-/NPTH-Bohrdaten. Nur dieses innere ZIP als Gerberdatei verwenden.
- BOM_JLCPCB.csv: 9 Bauteilgruppen / 16 SMD-Teile, mit geprüften JLC-/LCSC-Nummern.
- CPL_JLCPCB.csv: dieselben 16 Bauteile, Positionen in mm und Rotationen.
- Manual_Parts_NOT_IN_ASSEMBLY.csv: J1/J2/J3 für die spätere manuelle Bestückung; nicht als JLC-BOM hochladen.

Die 20 Bohrungen und Lötpads der manuellen Steckleisten bleiben in den Gerbern und Bohrdateien. Sie fehlen ausschließlich in der automatischen BOM/CPL. Unbestückte Testpunkte und die im Schaltplan extern dargestellten W5500-Gegenkontakte J6/J7 sind ebenfalls nicht Teil der Bestückungsliste. Schalter, J5 und R4 sind entfernt.

## Bestellvorgaben

23 x 41 mm, FR4, zwei Kupferlagen, 1,6 mm Dicke, 1 oz Kupfer. Eine Bestückungsseite: **Top/F**. Im eingebauten Zustand liegt diese Seite durch das Umdrehen unten! Für die Werksbestückung deshalb nicht versehentlich Bottom auswählen. Die manuell zu bestückende B-Seite benötigt keine JLC-Bestückung.

Für kleine Stückzahlen passt die Einzelplatine größenmäßig zu Economic PCBA (laut aktueller JLC-Tabelle ab 10 x 10 mm). Grün, bleifreies HASL beziehungsweise ENIG nach den im Bestellformular angebotenen Economic-Optionen wählen. Standard PCBA verlangt größere Einzelplatinen bzw. Panels; deshalb nicht ohne Prüfung darauf wechseln.

Das kompakte Layout hat an einigen Randstellen weniger als 2,5 mm Gehäuseabstand. Die JLC-DFM-Prüfung muss dies berücksichtigen; nötigenfalls temporäre Fertigungsstege/Panelisierung durch JLC vorsehen, damit die finale Endkontur klein bleibt. JLC nennt für Economic keine zwingenden separaten Fiducials/Rails, weist in den allgemeinen Montagebedingungen aber auf Randabstände und automatische Fertigungsergänzungen hin. Keine zusätzlichen Löcher unkontrolliert in die bestückte Endkontur setzen lassen.

## Koordinaten und Orientierung

Gerber, Bohrung und Placement verwenden denselben Exportursprung an der linken unteren Platinenecke. Im PCB ist das KiCad (98,66 / 136) mm, exportiert (0 / 0). Die Endkontur reicht von 0 bis 23 mm in X und 0 bis 41 mm in Y. Die CAD-Koordinaten sind keine Abstände vom V6-Platinenrand.

U1 erhält die SOIC-Korrektur +270 Grad nach der aktuellen Standardregel des Fabrication Toolkit. Die LCD-Buchse J4 ist die abgewinkelte Side-Entry-Version SM15B-GHS-TB(LF)(SN), JLC C265027. Sie steht in KiCad bei 270 Grad (gleichbedeutend mit -90 Grad). **Korrektur nach Nutzerprüfung der JLCPCB-3D-Vorschau: Für C265027 entfällt die allgemeine JST_GH_SM-Korrektur +180 Grad; die CPL enthält jetzt 270 Grad statt zuvor 90 Grad.** Mit dem bisherigen Wert zeigte die Öffnung laut Nutzer zum Platineninneren. Die korrigierte Ausrichtung muss in der JLC-Vorschau erneut mit Pin 1 und den Haltepads verglichen werden; sie wurde hier nicht im Bestellprojekt überprüft. Der Kabelabgang weist parallel zur Platine seitlich nach links aus der F-Ansicht, montiert also nach rechts. Rotation_Audit.csv zeigt jede Umrechnung. Vor Freigabe in der JLC-Bestückungsvorschau besonders Pin 1 von U1 und J4 sowie die Richtung der LCD-Buchse mit der KiCad-/Bestückungszeichnung vergleichen. Keine automatische Bauteilsubstitution mit anderem Gehäuse akzeptieren.

Diese Dateien wurden erzeugt und lokal auf Konsistenz geprüft. Es wurde kein CAD-/BOM-Upload und keine Bestellung bei JLC ausgeführt.

## Aktuell geprüfte Verfügbarkeit

Die Bestände wurden am 25.10.2026 direkt in der öffentlichen JLCPCB-Oberfläche abgelesen, ohne Anmeldung und ohne Teile zu reservieren. Lagerbestand und bestellbare Menge können sich ändern. Bei U1 war im Suchergebnis ein Bestand angegeben; keine separate bestellbare Menge wurde übernommen.

| Funktion / Referenzen | JLC-Nummer | Hersteller-Teilenummer | Lagerbestand |
| --- | --- | --- | --- |
| R0 | [C17477](https://jlcpcb.com/partdetail/0805W8F0000T5E/C17477) | 0805W8F0000T5E | 5.499.786 |
| R1, R2 | [C17673](https://jlcpcb.com/partdetail/0805W8F4701T5E/C17673) | 0805W8F4701T5E | 4.744.060 |
| R3, R5, R6, R7, R10 | [C17414](https://jlcpcb.com/partdetail/0805W8F1002T5E/C17414) | 0805W8F1002T5E | 54.247.168 |
| R8, R9 | [C17634](https://jlcpcb.com/partdetail/0805W8F330JT5E/C17634) | 0805W8F330JT5E | 1.362.580 |
| R11 | [C149504](https://jlcpcb.com/partdetail/0805W8F1003T5E/C149504) | 0805W8F1003T5E | 3.367.825 |
| C1, C2 | [C49678](https://jlcpcb.com/partdetail/CC0805KRX7R9BB104/C49678) | CC0805KRX7R9BB104 | 22.465.473 |
| C3 | [C15850](https://jlcpcb.com/partdetail/CL21A106KAYNNNE/C15850) | CL21A106KAYNNNE | 9.133.237 |
| U1 | [C92253](https://jlcpcb.com/partdetail/MicrochipTech-MCP23008_ESO/C92253) | MCP23008-E/SO | 442 |
| J4 | [C265027](https://jlcpcb.com/partdetail/JST-SM15B_GHS_TB_LF_SN/C265027) | SM15B-GHS-TB(LF)(SN) | 480 |

Alle primär ausgewählten Typen waren vorrätig. Es sind daher keine Ersatztypen in die BOM eingetragen.

## Geprüfte Alternativen

- Für C17673: [C407444 – 0805W8D4701T5E](https://jlcpcb.com/partdetail/396001-0805W8D4701T5E/C407444), Bestand 4.980. Gleicher Nennwert/Bauform, engere Toleranz; geeignete Alternative.
- Für C17414: [C84376 – RC0805FR-0710KL](https://jlcpcb.com/partdetail/RC0805FR-0710KL/C84376), Bestand 1.796.974. Gleicher Nennwert, Leistung und Bauform.
- Für C149504: [C96346 – RC0805FR-07100KL](https://jlcpcb.com/partdetail/YAGEO-RC0805FR07100KL/C96346), Bestand 1.509.081. Gleicher Nennwert, Leistung und Bauform.
- Für C17414: [C38522 – 0805W8F1002T5E](https://jlcpcb.com/partdetail/39505-0805W8F1002T5E/C38522), Bestand 0. Aktuell nicht vorrätig; deshalb nicht in der BOM.
- Für C149504: [C17407 – 0805W8F1003T5E SMTonly](https://jlcpcb.com/partdetail/18095-0805W8F1003T5E_SMT/C17407), Bestand 0. Aktuell nicht vorrätig; stattdessen C149504 ausgewählt.

MCP23008T-E/SO wäre die Tape-and-Reel-Ausführung desselben SOIC-18-Bausteins. Eine zusätzliche JLC-Bestandsposition dafür wurde nicht bestätigt. Bei späterem Engpass zuerst C92253 vorbestellen bzw. den identischen SOIC-18-Typ beschaffen lassen. MCP23008 in SSOP-20/QFN-20, MCP23S08 und PCF8574 sind keine direkten Ersatzteile für dieses Layout bzw. diese Firmware.

## Weitere Unterlagen

BOM_Detail.csv enthält Stückzahlen und Spezifikationen, Availability_2026-10-25.csv die abgelesenen Mengen und Quellen, Alternatives.csv die Ersatzteilliste. export_validation.json dokumentiert Dateikonsistenz, Ursprung, Maße, Ausschlüsse und SHA-256 der exportierten PCB. KiCad_SMD_positions.csv ist der unveränderte Ausgangsexport zur Nachvollziehbarkeit.

## Herstellerquellen

- [JLCPCB BOM/CPL aus KiCad 10](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad)
- [JLCPCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
- [JLCPCB Montagebedingungen und Randabstände](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service)
- [JLCPCB Panelisierung](https://jlcpcb.com/help/article/pcb-panelization)
- [Rotationen: Fabrication Toolkit](https://github.com/bennymeg/Fabrication-Toolkit/blob/master/plugins/transformations.csv), Blob 40878ad04b8f0ac427e48085c2440ea26bbd99a9.
