"""Device drivers. Each reads part of the home's state and applies part of a command.

    read()    -> dict with any of: battery_soc_pct, indoor_temp_c, ev_connected,
                 ev_session_kwh, pv_kw, grid_kw, home_kw
    apply(c)  -> carry out one quarter-hour command
                 {"battery_mode": "normal|hold|charge", "ev_charge": bool, "heat_setpoint_c": float|None}
    release() -> hand control back to the device's own normal behaviour
"""
import logging
import math
import time
from datetime import datetime, timezone

import requests

log = logging.getLogger("viertel")


class EvccDriver:
    """Car and home battery through evcc's REST API (tested against evcc 0.318 field names).

    - Charging: switches the loadpoint between "now" and the user's own default mode.
    - Battery: external battery mode must be re-sent at least every 60 s or evcc reverts.
    """
    name = "evcc"

    def __init__(self, url, loadpoint=1, password=None, control_battery=True, session=None):
        self.url = url.rstrip("/")
        self.lp = int(loadpoint)
        self.password = password
        self.control_battery = control_battery
        self.http = session or requests.Session()
        self.default_mode = None
        self._mode_set = None
        self._battery_external = False
        self._battery_controllable = False
        if password:
            self.http.post(f"{self.url}/api/auth/login", json={"password": password}, timeout=10).raise_for_status()

    def _state(self):
        r = self.http.get(f"{self.url}/api/state", timeout=10)
        r.raise_for_status()
        d = r.json()
        return d.get("result", d)              # evcc < 0.200 wrapped the state in "result"

    def read(self):
        d = self._state()
        lp = d["loadpoints"][self.lp - 1]
        if self.default_mode is None and lp.get("mode") not in (None, "now", "off"):
            self.default_mode = lp["mode"]       # how the user normally runs the charger
        bat = d.get("battery")
        soc = bat.get("soc") if isinstance(bat, dict) else d.get("batterySoc")
        if isinstance(bat, dict):
            self._battery_controllable = any(dev.get("controllable") for dev in bat.get("devices", []))
        grid = d.get("grid")
        grid_w = grid.get("power") if isinstance(grid, dict) else d.get("gridPower")
        session = lp.get("sessionEnergy")
        return {
            "battery_soc_pct": soc,
            "ev_connected": bool(lp.get("connected")),
            # evcc publishes session energy in Wh (the API docs say kWh; the live values are Wh).
            "ev_session_kwh": None if session is None else (session / 1000 if session > 200 else session),
            "pv_kw": None if d.get("pvPower") is None else d["pvPower"] / 1000,
            "grid_kw": None if grid_w is None else grid_w / 1000,
            "home_kw": None if d.get("homePower") is None else d["homePower"] / 1000,
        }

    def _post(self, path):
        r = self.http.post(f"{self.url}/api/{path}", timeout=10)
        r.raise_for_status()

    def _delete(self, path):
        r = self.http.delete(f"{self.url}/api/{path}", timeout=10)
        r.raise_for_status()

    def _set_mode(self, mode):
        try:
            self._post(f"loadpoints/{self.lp}/mode/{mode}")
        except requests.HTTPError:
            if mode != "smart":
                raise
            mode = "pv"                          # evcc before the "smart" rename
            self._post(f"loadpoints/{self.lp}/mode/{mode}")
        self._mode_set = mode
        if self.default_mode is None and mode != "now":
            self.default_mode = mode

    def apply(self, cmd):
        want = "now" if cmd.get("ev_charge") else (self.default_mode or "smart")
        if want != self._mode_set:
            self._set_mode(want)
        if self.control_battery and self._battery_controllable:
            mode = cmd.get("battery_mode", "normal")
            if mode in ("hold", "charge"):
                self._post(f"batterymode/{mode}")          # re-sent every control tick (< 60 s)
                self._battery_external = True
            elif self._battery_external:
                self._delete("batterymode")
                self._battery_external = False

    def release(self):
        if self._mode_set not in (None, self.default_mode):
            self._set_mode(self.default_mode or "smart")
        if self._battery_external:
            self._delete("batterymode")
            self._battery_external = False


