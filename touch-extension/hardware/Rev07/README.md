# Adapter Rev.0.7 - vier Spannungsmessungen

Neue Hardwarevariante neben der unveränderten Rev.0.6. Zielmaß weiterhin **23 × 41 mm**, zwei Kupferlagen, 1,6 mm. Stecker J1/J2/J3/J4 und die Überkopf-Einbaulage bleiben erhalten. Alle SMD-Bauteile liegen auf F (montiert unten); die vorhandenen manuellen Stiftleisten auf B.

## Messkanäle

| ADS1115-Eingang | Messpunkt | Spannungsteiler oben / unten | Vorgesehener Eingangsbereich |
| --- | --- | --- | --- |
| AIN0 | 3,3 V direkt an der V6, vor R0 | 10 kΩ / 10 kΩ | 0–3,6 V |
| AIN1 | 3,3 V im Erweiterungszweig, hinter R0 | 10 kΩ / 10 kΩ | 0–3,6 V |
| AIN2 | 5-V-Versorgung der V6 | 20 kΩ / 10 kΩ | 0–5,5 V |
| AIN3 | Externer 12-V-Messanschluss TP5 | 68 kΩ / 10 kΩ | 0–18 V, positiv gegen GND |

Die vorhandene Adapterbelegung führt keine 12 V. Für die Messung genügt bei gemeinsamer V6-/Adaptermasse **eine zusätzliche Leitung vom 12-V-Abgriff zu TP5 (+12V_SENSE)**. Die Masseverbindung besteht bereits über die vorhandenen Steckkontakte; eine zusätzliche Masseleitung ist dann nicht erforderlich. **TP6 ist ein optionaler GND-Löt- und Prüfpunkt**, beispielsweise für die Multimeter-Messspitze oder einen separaten Prüfaufbau ohne vorhandene Masseverbindung. TP5 ist ausschließlich ein hochohmiger Messeingang und versorgt die Platine nicht. Der konkrete 12-V-Abgriff muss am eigenen Gerät identifiziert werden. Keine Netzspannung, keine 24 V und keine negative Spannung anschließen.

## ADC und Schutzbeschaltung

- U2: ADS1115IDGSR, VSSOP-10, I²C-Adresse **0x48**, Versorgung aus +3V3_EXT. Der vorhandene Bus mit MCP23008 (0x20) und Touch (0x38) wird mitbenutzt; keine weiteren ESP32-Pins nötig.
- U1 verwendet in dieser Revision den **MCP23008-E/SS im SSOP-20-Gehäuse**. Das spart gegenüber dem bisherigen SOIC-18 Platz für die Messschaltung. Der Baustein ist elektrisch funktionsgleich, hat aber eine andere physische Pinbelegung; SOIC- und SSOP-Teile sind nicht austauschbar.
- U3: TMUX1511PWR, vier analoge Schalter mit Schutz bei ausgeschalteter Versorgung. Die Spannungsteiler liegen vor den Schaltern; dadurch sehen deren Eingänge auch bei anliegenden 12 V nur die heruntergeteilte Spannung.
- U4: TLV809EA29DCKR, 2,93-V-Supervisor. Er gibt die Messpfade erst bei ausreichender Erweiterungsversorgung frei und trennt sie bei Unterspannung. MCP23008 **GP0** liest dieses Freigabesignal: Low bedeutet ungültige Messung. GPIO5 / TX-Freigabe bleibt davon getrennt.
- Jeder Kanal hat einen 100-nF-Filter vor dem Schalter, danach einen 1-kΩ-Serienwiderstand und einen **100-kΩ-Ableitwiderstand** am ADC-Eingang. Neue Messwiderstände: 0603, 0,1 %. Bei der Bestellprüfung wurden die zuvor vorgesehenen 1 MΩ auf 100 kΩ geändert, damit der maximal spezifizierte Powered-off-Leckstrom rechnerisch unter 0,3 V am ausgeschalteten ADC bleibt. Die Belastung durch Serien-/Ableitwiderstände muss bei der Umrechnung berücksichtigt werden; die Faktoren stehen in `validation_summary.json`.
- Die digitalen Versorgungsprüfungen und die Hardware-Isolation sind kein Ersatz für einen Überspannungsschutz gegen beliebige Fehlverdrahtung. Unterhalb der Freigabeschwelle werden keine gültigen Spannungswerte geliefert; Ausfall von ESP32/Versorgung kann nicht am abgeschalteten Display angezeigt werden.

Die Messung dient langsamer Versorgungskontrolle. Gegen Multimeter kalibrieren; sehr kurze Einbrüche und die Regler-Stromreserve sind damit nicht zuverlässig nachgewiesen. Der ADS1115-Eingangswiderstand und die temperaturabhängigen Leckströme sind zusätzlich zur Widerstandstoleranz zu berücksichtigen.

