# Viertel connector

## Konfiguration

Kopieren Sie die Zeilen von Ihrer Viertel-Hausseite (`https://viertel.fly.dev/h/…`, Abschnitt „Autopilot“).

| Option | Bedeutung |
|---|---|
| `viertel_url` | `https://viertel.fly.dev` |
| `token` | Ihr persönlicher Schlüssel von der Hausseite. Nicht weitergeben. |
| `evcc_url` | Adresse Ihrer evcc-Installation, z. B. `http://192.168.1.20:7070`. Leer lassen ohne evcc. |
| `evcc_password` | Nur nötig, wenn evcc ein Passwort hat. |
| `evcc_loadpoint` | Nummer des Ladepunkts in evcc (meist 1). |
| `heat_pump_climate` | Die `climate`-Entität Ihrer Wärmepumpe, z. B. `climate.waermepumpe`. Leer lassen ohne Wärmepumpe. |
| `indoor_temperature` | Sensor der Raumtemperatur, z. B. `sensor.wohnzimmer_temperatur`. |
| `battery_soc_sensor` | Optional: Sensor für den Ladestand des Speichers, falls evcc ihn nicht kennt. |
| `simulate` | `true`: kein echtes Gerät wird gesteuert, ein simuliertes Haus läuft (zum Ausprobieren). |

## Was Sie im Protokoll sehen

- `plan received: now=…` – der Plan für die aktuelle Viertelstunde ist angekommen.
- `couldn't reach Viertel` – kein Internet; der Connector folgt weiter dem letzten Plan.
- `no valid plan: handing devices back` – der Plan ist älter als drei Stunden; die Geräte sind wieder auf normal.

Fragen und Hinweise: <https://viertel.fly.dev/mitmachen>
