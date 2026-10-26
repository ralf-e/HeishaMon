# HeishaMon V6 Touch - Firmware bauen

Ausführliche Anleitung zu Arduino CLI, Arduino IDE 2 und GitHub Actions. Software 0.1.0-dev.6 / Hardware Rev.0.6. Stand 25.10.2026.

## 14. Firmware bauen: Windows CLI, Arduino IDE oder GitHub Actions

### 14.1 Welcher Weg ist gemeint?

Der bestehende lokale Build verwendet Arduino CLI, nicht die grafische Arduino IDE. CLI und IDE verwenden den ESP32-Arduino-Core samt Compiler. GitHub Actions führt den CLI-Build auf einem Linux-Rechner bei GitHub aus. Alle drei Wege erzeugen eine Application-BIN; deren Installation erfolgt danach über das vorhandene HeishaMon-Webinterface.

| Weg | Auf dem eigenen Rechner benötigt | Ergebnis |
| --- | --- | --- |
| Windows / Arduino CLI | Python 3, Node.js LTS, Arduino CLI | Benannte BIN in output/firmware |
| Arduino IDE 2 | Arduino IDE, Bibliotheken; Python für das beiliegende Paketierungsskript | Exportierte BIN, anschließend mit MD5 benannt |
| GitHub Actions | GitHub-Konto, Browser; GitHub Desktop für den Projekt-Upload | Download-Artefakt mit BIN und Manifest |

Zum Kompilieren und Exportieren muss die V6 nicht per USB angeschlossen sein. Ein Port wird erst beim seriellen Hochladen benötigt; hier wird anschließend das Webinterface benutzt. Die IDE-Schaltfläche Hochladen ist daher nicht Teil dieses Ablaufs.

**Stand dieser Anleitung:** dev.7 enthält die neue Modellanzeige und Kopf-Schaltflächen. Der vollständige Buildversuch vom 26.10.2026 erkennt ESP32-Core 3.3.12, scheitert aber in der Agent-Ausführungsumgebung beim Compilerstart mit dem bekannten DLL-Fehler. dev.7 muss daher noch außerhalb dieser Umgebung neu gebaut werden. Der vorangegangene dev.6-Stand wurde vom Anwender erfolgreich mit Core 4.0.0-alpha1 gebaut; diese alte BIN enthält die neue Modellanzeige noch nicht. IDE-, Actions- und Hardwaretests von dev.7 sind nicht nachgewiesen.

### 14.2 Gemeinsame Vorbereitung und richtige Dateien

1. Das vollständige Projekt-ZIP in einen eigenen Ordner entpacken, zum Beispiel D:\ChatGPT_CODEX\HeishaMon. Nicht direkt innerhalb des ZIP arbeiten.
2. In diesem Hauptordner müssen README.md und die Unterordner firmware, extension, tools, tests, vendor und upstream-reference nebeneinander liegen.
3. Der zu bauende Sketch ist firmware/HeishaMon/HeishaMon.ino. Die Erweiterung ist dort bereits integriert. Nicht nur die Dateien aus extension einzeln in der IDE öffnen.
4. Eigene Hardwareparameter stehen in extension/hmx_config.h. Bei Änderungen an der Erweiterung müssen die installierten Dateien kontrolliert synchronisiert werden; das Integrationsskript überschreibt absichtlich keine abweichende Installation.
5. Für die folgenden PowerShell-Befehle im Explorer den Projekt-Hauptordner öffnen, in die Adresszeile powershell eingeben und Enter drücken. Mit den folgenden Befehlen den Arbeitsordner prüfen:

```powershell
Get-Location
Test-Path .\tools\build.ps1
Test-Path .\firmware\HeishaMon\HeishaMon.ino
```

Beide Test-Path-Ausgaben müssen True sein. Bei False den Ordner mit README.md öffnen und dort ein neues Terminal starten. Befehle einzeln ausführen und nach einer Fehlermeldung zunächst deren Ursache beheben.

