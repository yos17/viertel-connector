# Viertel connector

## Testablauf (Beta)

1. **Tag 1 bis 3: nur beobachten.** Lassen Sie `observe_only: true` (so ist es voreingestellt). Der Connector liest Ihre Geräte
   und Viertel plant, aber **nichts wird geschaltet**. Auf Ihrer Hausseite steht oben „Beobachtet“, im Protokoll
   `observe only, would set: …`. Prüfen Sie: Stimmen Speicherstand, „Auto angesteckt“ und Raumtemperatur mit der Wirklichkeit?
   Ist der Plan plausibel (Auto lädt nachts oder mittags, nicht um 18 Uhr)?
2. **Danach: steuern lassen.** `observe_only` ausschalten, Add-on neu starten. Oben steht jetzt „Autopilot“.
   Beobachten Sie in evcc, ob der Lademodus zwischen „Schnell“ und Ihrem normalen Modus wechselt.
3. **Rückmeldung.** Was hat gestimmt, was nicht? Schreiben Sie uns über <https://viertel.fly.dev/mitmachen>.

**Ausschalten geht jederzeit:** Add-on stoppen. Der Connector stellt dann sofort alles auf Ihre normalen Einstellungen zurück
(evcc-Lademodus, Batteriemodus, Thermostat).

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
| `simulate` | `true`: ein simuliertes Haus läuft (zum Ausprobieren ohne Geräte; dazu `observe_only` ausschalten). |
| `observe_only` | `true` (Voreinstellung): nur lesen und planen, nichts schalten. `false`: der Connector steuert. |

## Was Sie im Protokoll sehen

- `plan received: now=…` – der Plan für die aktuelle Viertelstunde ist angekommen.
- `observe only, would set: …` – so würde der Connector gerade schalten (im Beobachten-Modus).
- `couldn't reach Viertel` – kein Internet; der Connector folgt weiter dem letzten Plan.
- `no valid plan: handing devices back` – der Plan ist älter als drei Stunden; die Geräte sind wieder auf normal.

Fragen und Hinweise: <https://viertel.fly.dev/mitmachen>
