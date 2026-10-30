# Projektstand und nächste Aktualisierung

## Vorgemerkt: HMX-Workflow warten

Bei der nächsten Aktualisierung `.github/workflows/hmx.yml` im Repository-Hauptordner prüfen (vorgemerkt am 26.10.2026):

- `actions/checkout@v4`, `actions/upload-artifact@v4` und `arduino/setup-arduino-cli@v2` auf geeignete Versionen mit nativer Node.js-24-Unterstützung prüfen und aktualisieren. Verfügbare Versionen und Kompatibilität dann neu prüfen.
- Statt `ubuntu-latest` eine bewusst gewählte Ubuntu-Version, beispielsweise `ubuntu-24.04`, verwenden, um automatische Wechsel der Betriebssystemversion zu vermeiden. Vor der Festlegung Kompatibilität mit der ESP32-Toolchain prüfen.
- Danach den vollständigen HMX-Build einschließlich Regressionstests und Artefakt-Upload ausführen und die Warnungen erneut kontrollieren.

Anlass: Der [erfolgreiche Lauf 40388178334](https://github.com/ralf-e/HeishaMon/actions/runs/40388178334) meldet die Node.js-20-Abkündigung und die Umstellung von `ubuntu-latest` auf Ubuntu 26.04. Der Workflow bleibt bis zur nächsten Aktualisierung unverändert.

Quellen: [Node.js-Umstellung](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/) und [Ubuntu-Umstellung](https://github.com/actions/runner-images/issues/14748).

## Hardware Rev.0.7: Spannungsmessung vorbereitet

Die neue [Adaptervariante](../hardware/Rev07/README.md) ergänzt ADS1115 (0x48), vier Spannungsteiler, TMUX1511 und 2,93-V-Supervisor auf weiterhin 23×41 mm / zwei Lagen. Rev.0.6 und deren Firmware bleiben erhalten. Rev.0.7 hat ERC/DRC 0 und keine offenen Verbindungen; Hardwaretest und Fertigungsfreigabe stehen aus.

Noch erforderlich: ADC-Auswertung in der Firmware mit Erkennung des optionalen Bausteins, MCP-GP0 als Messfreigabe, korrekten Teilerfaktoren und Kalibrierung; Anzeige und gegebenenfalls MQTT; passende Tests und ESP32-S3-Build. Die aktuelle dev.7 enthält dies noch nicht.

Bestellprüfung am 30.10.2026 durchgeführt: alle 18 SMD-Typen bestellbar, engster Posten U4 mit 20 Stück. Nummerierte Lieferanten-Pads abgeglichen; U4-CPL von 0° auf 180° korrigiert. R15/R19/R23/R27 von 1 MΩ auf 100 kΩ geändert, um den maximal spezifizierten Powered-off-Leckstrom rechnerisch abzuführen; Teilerfaktoren entsprechend aktualisiert. ERC/DRC und Verbindungsprüfung erneut sauber. [Prüfbericht, Kontaktmessliste und 1:1-Passschablone](../hardware/Rev07/Bestellpruefung.md) liegen vor. Vor Bestellung bleiben Hersteller-Preview/Zentrierung, reale V6-Kontakte/Passform und Auswahl der Stapelkontakte anhand gemessener Höhen offen. Funktionstests am gefertigten Prototyp sind separat aufgeführt und noch nicht durchgeführt.

## Modellanzeige dev.7

Implementiert: 83 Einträge aus upstream-reference/HeatPumpType.md; Generator tools/update_model_table.py; getrennte Module extension/hmx_model.h und hmx_model_data.h. Quelle/Commit im generierten Katalog docs/model_catalogue.json.

Linker Kopf-Button: Modell/Geräteinfo. Rechter Kopf-Button: kurzes Antippen öffnet die Betriebsartenwahl. Gerätedetails enthalten Rohkennung, Community-Zuordnung, HeishaMon-Versionsstring/Basiscommit und HMX-Version. TOP92 über MQTT/JSON bleibt unverändert.

Die Tabelle wird separat gepflegt, ist aktuell aber in der Firmware kompiliert. Eine spätere separat aktualisierbare Laufzeit-Datei bleibt optional; sie ist noch nicht implementiert.

Der vollständige dev.7-Build und die Regressionstests waren im HMX-Actions-Lauf 40380596372 erfolgreich. Hardwaretests stehen weiterhin aus.

Hintergrund: https://github.com/heishamon/HeishaMon/issues/634#issuecomment-2605306904 und https://github.com/heishamon/HeishaMon/issues/910#issuecomment-4660654706
