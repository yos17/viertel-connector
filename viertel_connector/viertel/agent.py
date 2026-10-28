"""The connector loop: report state, receive the plan, carry out the current quarter-hour.

Safety rule: the plan carries 36 h of commands, so a short outage is harmless. If Viertel
can't be reached for STALE_AFTER, every driver is released back to its normal behaviour.
"""
import logging
import time
from datetime import datetime, timedelta, timezone

import requests

log = logging.getLogger("viertel")
SLOT = timedelta(minutes=15)


class CloudClient:
    def __init__(self, url, token, session=None):
        self.url = url.rstrip("/")
        self.http = session or requests.Session()
        self.headers = {"Authorization": f"Bearer {token}"}

    def post_state(self, state: dict) -> dict:
        r = self.http.post(f"{self.url}/api/v1/state", json=state, headers=self.headers, timeout=30)
        if r.status_code == 401:
            raise PermissionError("Viertel rejected the token. Copy it again from your Viertel page.")
        r.raise_for_status()
        return r.json()


def _ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class Agent:
    def __init__(self, cloud, drivers, report_every_s=300, control_every_s=30,
                 stale_after=timedelta(hours=3), now=lambda: datetime.now(timezone.utc)):
        self.cloud, self.drivers = cloud, drivers
        self.report_every_s, self.control_every_s = report_every_s, control_every_s
        self.stale_after, self.now = stale_after, now
        self.schedule, self.last_ok, self.last_report = [], None, None
        self.released = True

    def report(self):
        state = {"connector": " + ".join(d.name for d in self.drivers)}
        for d in self.drivers:
            try:
                state.update({k: v for k, v in d.read().items() if v is not None})
            except Exception as e:                          # noqa: BLE001 — one device down ≠ all down
                log.warning("reading %s failed: %s", d.name, e)
        self.last_report = self.now()
        plan = self.cloud.post_state(state)
        self.schedule = plan["schedule"]
        self.last_ok = self.now()
        log.info("plan received: now=%s", plan["now"])
        return plan

    def current_command(self):
        now = self.now()
        if self.last_ok is None or now - self.last_ok > self.stale_after:
            return None
        for slot in self.schedule:
            t = _ts(slot["t"])
            if t <= now < t + SLOT:
                return slot
        return None

    def control(self):
        cmd = self.current_command()
        if cmd is None:
            if not self.released:
                log.warning("no valid plan: handing devices back to their normal settings")
                for d in self.drivers:
                    try:
                        d.release()
                    except Exception as e:                  # noqa: BLE001
                        log.warning("releasing %s failed: %s", d.name, e)
                self.released = True
            return None
        for d in self.drivers:
            try:
                d.apply(cmd)
            except Exception as e:                          # noqa: BLE001
                log.warning("%s didn't accept the command: %s", d.name, e)
        self.released = False
        return cmd

    def step(self):
        due = self.last_report is None or (self.now() - self.last_report).total_seconds() >= self.report_every_s
        if due:
            try:
                self.report()
            except PermissionError:
                raise
            except Exception as e:                          # noqa: BLE001 — keep following the old plan
                log.warning("couldn't reach Viertel: %s", e)
        return self.control()

    def run_forever(self):
        try:
            while True:
                self.step()
                time.sleep(self.control_every_s)
        finally:
            for d in self.drivers:
                try:
                    d.release()
                except Exception:                           # noqa: BLE001
                    pass