class HomeAssistantDriver:
    """Heat pump thermostat and sensors through the Home Assistant REST API."""
    name = "home-assistant"

    def __init__(self, url, token, climate=None, indoor=None, battery_soc=None, session=None,
                 fallback_setpoint=21.0):
        self.url = url.rstrip("/")
        self.http = session or requests.Session()
        self.http.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        self.climate, self.indoor, self.battery_soc = climate, indoor, battery_soc
        self.original_setpoint = None
        self.fallback_setpoint = fallback_setpoint
        self._sent = None

    def _entity(self, eid):
        r = self.http.get(f"{self.url}/api/states/{eid}", timeout=10)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _float(x):
        try:
            v = float(x)
            return v if math.isfinite(v) else None
        except (TypeError, ValueError):
            return None                                   # "unavailable", "unknown"

    def read(self):
        out = {}
        if self.climate:
            c = self._entity(self.climate)
            if self.original_setpoint is None:
                self.original_setpoint = self._float(c["attributes"].get("temperature"))
            out["indoor_temp_c"] = self._float(c["attributes"].get("current_temperature"))
        if self.indoor:
            out["indoor_temp_c"] = self._float(self._entity(self.indoor)["state"])
        if self.battery_soc:
            out["battery_soc_pct"] = self._float(self._entity(self.battery_soc)["state"])
        return {k: v for k, v in out.items() if v is not None}

    def _set(self, temp):
        r = self.http.post(f"{self.url}/api/services/climate/set_temperature",
                           json={"entity_id": self.climate, "temperature": temp}, timeout=10)
        r.raise_for_status()
        self._sent = temp

    def apply(self, cmd):
        sp = cmd.get("heat_setpoint_c")
        if self.climate and sp is not None and (self._sent is None or abs(sp - self._sent) >= 0.25):
            self._set(sp)

    def release(self):
        if self.climate and self._sent is not None:
            self._set(self.original_setpoint or self.fallback_setpoint)
            self._sent = None


class SimulatedHome:
    """A pretend house for trying the connector without hardware. Physics are deliberately
    simple; it exists to show the loop working, not to be accurate."""
    name = "simulator"

    def __init__(self, speed=1.0, clock=time.time):
        self.clock, self.speed = clock, speed
        self.t = clock()
        self.soc, self.tin, self.session_kwh = 50.0, 21.0, 0.0
        self.cmd = {"battery_mode": "normal", "ev_charge": False, "heat_setpoint_c": 21.0}
        self._advance()

    def _sim_time(self):
        return datetime.fromtimestamp(self.t, tz=timezone.utc)

    def _advance(self):
        now = self.clock()
        dt_h = (now - self.t) * self.speed / 3600
        self.t = now
        h = (self._sim_time().hour + 1) % 24 + self._sim_time().minute / 60     # ~local CET
        pv = max(0.0, 6 * math.sin(math.pi * (h - 6) / 14)) if 6 < h < 20 else 0.0
        surplus = pv - 0.5
        mode = self.cmd.get("battery_mode", "normal")
        p = 5.0 if mode == "charge" else (max(min(surplus, 5), 0) if mode == "hold" else max(min(surplus, 5), -5))
        self.soc = min(max(self.soc + p * dt_h / 10 * 100, 10), 100)
        connected = h >= 18 or h < 7
        if not connected:
            self.session_kwh = 0.0
        elif self.cmd.get("ev_charge") and self.session_kwh < 8:
            self.session_kwh = min(8.0, self.session_kwh + 11 * dt_h)
        sp, t_out = self.cmd.get("heat_setpoint_c") or 21.0, 5.0
        heat = min(9.0, max(0.0, 10 * (sp - self.tin) / max(dt_h, 1e-6) + 0.15 * (self.tin - t_out)))
        self.tin += dt_h / 10 * (heat - 0.15 * (self.tin - t_out))
        self.connected = connected
        self.pv = pv

    def read(self):
        self._advance()
        return {"battery_soc_pct": round(self.soc, 1), "indoor_temp_c": round(self.tin, 2),
                "ev_connected": self.connected, "ev_session_kwh": round(self.session_kwh, 2),
                "pv_kw": round(self.pv, 2)}

    def apply(self, cmd):
        self._advance()
        self.cmd = dict(cmd)

    def release(self):
        self.apply({"battery_mode": "normal", "ev_charge": self.connected, "heat_setpoint_c": 21.0})
