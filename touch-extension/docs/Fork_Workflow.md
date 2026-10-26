# HeishaMon Touch: Arbeiten im GitHub-Fork

Stand: 26.10.2026. Software 0.1.0-dev.7, Hardware Rev.0.6. Hardware noch nicht getestet.

## Aufbau und Zuständigkeiten

Repository: https://github.com/ralf-e/HeishaMon (öffentlicher Fork von heishamon/HeishaMon).

- `main`: unveränderter offizieller Stand; hier keine Displayänderungen einpflegen.
- `touch-display`: Display-Erweiterung und eigener Build-Workflow.
- `HeishaMon/`: offizielle Quelltexte. Auf dem Erweiterungsbranch bleiben sie ebenfalls unverändert.
- `touch-extension/extension/`: einzige gepflegte Quelle der Displaymodule.
- `touch-extension/tools/apply_extension.py`: exakt geprüfte Integrationspunkte für zwei offizielle Dateien.
- `touch-extension/firmware/`: erzeugter Sketch, von Git ausgeschlossen; niemals als zweite Quelle pflegen.
- `touch-extension/hardware/`, `manufacturing/`, `docs/`: Schaltung, PCB, Fertigung und Dokumentation.

Der zusätzliche Ordner vermeidet unter Windows die Kollision von Upstreams `Tools/` mit unseren `tools/`. Die bisherige Arbeitskopie außerhalb des Unterordners `fork` bleibt als vorheriger Projektstand erhalten. Ab jetzt am Fork arbeiten.

Die vollständige bisherige Git-Historie des Originalprojekts bleibt erhalten. Die lokale ältere Entwicklungsarbeit wird mit einem gemeinsamen Import-Commit übernommen; eine früher nicht vorhandene eigene Commit-Historie wird nicht nachträglich erfunden.

## Windows: Build mit Arduino CLI

Python 3, Git und Arduino CLI müssen verfügbar sein. Die Arduino-Bibliotheken und Boardeinstellungen stehen in `Build_Installation.md`. Der HMX-Workflow verwendet ESP32-Core **3.3.12** und die dort eingetragenen Bibliotheksversionen.

Für die hier angelegte Arbeitskopie, aus jedem PowerShell-Verzeichnis:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File 'D:\ChatGPT_CODEX\HeishaMon\fork\touch-extension\tools\build.ps1' -ArduinoCli 'C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
~~~

Bei abweichender Python-Installation zusätzlich `-Python 'C:\Pfad\python.exe'` angeben. Kein Wechsel des aktuellen Verzeichnisses nötig.

Das Skript führt zuerst `prepare_firmware.py` aus. Es exportiert die geprüfte Git-Basis, vergleicht die Arbeitskopie mit ihren 73 Originaldateien (Windows-Zeilenenden dürfen abweichen) und integriert die Erweiterung in eine isolierte Kopie. Unveränderte alte erzeugte Kopien landen bei erneutem Vorbereiten unter `archive/generated-*`; manuelle Änderungen an bereits erfassten Sketchdateien führen zu einem Stopp und werden erhalten. Zusätzliche Dateien einer früheren IDE-Sitzung bleiben mit der archivierten Kopie erhalten.

Ergebnisse liegen unter `touch-extension/output/firmware/`: benannte Application-BIN samt MD5 im Dateinamen und `firmware_manifest.json` mit SHA256 und Quellprüfsummen. Ein fehlgeschlagener Build erzeugt kein neues Freigabepaket. Alte Dateien im Ausgabeordner gelten dadurch nicht als aktueller Build; Manifest und Version prüfen.

## Windows: Arduino IDE 2

Zuerst den Sketch erzeugen:

~~~powershell
python 'D:\ChatGPT_CODEX\HeishaMon\fork\touch-extension\tools\prepare_firmware.py'
~~~

Dann ausschließlich `D:\ChatGPT_CODEX\HeishaMon\fork\touch-extension\firmware\HeishaMon\HeishaMon.ino` öffnen. Der originale Sketch im Repository-Hauptordner enthält die Erweiterung nicht.

