# Changelog

## 0.2.0 (2026-10-29)

- Neu: `observe_only` (voreingestellt): liest und plant, schaltet nichts. Für die ersten Tage im echten Haus.
- Behoben: evcc meldet die Ladeenergie in Wh. Kleine Werte am Anfang eines Ladevorgangs wurden als kWh gelesen
  (z. B. 150 Wh als 150 kWh), wodurch Viertel das Auto für fast voll halten konnte.
- Getestet mit evcc 0.318.1 (Demo-Modus): Lademodus und Batteriemodus schalten und zurückstellen.

## 0.1.0 (2026-10-28)

- Erste Beta: evcc (Auto, Speicher), Home Assistant (Wärmepumpe), Simulator.