Für alle drei Wege gelten dieselben Zielparameter:

| Parameter | Einstellung |
| --- | --- |
| Zielboard | ESP32S3 Dev Module, Kennung esp32:esp32:esp32s3 |
| ESP32-Core | esp32 by Espressif Systems, Version 3.3.12 |
| USB CDC On Boot | Enabled; CLI: CDCOnBoot=cdc |
| PSRAM | QSPI PSRAM; CLI: PSRAM=enabled |
| Partition Scheme | Minimal SPIFFS mit OTA; CLI: PartitionScheme=min_spiffs |
| Flash Size | 4 MB entsprechend der hier verwendeten Build-Konfiguration |
| Sonstige Boardoptionen | Voreinstellungen dieses Boards/Core-Stands |

Zielboard, USB CDC, QSPI-PSRAM und Partitionierung entsprechen dem offiziellen HeishaMon-S3-Buildskript. Für den nächsten lokalen Build und die beiliegende CI-Vorlage ist Core 3.3.12 vorgesehen. PSRAM=enabled heißt beim S3 konkret QSPI PSRAM, nicht OPI. Andere Modulvarianten müssen vor einer Abweichung anhand ihrer Hardware geprüft werden. Die reale Partitionstabelle der vorhandenen V6 wurde hier nicht ausgelesen.

### 14.3 Weg A: Windows mit Arduino CLI - einmalige Einrichtung

**Python installieren:** Auf https://www.python.org/downloads/windows/ einen regulären Python-3-Installer für Windows auswählen. Im klassischen Installer die Option Add python.exe to PATH aktivieren. Alternativ den offiziellen Python Install Manager verwenden. Danach ein neues PowerShell-Fenster öffnen:

```powershell
python --version
```

Erwartet wird Python 3.x. Falls stattdessen der Microsoft Store geöffnet wird, Python-Installation und Windows-App-Ausführungsalias prüfen. Funktioniert auf dem Rechner nur py -3, in allen folgenden Python-Befehlen python durch py -3 ersetzen. Für Integration und Firmware-Paketierung sind keine zusätzlichen pip-Pakete nötig.

**Node.js installieren:** Auf https://nodejs.org/en/download die Windows-LTS-Version installieren und anschließend ein neues Terminal öffnen:

```powershell
node --version
```

Erwartet wird eine Versionsnummer. Node.js wird für den Test der HTML-Displayvorschau gebraucht; es kompiliert nicht die Firmware.

**Arduino CLI installieren:** Auf https://docs.arduino.cc/arduino-cli/installation/ unter Download die passende Windows-Version laden. arduino-cli.exe zum Beispiel nach C:\Tools\ArduinoCLI entpacken. Diesen Ordner über Windows-Suche Umgebungsvariablen bearbeiten > Benutzervariablen > Path > Bearbeiten > Neu hinzufügen. Vorhandene PATH-Einträge beibehalten. Danach PowerShell neu öffnen:

```powershell
arduino-cli version
```

Erwartet wird die CLI-Version. Eine installierte Arduino IDE ersetzt diesen PATH-Schritt nicht automatisch. Als Alternative unterstützt tools/build.ps1 den Parameter -ArduinoCli mit dem vollständigen EXE-Pfad.

**ESP32-Core und Bibliotheken installieren:** Bei Internetzugriff nacheinander im Projekt-Hauptordner ausführen:

```powershell
$espIndex='https://espressif.github.io/arduino-esp32/package_esp32_index.json'
arduino-cli core update-index --additional-urls $espIndex
arduino-cli core install esp32:esp32@3.3.12 --additional-urls $espIndex
arduino-cli lib update-index
arduino-cli lib install "RingBuffer@1.0.5" "PubSubClient@2.8"
arduino-cli lib install "ArduinoJson@7.4.2" "DallasTemperature@4.0.5"
arduino-cli lib install "OneWire@2.3.8" "Adafruit GFX Library@1.12.4"
arduino-cli lib install "Adafruit BusIO"
arduino-cli core list
arduino-cli lib list
```

