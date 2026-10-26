## Anhang A. Vollständige Verbindungsliste

Jeder Eintrag bezeichnet **Bauteilreferenz.Kontaktnummer** des neuen Adapters. Alle Punkte einer Zeile sind elektrisch verbunden. Die Netzliste wurde unabhängig für die Platinenbauteile mit dem KiCad-Export abgeglichen. J6/J7 zeigen die externen Gegenkontakte des W5500-Moduls; diese erhalten keinen zusätzlichen PCB-Footprint.

| Netz | Sämtliche Anschlusspunkte |
| --- | --- |
| +3V3_EXT | C1.1, C2.1, C3.1, J4.1, R0.2, R1.1, R10.1, R2.1, R3.1, R5.1, R6.1, R7.1, TP2.1, U1.18 |
| +3V3_V6 | J2.2, J2.3, J3.6, J7.2, J7.3, R0.1, TP1.1 |
| +5V_V6 | J3.7, TP3.1 |
| ETH_CS | J1.5, J6.5 |
| ETH_IRQ | J1.6, J6.6 |
| ETH_RST | J2.5, J7.5 |
| GND | C1.2, C2.2, C3.2, J1.1, J1.2, J2.1, J3.8, J4.3, J6.1, J6.2, J7.1, R11.2, TP4.1, U1.3, U1.4, U1.5, U1.9 |
| I2C_SCL | J3.5, J4.13, R2.2, U1.1 |
| I2C_SDA | J3.4, J4.12, R1.2, U1.2 |
| LCD_BL | J3.3, J4.11, R11.1 |
| LCD_CS | J3.1, J4.8, R5.2 |
| LCD_DC | J3.2, J4.9 |
| LCD_MOSI | J4.5, R8.2 |
| LCD_RST | J4.10, R6.2, U1.12 |
| LCD_SCK | J4.6, R9.2 |
| MCP_RST | R3.2, U1.6 |
| SD_CS | J4.7, R10.2 |
| SPI_MISO | J2.6, J7.6 |
| SPI_MOSI | J1.3, J6.3, R8.1 |
| SPI_SCK | J1.4, J6.4, R9.1 |
| TP_RST | J4.15, R7.2, U1.11 |

Bewusst unbeschaltet: J2.4, J4.2, J4.4, J4.14, U1.7, U1.8, U1.10, U1.13, U1.14, U1.15, U1.16, U1.17, J7.4. J6/J7 liegen extern am Ethernetmodul.

**Prüfstand:** ERC 0 Verstöße; Geroutete Platine 0 DRC-Verstöße; 0 offene Verbindungen. Mechanische Passung und Hardwaretest stehen aus; keine Fertigungsfreigabe.
