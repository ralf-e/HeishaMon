# Rev.0.7 - Prototypdaten, keine Bestellfreigabe

23 x 41 mm, 2 Kupferlagen, 1,6 mm, 1 oz. SMD auf Top/F (eingebaut unten), Stiftleisten manuell auf B. Gegenueber Rev.0.6 neuer ADC, Schutzschalter, Supervisor und MCP23008 im SSOP-20-Gehaeuse.

42 SMD-Referenzen in BOM und CPL, drei manuelle Stiftleisten sowie sechs unbestueckte Mess-/Loetpads. Keine Dateien mit Rev06 mischen.

Gepruefte Designregeln: Leiterbahnen mindestens 0,15 mm, Kupferabstand mindestens 0,15 mm, Vias 0,50 mm mit 0,20-mm-Bohrung, Kantenabstand mindestens 0,30 mm. Diese Werte muessen zur bestellten Kupferstaerke und Fertigungsoption passen.

Alle 18 SMD-Typen sind im direkten JLCPCB-Abgleich vom 30.10.2026 verfuegbar; die zuvor fraglichen Praezisionswiderstaende muessen nicht ersetzt werden. Engpass U4: 20 bestellbare Stueck, ohne Reservierung oder Beruecksichtigung auftragsbezogener Zuschlaege. Aktuelle Zahlen und UTC-Zeit stehen in BOM_Detail.csv und hardware/Rev07/stock_snapshot.json. Vor tatsaechlicher Bestellung erneut abgleichen.

Die Pin-1-/Rotationspruefung anhand aller nummerierten Lieferanten-Pads ist bestanden: U1/U2/U3 CPL270, U4 korrigiert auf CPL180, J4 CPL270. Quelle: JLCEDA/EasyEDA Official Library (https://lceda.cn/ und https://easyeda.com/). Widerstaende/MLCC sind ungepolt. Eine ausfuehrliche Pruefung und Grafik liegen in hardware/Rev07/Bestellpruefung.md und Bestueckungsrotationen.svg.

Die mit REVIEW benannten BOM/CPL behalten ihren Namen: Das auftragsbezogene Hersteller-Preview muss die tatsaechlichen Maschinenmodelle, Pin 1 und die Zentrierung bestaetigen. Insbesondere J4 hat zwischen den Bibliotheken unterschiedliche Bezugspunkte; kein automatischer Positionsversatz wurde angewendet. Ein Bibliotheksvergleich ersetzt diesen letzten Schritt nicht.

TP5 ist nur fuer positive 12-V-Messung bis zum vorgesehenen Bereich 18 V. Bei gemeinsamer V6-/Adaptermasse genuegt eine zusaetzliche Leitung vom 12-V-Abgriff zu TP5; GND besteht bereits ueber die Steckkontakte. TP6 ist ein optionaler GND-Loet-/Pruefpunkt, keine zusaetzlich erforderliche Masseleitung. Keine Einspeisung, keine 24 V. V6-Kontakte, Stromreserve und reale Passform sind noch ungetestet.

Die Firmware dev.7 liest den ADC noch nicht aus. Rev06-Software bleibt getrennt erhaeltlich.

Hersteller-Fertigungsgrenzen: https://jlcpcb.com/capabilities/pcb-capabilities/