Erwartet wird der Core esp32:esp32 in Version 3.3.12 und die genannten Bibliotheken. Adafruit NeoPixel 1.15.5 liegt bereits unter vendor/Adafruit_NeoPixel und wird vom Buildskript über --library vendor/Adafruit_NeoPixel eingebunden. vendor/DisplayFont dient der Vorschauerzeugung und wird nicht als zusätzliche Arduino-Bibliothek installiert. Keine zusätzlichen Displaytreiber wie TFT_eSPI oder LVGL nötig.

Erste Downloads und erster Build können mehrere Minuten dauern. Die spätere Kompilierung nutzt lokale Caches. Die hier genannten Versionen entsprechen der beigefügten Workflow-Vorlage; ein Versionswechsel wird nicht automatisch als kompatibel angenommen.

### 14.4 Weg A: prüfen, bauen und BIN finden

Im Projekt-Hauptordner:

```powershell
python tools/apply_extension.py firmware --check
python tests/test_integration.py
node tests/test_preview.mjs
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build.ps1
```

Erwartete Ergebnisse: Die Integrationsprüfung meldet HMX already installed; all tracked hashes match. Die Python-Tests melden sechs erfolgreiche Tests und OK. Der Vorschautest endet mit seiner OK-Meldung. Erst nach erfolgreicher Kompilierung gibt das Buildskript Web-Update: und den Pfad zur benannten BIN aus.

ExecutionPolicy Bypass gilt hier nur für diesen PowerShell-Aufruf. Es wird keine dauerhafte Ausführungsrichtlinie geändert.

Ergebnisordner: output/firmware. Die relevante Datei heißt HeishaMon_ESP32-HMX-0.1.0-dev.7-<md5>.bin. Die spitzen Klammern stehen für die tatsächliche 32-stellige MD5-Prüfsumme und werden nicht mitgetippt. Das Skript prüft die Größe und benennt nur nach einem erfolgreichen Compiler-Aufruf eine Application-BIN.

Optional zusätzlich das Firmware-Manifest erzeugen:

```powershell
python tools/package_firmware.py output/firmware
```

Dieses Skript erwartet eine vorhandene HeishaMon.ino.bin, prüft deren Magic-Byte und Größe, erzeugt die benannte Kopie sowie firmware_manifest.json mit MD5 und SHA256. Es kompiliert selbst nicht.

Alternative, wenn arduino-cli.exe nicht im PATH liegt:

```powershell
$cli='C:\Tools\ArduinoCLI\arduino-cli.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build.ps1 -ArduinoCli $cli
```

Die Einrichtungsschritte davor ebenfalls mit diesem EXE-Pfad aufrufen, zum Beispiel & $cli version. Falls CLI eine eigene YAML-Konfiguration braucht, unterstützt build.ps1 zusätzlich -ConfigFile mit deren Pfad. IDE und CLI können unterschiedliche Daten- und Bibliotheksordner verwenden; bei fehlenden Bibliotheken arduino-cli config dump kontrollieren.

### 14.5 Weg B: Arduino IDE 2 einrichten

1. Arduino IDE 2 von https://www.arduino.cc/en/software/ installieren und öffnen.
2. Datei > Voreinstellungen / File > Preferences öffnen. Bei Zusätzliche Boardverwalter-URLs die folgende URL als weiteren Eintrag ergänzen. Vorhandene URLs beibehalten:

```text
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

3. Den Boardverwalter / Boards Manager öffnen. Nach esp32 suchen, esp32 by Espressif Systems auswählen und Version 3.3.12 installieren.
4. Unter Werkzeuge > Board / Tools > Board das ESP32S3 Dev Module auswählen.
5. Unter Werkzeuge die Einstellungen aus der Tabelle in 14.2 setzen: USB CDC Enabled, PSRAM QSPI PSRAM, Flash Size 4MB und Minimal SPIFFS mit OTA. Je nach Core-Version enthält der Menütext eine gerundete App-/SPIFFS-Größe; entscheidend ist die Option min_spiffs. Nicht Huge APP oder ein Schema ohne OTA wählen.
6. Über den Bibliotheksverwalter / Library Manager die Bibliotheken aus folgender Tabelle installieren. Falls eine Versionsauswahl angeboten wird, die angegebene Version nehmen. Erforderliche Abhängigkeiten, insbesondere Adafruit BusIO, mitinstallieren.

| Bibliothek | Version / Herkunft |
| --- | --- |
| RingBuffer | 1.0.5 |
| PubSubClient | 2.8 |
| ArduinoJson | 7.4.2 |
| DallasTemperature | 4.0.5 |
| OneWire | 2.3.8 |
| Adafruit GFX Library | 1.12.4 |
| Adafruit BusIO | Über Bibliotheksverwalter / Abhängigkeitsdialog |
| Adafruit NeoPixel | 1.15.5; dieselbe Version wie im Projekt-vendor |

Die IDE übernimmt --library vendor/Adafruit_NeoPixel aus dem PowerShell-Skript nicht. Deshalb NeoPixel hier ausdrücklich installieren. Falls diese Version im Manager nicht verfügbar ist, bei geschlossener IDE den kompletten Ordner vendor/Adafruit_NeoPixel nach <Sketchbook>/libraries/Adafruit_NeoPixel kopieren. Den Sketchbook-Pfad zeigt Datei > Voreinstellungen. Vorhandene Bibliotheken nicht ungeprüft überschreiben; doppelte NeoPixel-Installationen zuerst vergleichen. Anschließend IDE neu starten.

7. Datei > Öffnen und firmware/HeishaMon/HeishaMon.ino auswählen. Alle zum Sketch gehörenden Dateien bleiben im mitgelieferten Ordner, einschließlich src/hmx.
8. Optional in Voreinstellungen die ausführliche Ausgabe beim Kompilieren einschalten. Das erleichtert die Prüfung verwendeter Bibliotheksversionen und die Fehlersuche.

### 14.6 Weg B: in der IDE kompilieren, exportieren und benennen

1. Zunächst Überprüfen / Verify (Häkchen) wählen. Die IDE muss ohne Compilerfehler abschließen. Ein erfolgreiches Verify allein erzeugt noch keine zuverlässig auffindbare Exportdatei für diesen Ablauf.
2. Sketch > Kompilierte Binärdatei exportieren / Sketch > Export Compiled Binary wählen. Der Sketch wird gegebenenfalls erneut gebaut.
3. Über Sketch > Sketch-Ordner anzeigen / Show Sketch Folder den Ordner firmware/HeishaMon öffnen. Die ESP32-IDE-2-Ausgabe liegt üblicherweise darunter in build/esp32.esp32.esp32s3. Falls abweichend, nach der gerade erzeugten HeishaMon.ino.bin suchen und Zeitstempel kontrollieren.
4. Ausschließlich die Application-Datei HeishaMon.ino.bin verwenden. Nicht HeishaMon.ino.bootloader.bin, HeishaMon.ino.partitions.bin, eine merged.bin oder eine with_bootloader-Datei.
5. Zur Größenprüfung, MD5-Benennung und Erzeugung des Manifests das beiliegende Paketierungsskript benutzen. Dazu Python wie in 14.3 einrichten und im Projekt-Hauptordner den tatsächlich vorhandenen Exportordner angeben:

```powershell
$exportDir='firmware/HeishaMon/build/esp32.esp32.esp32s3'
Test-Path (Join-Path $exportDir 'HeishaMon.ino.bin')
python tools/package_firmware.py $exportDir
```

Test-Path muss True liefern. Bei False den Exportordner anpassen und nicht mit einer zufällig noch vorhandenen alten BIN weiterarbeiten. Das Skript schreibt die benannte HeishaMon_ESP32-HMX-0.1.0-dev.7-<md5>.bin und firmware_manifest.json direkt in diesen Exportordner.

Die IDE meldet eventuell nur, dass das Programm in den regulären App-Slot passt. Für den vorhandenen Web-Updater ist zusätzlich die konservative Grenze 0x1DF000 Byte einzuhalten; das Paketierungsskript prüft genau diese Grenze.

Die IDE führt die Python-Integrations- und Node-Vorschautests nicht automatisch aus. Diese bei vorhandenen Werkzeugen wie in 14.4 separat ausführen. Ein erfolgreicher IDE-Build ersetzt keine Hardware-Funktionsprüfung.

### 14.7 Weg C: GitHub Actions ohne lokalen ESP32-Compiler

Hier kompiliert GitHub auf Linux. Auf dem eigenen Rechner werden weder ESP32-Compiler noch Arduino CLI oder IDE benötigt. Die Vorlage liegt unter tools/HMX_build_workflow.yml; sie wird nicht automatisch durch das Herunterladen des Projekt-ZIP aktiv. Es wird ein eigenes Repository mit Schreibzugriff benötigt.

**Eigenes Repository mit GitHub Desktop vorbereiten:**

1. GitHub-Konto anlegen beziehungsweise anmelden. GitHub Desktop von https://desktop.github.com/ installieren und dort anmelden.
2. Eine Arbeitskopie des entpackten Projektordners verwenden. In deren Hauptordner liegt die mitgelieferte .gitignore. Im Explorer unter Ansicht die Anzeige ausgeblendeter Elemente aktivieren, falls die Datei nicht sichtbar ist.
3. In GitHub Desktop File > Add local repository wählen und genau diesen Hauptordner auswählen. Falls er noch kein Git-Repository ist, den angebotenen Link create a repository here verwenden. Vor dem Bestätigen den endgültigen Pfad kontrollieren, damit kein zusätzlicher gleichnamiger Unterordner entsteht.
4. Die Vorlage im Projektordner an den für GitHub erforderlichen Ort kopieren. Dazu PowerShell im Hauptordner öffnen:

```powershell
New-Item -ItemType Directory -Force .github\workflows | Out-Null
Copy-Item .\tools\HMX_build_workflow.yml .\.github\workflows\hmx-build.yml
Test-Path .\.github\workflows\hmx-build.yml
```

5. Zurück in GitHub Desktop die Änderungen prüfen und als ersten Commit speichern, beispielsweise mit der Zusammenfassung HeishaMon Touch Build vorbereiten.
6. Publish repository wählen. Einen eigenen Namen vergeben, zum Beispiel HeishaMon-Touch. Private Veröffentlichung ist möglich; dann Keep this code private aktiviert lassen. Aktionen und mögliche Kontingente richten sich nach dem GitHub-Konto. Anschließend Repository veröffentlichen.
7. Im Browser im Repository prüfen, ob firmware/HeishaMon/HeishaMon.ino, vendor/Adafruit_NeoPixel, tools, tests und upstream-reference tatsächlich vorhanden sind. Die Ordner dürfen nicht versehentlich in einer zusätzlichen ZIP-Verzeichnisebene liegen.
8. Unter .github/workflows muss hmx-build.yml auf dem Standardbranch, üblicherweise main, sichtbar sein. output und archive sind durch .gitignore absichtlich vom Repository ausgeschlossen.

Ein einfacher Fork des unveränderten offiziellen HeishaMon reicht nicht aus: Der Workflow benötigt unser vollständiges Projekt mit integrierter Erweiterung, Prüfdateien und vendor-Inhalt. GitHub Desktop benötigt für diesen Ablauf keinen zusätzlichen lokalen Git-CLI-Aufruf.

**Build starten und verfolgen:**

1. Im eigenen Repository den Reiter Actions öffnen.
2. Falls GitHub eine Aktivierung der Workflows verlangt, diese im eigenen Repository freigeben. Bei organisationsseitiger Sperre sind die Repository-/Organisationsregeln maßgeblich.
3. Links HMX ESP32-S3 build auswählen.
4. Run workflow anklicken, den Standardbranch auswählen und mit Run workflow starten. Der Workflow muss für diesen Knopf auf dem Standardbranch liegen und workflow_dispatch enthalten; beides ist mit der genannten Einrichtung vorgesehen.
5. Den neu angelegten Lauf öffnen. Der Job build prüft Python-/C++-Regressionsfälle und Integration, installiert Core/Bibliotheken, kompiliert den Sketch und paketiert die BIN. Die dev.7-Vorlage prüft zusätzlich Modellzuordnung, Tabellenreproduktion und HTML-Vorschau.
6. Erst bei grünem Abschluss mit dem Download fortfahren. Ein roter Schritt bedeutet: dessen Protokoll öffnen, Fehlermeldung beheben, Änderung committen und Push origin ausführen. Danach einen neuen Lauf starten. Ein grüner Build ist ein Compiler-Nachweis, kein Nachweis erfolgreicher Hardwaretests.

Die Vorlage startet außerdem bei Pushes mit Änderungen unter extension, firmware, tools oder tests. Der manuelle Start bleibt möglich. Ein Workflow-Lauf veröffentlicht die Firmware nicht automatisch als GitHub Release und installiert nichts auf der V6.

**Fertige BIN herunterladen:**

1. Auf der Übersichtsseite des erfolgreichen Laufs zum Abschnitt Artifacts scrollen.
2. HeishaMon-HMX-ESP32S3-development anklicken. Zum Download bei GitHub angemeldet sein.
3. Das heruntergeladene ZIP entpacken. Darin müssen die benannte HeishaMon_ESP32-HMX-0.1.0-dev.7-<md5>.bin und firmware_manifest.json enthalten sein. Eventuelle Unterordner mit öffnen.
4. Im Manifest Ziel ESP32-S3, Erweiterungsversion, Dateigröße und MD5 prüfen. Das Feld hardware_tested bleibt false, solange kein separater Hardwaretest dokumentiert ist.
5. Die benannte BIN lokal aufbewahren und mit Kapitel 15 fortfahren. Das Artefakt-ZIP selbst nicht im HeishaMon hochladen.

Falls kein Run-workflow-Knopf erscheint: Standardbranch, Dateipfad .github/workflows/..., workflow_dispatch und Schreibrechte prüfen. Falls Artifacts fehlt: erfolgreichen Abschluss des Upload-artifact-Schritts prüfen. Artefakte können ablaufen; benötigte BIN und Manifest rechtzeitig lokal sichern.

### 14.8 BIN prüfen und typische Fehler unterscheiden

Für alle Wege gilt: Nur die BIN des letzten tatsächlich erfolgreichen Builds verwenden. Nach einem fehlgeschlagenen Build können alte Dateien im Ausgabeordner liegen. Zeitstempel, Versionsangabe, Buildprotokoll und gegebenenfalls Manifest zusammen betrachten.

```powershell
$image=Get-ChildItem .\output\firmware\HeishaMon_ESP32-HMX-*.bin
$image | Select-Object Name,Length,LastWriteTime
```

Dieser Ordner gilt für den CLI-Weg. Beim IDE-Weg den Exportordner und beim Actions-Weg den entpackten Downloadordner verwenden. Falls mehrere BINs vorhanden sind, die zum ausgewählten erfolgreichen Build gehörende Datei gezielt bestimmen. MD5 für eine konkret ausgewählte Datei:

```powershell
$bin='D:\Pfad\Zur\ausgewaehlten.bin'
Get-FileHash -LiteralPath $bin -Algorithm MD5
```

Die tatsächliche Prüfsumme muss mit dem Dateinamen beziehungsweise Manifest übereinstimmen. Die Dateigröße darf 0x1DF000 Byte, also 1.961.984 Byte, nicht überschreiten. Die Build- und Paketierungsskripte brechen bei Übergröße ab. Ein normales Application-Update ändert keine Partitionstabelle.

| Meldung / Situation | Nächster Schritt |
| --- | --- |
| python, node oder arduino-cli nicht gefunden | Installation und PATH kontrollieren; neues Terminal öffnen |
| Datei oder Sketch nicht gefunden | Hauptordner und Test-Path aus 14.2 prüfen |
| Header/Bibliothek fehlt | Genannte Bibliothek im verwendeten CLI-/IDE-Profil installieren; vendor bei CLI mitnehmen |
| Changed installed file / Partial integration | Abweichung prüfen; keinen erzwungenen Neuauftrag über den bearbeiteten Sketch laufen lassen |
| Illegales Verschieben einer System-DLL | Lokaler Compiler startet nicht; kein Firmwarefehler nachgewiesen. Toolchain-/Windows-Umgebung reparieren oder Linux-Actions-Weg verwenden |
| IDE zeigt denselben DLL-Fehler | IDE benutzt ebenfalls den lokalen Xtensa-Compiler; bloßer Wechsel von CLI zur IDE behebt das nicht zwingend |
| Fehler in C++-Quellcode oder Linker | Erste relevante Fehlermeldung und Bibliotheks-/Core-Versionen prüfen; noch keine fertige BIN annehmen |
| Application exceeds ... / Sketch too big | Nicht flashen; Größe und Konfiguration prüfen. Nicht ungeprüft auf ein OTA-loses Schema umstellen |
| Web-Upload meldet MD5-Fehler | ZIP entpacken, richtige Application-BIN wählen und MD5 erneut vergleichen |
| Web-Upload meldet zu wenig Platz / keine Partition | Vorhandene Flash-Aufteilung untersuchen; nicht durch Umbenennen oder merged.bin umgehen |

Die gemeinsame Build-Konfiguration verwendet min_spiffs wie das offizielle HeishaMon-S3-Skript. Die App-Slots haben in diesem 4-MB-Schema je 0x1E0000 Byte. Der Web-Updater reserviert zusätzlich 4 KiB; daher die kleinere Grenze. Erst ein erfolgreicher Build zeigt, ob unsere erweiterte Firmware hineinpasst.

### 14.9 Spätere Builds, Upstream-Versionen und Quellen

Nur neu kompilieren, ohne neue Upstream-Version: denselben gewählten Weg wiederholen, aktuelle Konfiguration und Quellstände behalten und nach erfolgreichem Build wieder die neue Application-BIN verwenden.

Neue HeishaMon-Version übernehmen: zunächst Kapitel 16 abarbeiten. Ein Update des ESP32-Cores oder eine frische Original-HeishaMon-BIN integriert unsere Erweiterung nicht automatisch. Beim Wechsel der Softwareversion auch die Versionsangaben in Buildskript, Paketierung, Manifest und Anleitung konsistent aktualisieren. Ein vorhandenes grünes Actions-Ergebnis für einen älteren Commit gilt nicht als Build-Nachweis für neue Quellen.

Offizielle Anleitungen, geprüft am 25.10.2026:

- Arduino CLI installieren: https://docs.arduino.cc/arduino-cli/installation/
- Arduino IDE herunterladen: https://www.arduino.cc/en/software/
- ESP32-IDE-Werkzeugmenü und PSRAM: https://docs.espressif.com/projects/arduino-esp32/en/latest/guides/tools_menu.html
- Arduino Exportrezepte: https://docs.arduino.cc/arduino-cli/platform-specification/
- Python für Windows: https://www.python.org/downloads/windows/
- Node.js LTS: https://nodejs.org/en/download
- GitHub Desktop, lokales Repository hinzufügen: https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-a-repository-from-your-local-computer-to-github-desktop
- GitHub Workflow manuell starten: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- GitHub Build-Artefakte herunterladen: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- Offizielles HeishaMon-S3-Buildskript: https://github.com/heishamon/HeishaMon/blob/main/scripts/build_esp32s3.sh
