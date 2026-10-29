# Viertel connector (Home Assistant add-on)

Der Viertel-Connector führt Ihren [Viertel](https://viertel.fly.dev)-Plan zu Hause aus: Er lädt das E-Auto und den
Speicher und wärmt das Haus dann vor, wenn Strom günstig ist, und meldet Viertel alle fünf Minuten den aktuellen Stand.

**Testphase (Beta).** Der Connector ist neu: getestet mit einem simulierten Haus und mit evcc 0.318 im Demo-Modus, noch nicht in einem echten Haus.
Sie möchten ihn als Erste ausprobieren? Tragen Sie sich ein: <https://viertel.fly.dev/mitmachen>

## Installation in Home Assistant

1. Legen Sie auf <https://viertel.fly.dev/genau> Ihre Hausseite an („Meine Hausseite anlegen“).
   Dort steht Ihr persönlicher Schlüssel (`token`).
2. Home Assistant: **Einstellungen → Add-ons → Add-on-Store → ⋮ → Repositories** und diese Adresse hinzufügen:
   `https://github.com/yos17/viertel-connector`
3. **Viertel connector** installieren, unter **Konfiguration** die Zeilen von Ihrer Hausseite einfügen, starten.
4. Die ersten Tage nur beobachten (`observe_only: true`, voreingestellt): Es wird nichts geschaltet. Danach ausschalten,
   dann steuert der Connector. Details im Reiter „Dokumentation“ des Add-ons.

## Was er steuert

| Gerät | über | was passiert |
|---|---|---|
| E-Auto | [evcc](https://evcc.io) | Laden an oder aus, je Viertelstunde |
| Hausspeicher | evcc (Batteriemodus) | normal, halten oder aus dem Netz laden |
| Wärmepumpe | Home Assistant (`climate`-Entität) | Solltemperatur, nie unter Ihrer normalen |

## Sicherheit

- Ohne Internet folgt der Connector dem zuletzt erhaltenen Plan (36 Stunden).
- Ist der Plan älter als drei Stunden oder wird das Add-on gestoppt, gehen alle Geräte zurück in ihre normalen Einstellungen.
- Fällt ein Gerät aus, laufen die anderen weiter.

## Ohne Home Assistant (Docker neben evcc)

```bash
docker build -t viertel-connector viertel_connector
docker run -d --restart unless-stopped --name viertel \
  -e VIERTEL_URL=https://viertel.fly.dev -e VIERTEL_TOKEN=<Ihr Schlüssel> \
  -e EVCC_URL=http://192.168.1.20:7070 viertel-connector
```

Zum Ausprobieren ohne Geräte: `-e SIMULATE=1`. Nur beobachten, nichts schalten: `-e OBSERVE_ONLY=1`.

---

*English: Home Assistant add-on that runs your Viertel plan (dynamic electricity tariff optimizer for German homes)
on your EV charger, home battery (both via evcc) and heat pump (via a Home Assistant climate entity). Beta.*
