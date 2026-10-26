# HeishaMon V6 Adapter Rev.0.6 – kompakt, Überkopf, Touch-Betriebsart

KiCad 10: HeishaMon_V6_Touch_Adapter.kicad_pro öffnen.

23×41 mm, 1,6 mm, zwei Kupferlagen. Gegenüber Rev.0.3 sinkt die Platinenfläche um 64,2 %. F-Seite mit allen SMD-Bauteilen und LCD-Buchse liegt montiert unten; die manuell auf B gelöteten Stiftleisten J1/J2/J3 liegen oben. J3 ist 2×4, nicht mehr 1×8. Pin 1 und GPIO-Belegung sind beschriftet.

Kein mechanischer Schalter: J5, S1 und R4 entfallen, MCP-GP0 bleibt frei. Die Betriebsarten Automatisch / Listen only werden per Touch gewählt und im ESP32-NVS gespeichert. Der MCP23008 bleibt für die Resetleitungen vorhanden.

23 PCB-Footprints: 16 SMD-Bauteile, drei manuelle Stiftleisten und vier unbestückte Messpads. 21 Netze. J6/J7 sind ausschließlich im Gesamtschaltplan die externen W5500-Gegenkontakte.

ERC 0 Verstöße; DRC 0 Verstöße; 0 offene Verbindungen. Die Kontaktspiegelung nach dem 180°-Kippen wurde unabhängig an den tatsächlichen PCB-Pads geprüft. Diese Koordinatenprüfung bestätigt die USR-ES1-Referenz, nicht die noch unvermessenene V6-Hardware.

## Fertigung

Die Prototyp-Fertigungsdaten liegen unter manufacturing/JLCPCB/Rev06/. BOM und CPL enthalten nur SMD-Teile. J1/J2/J3 fehlen in diesen beiden Dateien; ihre Bohrungen und Pads sind in den Gerbern und Bohrdaten weiterhin vorhanden. Werkseitig Top/F bestücken, obwohl die F-Seite später montiert unten liegt.

Gesamtschaltplan_rev06.pdf und Gesamtverdrahtung_rev06.pdf zeigen alle Verbindungen. PCB_Vorderseite.svg und PCB_Rueckseite.svg zeigen die tatsächlichen Kupferlagen. parts_catalogue.json enthält Teilenummern, Bestandsprüfung und Alternativen.

Vor Bestellung V6-Steckerbelegung, Modul-/Kabelabstände, unterseitige LCD-Buchse und Stromreserve praktisch prüfen. Die langen Stapelanschlüsse J1/J2 sind als generisches Bohrbild modelliert; ein konkretes Steckerteil mit passender Gesamthöhe ist noch auszuwählen. Weitere JLC-DFM-/Orientierungsangaben stehen in der Fertigungsanleitung.

## Reproduktion

routed_copper.json enthält die fertige Kupfergeometrie, routing_order.json die passende Routingreihenfolge. Achtung: tools/design_adapter.py überschreibt PCB und Schaltplan mit dem Ausgangsentwurf. Manuelle Änderungen zuerst sichern.

1. Mit KiCad-Python tools/design_adapter.py ausführen.
2. tmp/ anlegen; hardware/routed_copper.json nach tmp/routed_copper.json kopieren.
3. Mit KiCad-Python tools/pcb_io.py import ausführen (Kupfer importieren und Masseflächen füllen).
4. KiCad-ERC, DRC und Netzliste neu exportieren; tools/check_hardware.py prüfen.
5. Mit KiCad-Python tools/export_jlcpcb.py die Fertigungsdaten reproduzieren.

Ein neuer Routingentwurf kann nach pcb_io.py export mit route_adapter.py hardware/routing_order.json berechnet werden (Python mit NumPy). refine_routing.py bereinigt anhand eines ersten DRC-Berichts unnötige Vias und ergänzt Masse-Vias. Die mitgelieferte Kupferdatei ist bereits nachbearbeitet.
