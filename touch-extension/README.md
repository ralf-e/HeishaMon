# HeishaMon V6 Touch – Software 0.1.0-dev.7 / Hardware Rev.0.6

Waveshare SKU29318, 480×320 quer, 6×8-Schrift und 20 Zeilen pro Seite. Die Übersicht zeigt 20 Werte einschließlich WW/HK1/HK2-Status und Ist/Soll, Haupttimer und Puffer. Automatisch / Listen only wird per Touch gewählt und im ESP32-NVS gespeichert. Kein mechanischer Schalter.

## GitHub-Fork: Einstieg

Dieser Ordner enthält die gepflegte Erweiterung. Die offiziellen Quellen liegen im Repository unter `HeishaMon/`; `main` bleibt unverändert. Der Build-Sketch unter `touch-extension/firmware/` wird aus der geprüften Basis erzeugt und ist nicht versioniert. **Zuerst [Fork- und Update-Anleitung](docs/Fork_Workflow.md) lesen.** Sie ergänzt die bisherigen Anleitungen um die neuen Pfade und hat für den Fork Vorrang.

Markdown-Anleitung und PDF beschreiben den Fork-Aufbau. Die Build-Anleitung verlinkt die zentral gepflegten Schritte für Actions, CLI und IDE; Upstream-Updates stehen in der Fork-Anleitung.

**Lizenz:** Die eigene Erweiterungssoftware steht unter [MPL-2.0](LICENSE). [Geltungsbereich und Ausnahmen](LICENSING.md) grenzen Fremdquellen, Modelltabellendaten und Hardwareunterlagen ab. Upstream hat auf [Issue #1029](https://github.com/heishamon/HeishaMon/issues/1029#issuecomment-6421009129) mit einem MPL-2.0-Vorschlag in [PR #1030](https://github.com/heishamon/HeishaMon/pull/1030) reagiert; Stand 26.10.2026 ist dieser PR noch offen. Einzelheiten für die gesamte Firmware stehen in den [Lizenzhinweisen zum Fork](docs/Fork_Workflow.md#prüfumfang-und-lizenz).

## Einstieg

- [Build-Anleitung: Windows CLI, Arduino IDE und GitHub Actions](docs/Build_Installation.md)
- [Anleitung als Markdown](docs/HeishaMon_V6_Touch_Anleitung.md)
- [Anleitung als PDF](docs/HeishaMon_V6_Touch_Anleitung_dev7_Rev06.pdf)
- [Interaktive Display-Vorschau](docs/Display_Vorschau.html), lokal im Browser öffnen; ausschließlich Demo-Daten und eigener Browser-Speicher.
- [KiCad-Projekt](hardware/HeishaMon_V6_Touch_Adapter.kicad_pro)
- [JLCPCB-Fertigungsanleitung und Verfügbarkeit](manufacturing/JLCPCB/Rev06/README_JLCPCB.md)

## Projektstruktur

| Ordner | Inhalt |
| --- | --- |
| extension/ | Gepflegte Erweiterungsmodule, unabhängig vom Upstream |
| firmware/HeishaMon/ | Erzeugter integrierter Sketch, nicht versioniert |
| hardware/ | Aktueller Schaltplan, geroutete PCB, Regeln und Prüfberichte |
| manufacturing/JLCPCB/Rev06/ | Gerber, Bohrung, SMD-BOM, CPL, Bestände und Alternativen |
| docs/ | Anleitung, Schaltplanabbildungen und Display-Vorschau |
| output/ | Nur aktuelle Downloadpakete und PDF |
| tools/ | Integration, Build, Tests und reproduzierbare Exporte |
| tests/ | Integrations-, Betriebsarten- und Vorschautests |
| upstream-reference/ | Unveränderte Ausgangsdateien und Herkunftsnachweis |
| vendor/ | Benötigte mitgelieferte Bibliothek/Schrift samt Lizenzen |
| archive/ | Frühere Entwürfe, getrennt vom aktuellen Stand |
| validation/ | Aktuelle Prüfprotokolle |

## Hardware und Fertigung

23×41 mm, zwei Kupferlagen, 1,6 mm. GH-Side-Entry-Buchse SM15B-GHS-TB am linken F-Rand, montiert unten rechts; J3 gegenüber auf B, montiert oben links. F-Seite mit SMD und LCD liegt montiert unten; manuelle Stiftleisten auf B liegen oben. Die um 180° gekippte Kontaktzuordnung wurde am PCB geprüft. Gegenüber 28×94 mm reduziert sich die Fläche um 64,2 %.

ERC 0 Verstöße, DRC 0 Verstöße und 0 offene Verbindungen. 21 Netze. Die JLCPCB-BOM und CPL enthalten identische 16 SMD-Referenzen in 9 Gruppen. J1/J2/J3 werden manuell bestückt und fehlen in diesen Listen; ihre 20 Bohrungen bleiben in den Gerber-/Bohrdaten erhalten. Bei JLC **Top Side** wählen, obwohl F im eingebauten Zustand unten liegt.

Prototyp-Fertigungsdaten: Mechanik, V6-Stromreserve und tatsächliche Funktion sind noch nicht am Original bestätigt. Bestückungsorientierung und DFM-Hinweise in der Fertigungsanleitung prüfen.

## Software und Prüfungen

tools/prepare_firmware.py erzeugt den Build-Sketch aus der geprüften Git-Basis; tools/apply_extension.py integriert die Erweiterung dabei in zwei Dateien der erzeugten Kopie. Die offiziellen Quellen bleiben unverändert. Lokal erzeugt tools/build.ps1 die Application-BIN für das Webinterface. Auf GitHub ist ausschließlich .github/workflows/hmx.yml im Repository-Hauptordner der aktive HMX-Workflow; die ältere Datei tools/HMX_build_workflow.yml wird für den Fork nicht benötigt.

**dev.7 erfolgreich gebaut:** Der [HMX-Actions-Lauf 40380596372](https://github.com/ralf-e/HeishaMon/actions/runs/40380596372) hat Commit `bfc89046e7ac04ee628347f56f0198b0bbca997f` mit ESP32-Core 3.3.12 kompiliert, die Regressionstests bestanden und das Entwicklungsartefakt `HeishaMon-HMX-ESP32S3-development` mit Application-BIN und Manifest bereitgestellt. Hardwaretests stehen weiterhin aus. Für Build und Installation im Fork gilt die [Fork-Anleitung](docs/Fork_Workflow.md).

Grundprüfungen:

    python tools/prepare_firmware.py
    python tests/test_integration.py
    python tests/test_fork_build.py
    python tools/apply_extension.py firmware --check
    node tests/test_preview.mjs
    g++ -std=c++17 -fsyntax-only tests/policy_compile.cpp
    python tools/check_hardware.py

Der letzte Befehl gleicht gespeicherte KiCad-Exporte und den tatsächlichen PCB-Audit ab. Bei Änderungen zuerst ERC, DRC und Netzliste neu exportieren. KiCad-Python wird für tools/design_adapter.py, tools/pcb_io.py und tools/export_jlcpcb.py benötigt. Details und die reproduzierbare Routingfolge stehen in hardware/README.md. Der Ausgangsgenerator überschreibt absichtlich PCB und Schaltplan; manuelle Änderungen vorher sichern.

## Modellanzeige ab dev.7

Linker Kopf-Button öffnet die Geräteinfo, rechter die Betriebsartenwahl. Tabellenstand und Pflege: [Modellmodul](docs/NEXT_STEPS.md). HeishaMon-Basisversion/Commit und HMX-Version werden getrennt angezeigt.
