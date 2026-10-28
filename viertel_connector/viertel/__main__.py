"""Start the connector. Settings come from environment variables, or from the Home Assistant
add-on options (/data/options.json) when running as an add-on."""
import json
import logging
import os
import signal
import sys
from pathlib import Path

from .agent import Agent, CloudClient
from .drivers import EvccDriver, HomeAssistantDriver, SimulatedHome

OPTIONS = Path("/data/options.json")


def settings():
    if OPTIONS.exists():                      # running as a Home Assistant add-on
        o = json.loads(OPTIONS.read_text())
        return {
            "url": o["viertel_url"], "token": o["token"],
            "evcc_url": o.get("evcc_url"), "evcc_password": o.get("evcc_password"),
            "evcc_loadpoint": o.get("evcc_loadpoint", 1),
            "ha_url": "http://supervisor/core", "ha_token": os.environ.get("SUPERVISOR_TOKEN"),
            "climate": o.get("heat_pump_climate"), "indoor": o.get("indoor_temperature"),
            "battery_soc": o.get("battery_soc_sensor"), "simulate": o.get("simulate", False),
        }
    e = os.environ.get
    return {
        "url": e("VIERTEL_URL"), "token": e("VIERTEL_TOKEN"),
        "evcc_url": e("EVCC_URL"), "evcc_password": e("EVCC_PASSWORD"),
        "evcc_loadpoint": int(e("EVCC_LOADPOINT", "1")),
        "ha_url": e("HA_URL"), "ha_token": e("HA_TOKEN"),
        "climate": e("HEAT_PUMP_CLIMATE"), "indoor": e("INDOOR_TEMPERATURE"),
        "battery_soc": e("BATTERY_SOC_SENSOR"), "simulate": e("SIMULATE", "") in ("1", "true", "yes"),
        "sim_speed": float(e("SIM_SPEED", "1")),
    }


def build(s):
    if not s["url"] or not s["token"]:
        sys.exit("Set VIERTEL_URL and VIERTEL_TOKEN (both are on your Viertel page).")
    drivers = []
    if s["simulate"]:
        drivers.append(SimulatedHome(speed=s.get("sim_speed", 1.0)))
    if s.get("evcc_url"):
        drivers.append(EvccDriver(s["evcc_url"], s["evcc_loadpoint"], s.get("evcc_password") or None))
    if s.get("ha_url") and s.get("ha_token") and (s.get("climate") or s.get("indoor") or s.get("battery_soc")):
        drivers.append(HomeAssistantDriver(s["ha_url"], s["ha_token"], s.get("climate") or None,
                                           s.get("indoor") or None, s.get("battery_soc") or None))
    if not drivers:
        sys.exit("No devices configured. Set EVCC_URL and/or Home Assistant entities, or SIMULATE=1.")
    return Agent(CloudClient(s["url"], s["token"]), drivers)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    agent = build(settings())
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))   # run_forever's finally releases devices
    logging.getLogger("viertel").info("connector started with %s", ", ".join(d.name for d in agent.drivers))
    agent.run_forever()


if __name__ == "__main__":
    main()
