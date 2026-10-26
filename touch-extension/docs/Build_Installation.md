# HeishaMon V6 Touch - Build und Installation im Fork

Software 0.1.0-dev.7 / Hardware Rev.0.6. Stand 26.10.2026.

Die Build-Anleitung wird zentral in der vollständigen Anleitung gepflegt. Der frühere Ablauf mit Projekt-ZIP, neuem Repository und kopierter Workflow-Vorlage wird im Fork nicht mehr benötigt.

- [GitHub Actions: BIN herunterladen oder neu bauen](HeishaMon_V6_Touch_Anleitung.md#147-weg-c-github-actions-ohne-lokalen-esp32-compiler) - einfacher Einstieg ohne lokalen Compiler.
- [Lokale Vorbereitung und Boardeinstellungen](HeishaMon_V6_Touch_Anleitung.md#142-gemeinsame-vorbereitung-und-richtige-dateien).
- [Arduino CLI unter Windows](HeishaMon_V6_Touch_Anleitung.md#143-weg-a-windows-mit-arduino-cli---einmalige-einrichtung).
- [Arduino IDE 2](HeishaMon_V6_Touch_Anleitung.md#145-weg-b-arduino-ide-2-einrichten).
- [Installation über das HeishaMon-Webinterface](HeishaMon_V6_Touch_Anleitung.md#15-installation-und-updates-über-das-normale-webinterface).
- [Fork-Struktur und spätere Upstream-Updates](Fork_Workflow.md).

Alle lokalen Buildbefehle der vollständigen Anleitung gelten aus `touch-extension/`. Den erzeugten Sketch dort bauen; der originale Sketch im Repository-Hauptordner enthält keine Touch-Erweiterung. Der dev.7-Actions-Build ist erfolgreich, Hardwaretests stehen weiterhin aus.
