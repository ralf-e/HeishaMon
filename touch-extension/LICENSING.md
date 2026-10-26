# Lizenz der HMX-Erweiterungssoftware

Die eigenen Softwarebeiträge zur HeishaMon-Touch-Erweiterung werden unter der **Mozilla Public License 2.0 (MPL-2.0)** bereitgestellt. Der vollständige Lizenztext steht in [LICENSE](LICENSE).

Dies gilt für den eigenen Code in `extension/`, `tools/` und `tests/` sowie den eigenen HTML-/JavaScript-Code der Displayvorschau unter `docs/`. Vorhandene abweichende Lizenz- und Herkunftshinweise bleiben maßgeblich. In den eigenen Displaymodulen kennzeichnet `SPDX-License-Identifier: MPL-2.0` die Lizenz.

## Fremdquellen und weitere Projektdateien

- Die aus Upstream übernommenen Modelltabellendaten in `extension/hmx_model_data.h`, `docs/model_catalogue.json` und den Vorschau-Daten behalten ihre Herkunft und die jeweils geltenden Upstream-Bedingungen. Die Lizenzierung des eigenen Generators vergibt keine zusätzlichen Rechte an diesen Quelldaten.
- Offizielle HeishaMon-Quellen, `upstream-reference/`, erzeugte Kopien unter `firmware/` und eingebundene Fremdbibliotheken werden durch diese Erklärung nicht neu lizenziert. Bestehende Copyright- und Lizenzhinweise bleiben erhalten. Den Stand der Upstream-Lizenzklärung beschreibt die [Fork-Anleitung](docs/Fork_Workflow.md#prüfumfang-und-lizenz).
- NeoPixel und die mitgelieferte Schrift behalten ihre Lizenzdateien unter `vendor/Adafruit_NeoPixel/COPYING` und `vendor/DisplayFont/LICENSE.txt`. Weitere eingebundene Bibliotheken behalten ihre eigenen Lizenzen.
- Diese Softwarelizenz vergibt keine Pauschallizenz für Hardwareentwürfe, Fertigungsdaten, Dokumentation oder Abbildungen.

## Weitergabe der Software und Firmware

Bei Weitergabe der eigenen MPL-2.0-Software deren Copyright- und Lizenzhinweise erhalten und Änderungen an diesen Dateien ebenfalls unter MPL-2.0 zugänglich machen. Empfänger einer Firmware-BIN auf den dazu passenden Quellcommit und die [Build-Anleitung](docs/Build_Installation.md) hinweisen. Der Quellstand liegt im [Branch touch-display](https://github.com/ralf-e/HeishaMon/tree/touch-display); für eine konkrete BIN ist der zugehörige vollständige Commit anzugeben.

Die eigene MPL-2.0-Lizenzierung gilt unabhängig vom Merge des Upstream-Lizenz-PRs. Für die gesamte Firmware gelten zusätzlich die Bedingungen der darin enthaltenen HeishaMon- und Fremdkomponenten.