ESP32S3 Dev Module, USB CDC On Boot aktiviert, QSPI-PSRAM und Partition `Minimal SPIFFS (1.9MB APP with OTA/190KB SPIFFS)` wählen. Bibliotheken gemäß `Build_Installation.md` einrichten; die mitgelieferte NeoPixel-Bibliothek bei Bedarf wie dort beschrieben hinzufügen. `vendor/DisplayFont` ist keine Arduino-Bibliothek.

Kompilieren bzw. kompilierte Binärdatei exportieren. Danach die exportierte Application-BIN mit `tools/package_firmware.py AUSGABEORDNER` benennen und prüfen. Die ausführliche IDE-Anleitung gilt weiterhin, mit dem zusätzlichen Pfadbestandteil `fork/touch-extension`. Änderungen am Displaycode immer unter `extension/` durchführen und den Sketch danach neu erzeugen.

## Build auf GitHub

Workflow: `.github/workflows/hmx.yml`, Name **HMX ESP32-S3 build**.

Er läuft bei Änderungen auf `touch-display` an Erweiterung, offiziellen Sketchquellen oder seinem eigenen Workflow. Er prüft Integration, Sketch-Erzeugung, C++-Status-/Modelllogik und Vorschau, installiert Core 3.3.12 und kompiliert die ESP32-S3-Anwendung. Nach Erfolg wird das Actions-Artefakt **HeishaMon-HMX-ESP32S3-development** mit benannter BIN und Manifest bereitgestellt. Dies ist ein Entwicklungsartefakt, kein getestetes Release.

Falls GitHub Actions für den neuen Fork noch deaktiviert sind, im Reiter **Actions** einmal aktivieren. Die manuelle Workflow-Auswahl kann bei einem Workflow, der nur auf einem Nebenbranch liegt, eingeschränkt sein; der Push-Trigger ist der normale Einstieg. Der offizielle Workflow `main.yml` wird auf `touch-display` durch eine Repository-Bedingung vom HMX-Build getrennt, damit er keine unveränderte Standardfirmware als vermeintliche Display-Firmware erzeugt. Auf `main` bleibt die Originaldatei erhalten.

## Installation / Update über HeishaMon-Webinterface

Die Partitionierung wird durch den Fork nicht verändert: weiterhin ESP32-S3 mit `min_spiffs`. Bei bereits passender Partitionierung kann die benannte **Application-BIN** im normalen Webinterface installiert werden. Keine `merged.bin`, Bootloader- oder Partition-BIN dort hochladen. Konservative Grenze: 0x1DF000 Bytes. Bei unbekannter/anderer Partitionierung zuerst die detaillierte USB-Erstinstallationsanleitung beachten.