Für die spätere Firmware: alle vier Kanäle single-ended gegen GND, PGA-Messbereich **±4,096 V**, beispielsweise 128 Samples/s und gefilterte langsame Anzeige. Bei Low an GP0 die Messung als ungültig kennzeichnen. Die nominalen Umrechnungsfaktoren stehen in `validation_summary.json`; sie berücksichtigen die 1-kΩ-/100-kΩ-Beschaltung, ersetzen aber keinen Abgleich am Gerät.

## Ergebnis der elektrischen Prüfungen

ERC **0**, DRC **0**, **0 offene Verbindungen**. Unabhängiger Vergleich: 35 Netze im Schaltplan und auf den echten PCB-Pads, unveränderte Steckerpositionen J1/J2/J3/J4. 51 PCB-Footprints: 42 SMD-Bauteile, drei manuelle Stiftleisten und sechs Mess-/Lötpads. Zwei Kupferlagen, 835 Leiterbahnsegmente und 79 Vias.

Die kompakte Variante verwendet mindestens 0,15 mm Leiterbahnbreite und Kupferabstand sowie Vias 0,50/0,20 mm. Der Kantenabstand bleibt mindestens 0,30 mm. Die zugehörigen Prototyp-Fertigungsdaten liegen unter [manufacturing/JLCPCB/Rev07](../../manufacturing/JLCPCB/Rev07/README.md). Die [Bestellprüfung](Bestellpruefung.md) dokumentiert den aktuellen Bestand aller 18 SMD-Typen und den nummerierten Lieferanten-Padvergleich. U4 wurde auf CPL180 korrigiert; U1/U2/U3/J4 verwenden CPL270. Hersteller-Preview/Zentrierung sowie reale V6-Kontakte und Passform bleiben offen. Dies ist keine Hardware- oder Bestellfreigabe.

## Software und Prüfumfang

Die vorhandene Firmware **0.1.0-dev.7 / Commit d19d576** bleibt für Rev.0.6 verfügbar. Sie liest den neuen ADC noch nicht aus. Die bisherige Display-/Betriebsartenfunktion wird durch die zusätzlichen I²C-Bauteile nicht absichtlich verändert; der reale Betrieb beider Platinenrevisionen ist noch zu prüfen. Für Spannungsanzeige/MQTT ist eine separate Firmware-Erweiterung erforderlich.

Vor Fertigung müssen ERC, DRC, Verbindungsvergleich, 12-V-Polarität, Montageabstände, Bestückungsorientierung und Bauteilverfügbarkeit geprüft sein. Der elektrische Rechencheck ersetzt keine Hardwareprüfung. Es erfolgt keine automatische Fertigungsfreigabe oder Bestellung.

## Reproduktion

1. `tools/design_adapter.py --voltage` mit KiCad-Python erzeugt diese Variante, ohne Rev.0.6 zu überschreiben. Die festgehaltene Platzierung steht in `component_placement.json`.
2. Für die Reproduktion des vorhandenen Layouts `tools/route_voltage_monitor.py restore` verwenden. Es übernimmt die festgehaltene endgültige Kupfergeometrie aus `routed_copper.json` und füllt die Masseflächen. Dafür ist kein Autorouter erforderlich.
3. Nur für eine neue Entflechtung: `tools/route_voltage_monitor.py export` erzeugt die lokale DSN-Datei unter `tmp/Rev07/`; lokal mit Freerouting entflechten und anschließend mit `import` übernehmen. Nicht jeden Autorouter-Ausgang als fertiges Layout behandeln: Auch minimale Verengungen und lose Enden mit KiCad prüfen und korrigieren.
4. KiCad ERC, DRC und XML-Netzliste neu exportieren; danach `tools/check_voltage_monitor.py` mit KiCad-Python ausführen. Die unabhängige Prüfung vergleicht Schaltplan und echte PCB-Pads, Steckerpositionen und Messbereichsrechnung.

## Quellen

- [ADS1115: Datenblatt und Pinbelegung](https://www.ti.com/lit/ds/symlink/ads1115.pdf)
- [TMUX1511: Datenblatt, Powered-off Protection](https://www.ti.com/lit/ds/symlink/tmux1511.pdf)
- [TLV809E: 2,93-V-Supervisor und SC70-Pinbelegung](https://www.ti.com/lit/ds/symlink/tlv803e.pdf)

Die Dateien im übergeordneten `hardware/` und unter `manufacturing/JLCPCB/Rev06/` beschreiben weiterhin Rev.0.6. Sie dürfen für die neue Messvariante nicht mit Rev.0.7-Dateien vermischt werden.
