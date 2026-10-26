# Modellanzeige dev.7

Implementiert: 83 Einträge aus upstream-reference/HeatPumpType.md; Generator tools/update_model_table.py; getrennte Module extension/hmx_model.h und hmx_model_data.h. Quelle/Commit im generierten Katalog docs/model_catalogue.json.

Linker Kopf-Button: Modell/Geräteinfo. Rechter Kopf-Button: kurzes Antippen öffnet die Betriebsartenwahl. Gerätedetails enthalten Rohkennung, Community-Zuordnung, HeishaMon-Versionsstring/Basiscommit und HMX-Version. TOP92 über MQTT/JSON bleibt unverändert.

Die Tabelle wird separat gepflegt, ist aktuell aber in der Firmware kompiliert. Eine spätere separat aktualisierbare Laufzeit-Datei bleibt optional; sie ist noch nicht implementiert.

Der vollständige dev.7-Build und die Regressionstests waren im HMX-Actions-Lauf 40380596372 erfolgreich. Hardwaretests stehen weiterhin aus.

Hintergrund: https://github.com/heishamon/HeishaMon/issues/634#issuecomment-2605306904 und https://github.com/heishamon/HeishaMon/issues/910#issuecomment-4660654706