Der [HMX-Actions-Lauf 40380596372](https://github.com/ralf-e/HeishaMon/actions/runs/40380596372) hat dev.7 auf Commit `bfc89046e7ac04ee628347f56f0198b0bbca997f` erfolgreich gebaut, die Regressionstests bestanden und BIN sowie Manifest als Entwicklungsartefakt bereitgestellt. Hardwaretests stehen weiterhin aus. Die früher lokal gebaute dev.6-BIN gehört nicht zum aktuellen Fork-Quellstand.

## Neue offizielle HeishaMon-Version übernehmen

1. Arbeitskopie sauber committen. `git -C 'D:\ChatGPT_CODEX\HeishaMon\fork' status` prüfen.
2. `git -C 'D:\ChatGPT_CODEX\HeishaMon\fork' fetch upstream`.
3. Auf `main` wechseln und `upstream/main` ausschließlich per Fast-Forward übernehmen. Danach wieder auf `touch-display` wechseln und `main` mergen. Bei Konflikten die eigenen Änderungen erhalten und jeden Konflikt prüfen; kein Force-Push.
4. Änderungen seit dem in `upstream-reference/tree.json` gespeicherten Basiscommit prüfen: insbesondere UART/TX, Startup-Fremdverkehrserkennung, GPIO, Decoder und ESP32-APIs. Die Sketch-Erzeugung stoppt bis zur bewussten Freigabe veränderter Quelldateien.
5. Nach Prüfung die Basisreferenzen aktualisieren: `upstream-reference/tree.json` mit Git-Blob-SHAs aller offiziellen .ino/.cpp/.h-Dateien unter `HeishaMon/`, die beiden Originaldateien `upstream-reference/HeishaMon.ino` und `gpio.cpp`, sowie den Basiscommit in `extension/hmx_config.h`, `tools/apply_extension.py` und `tools/package_firmware.py`. Keine geänderten Integrationsanker erzwingen: Transformationscode bei Bedarf gezielt anpassen.
6. `prepare_firmware.py`, Integrationstests, `test_fork_build.py`, C++-Prüfungen, Modelltabellenprüfung und Vorschautest ausführen. Danach vollständigen ESP32-S3-Build ausführen, Manifest/Größe/Partition kontrollieren und die sicherheitsrelevanten Betriebsarten am Gerät testen.
7. Erst den geprüften Stand committen und nach `origin/touch-display` pushen. `main` getrennt nach `origin/main` pushen, damit es Originalstand bleibt.

Das ist weiterhin eine bewusst überprüfte Übernahme. Offizielle Updates werden nicht unbeaufsichtigt in eine Firmware für die Wärmepumpe eingebaut. Da die offiziellen Quelldateien im Erweiterungsbranch unverändert bleiben, entstehen dort gewöhnlich keine Display-Mergekonflikte; Änderungen der Integrationspunkte werden beim Erzeugen erkannt.

Die Modellzuordnung hat einen eigenen dokumentierten Tabellenstand. Aktualisierung mit `tools/update_model_table.py --commit VOLLSTAENDIGER_GEPRUEFTER_COMMIT`, danach `--check`, neu vorbereiten und neu bauen. Ein neuer HeishaMon-Basiscommit aktualisiert die Modelltabellendaten nicht automatisch.

## Prüfumfang und Lizenz

Die Migration übernimmt Software und Hardware ohne Funktionsänderung. Hinzu kommen Fork-Aufbau, Quellprüfung, Erzeugung des Build-Sketches und CI-Anpassung. Hardwareprüfung, Stromreserve der V6, Passform und realer Betrieb von LCD/Touch/Ethernet sind weiterhin ausstehend.

**Lizenzstand vom 26.10.2026:** Igor Ybema hat in der [Antwort auf Issue #1029](https://github.com/heishamon/HeishaMon/issues/1029#issuecomment-6421009129) die vorgesehene Lizenzierung erläutert. [PR #1030](https://github.com/heishamon/HeishaMon/pull/1030) ergänzt dafür `LICENSE` (MPL-2.0), `THIRD_PARTY_NOTICES.md` sowie Bibliotheks- und README-Hinweise. Der PR ist noch offen und sammelt die Zustimmung der Mitwirkenden; die Antwort stellt die folgenden Bedingungen ausdrücklich unter den Vorbehalt des Merges:

- MPL-2.0 soll für Dateien ohne abweichenden Lizenzheader gelten. Änderungen an HeishaMon-Dateien müssen unter MPL-2.0 veröffentlicht werden; neue eigene Dateien, etwa Display-/Touchmodule, dürfen eine eigene Lizenz erhalten.
- Empfänger einer Firmware-BIN müssen auf den exakt passenden Quellcode hingewiesen werden. Für HMX sind dazu der jeweilige Quellcommit, die Erweiterungsquellen und die Build-Anleitung anzugeben.
- Vorhandene Copyright- und Lizenzhinweise bleiben erhalten. `THIRD_PARTY_NOTICES.md` ist bei BIN-Weitergabe beizulegen oder zu verlinken; Fremdquellen und eingebundene Bibliotheken behalten ihre eigenen Lizenzen. Vollständige Quellen und Build-Anweisungen sollen den Neubau mit geänderten LGPL-Bibliotheken ermöglichen.

Der aktuelle Fork-Basisstand enthält diese neuen Upstream-Lizenzdateien noch nicht. Nach dem Merge sind sie bei einer geprüften Übernahme zu berücksichtigen und bei künftigen BIN-Veröffentlichungen mit dem passenden Quellstand zu verknüpfen.

**Eigene Erweiterungssoftware:** Die eigenen HMX-Softwarebeiträge sind ausdrücklich unter [MPL-2.0](../LICENSE) lizenziert. [LICENSING.md](../LICENSING.md) beschreibt den Geltungsbereich und die Ausnahmen für Upstream-Daten, Fremdkomponenten und Hardwareunterlagen. Diese eigene Lizenzierung gilt unabhängig vom offenen Upstream-PR; sie ersetzt keine Lizenzfreigabe für fremde Beiträge.
