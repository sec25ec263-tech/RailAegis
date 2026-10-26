"""RailAegis simulation engine.

EVERYTHING IN THIS FILE IS SIMULATED. No hardware, no real railway data.
The engine is plain Python (no Streamlit) so it can be unit-tested easily.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

DATA_LABEL = "SIMULATED DATA - not real railway measurements"
SIM_START = datetime(2026, 1, 1, 8, 0, 0)  # fixed virtual clock start
SENSOR_MAX_RANGE_M = 50.0

SEVERITIES = ("INFO", "WARNING", "CRITICAL")
IDLE, RUNNING, PAUSED, HAZARD_HOLD, STOPPED, COMPLETED = (
    "IDLE", "RUNNING", "PAUSED", "HAZARD_HOLD", "STOPPED", "COMPLETED")
FINISHED_STATES = (STOPPED, COMPLETED)


class InvalidTransitionError(ValueError):
    """Raised when a control (e.g. pause) is not allowed in the current state."""


@dataclass
class Obstacle:
    position_m: float
    kind: str
    severity: str
    detected: bool = False
    resolved: bool = False


@dataclass
class Event:
    sim_time_s: float
    timestamp: str
    position_m: float
    severity: str
    message: str
    data_label: str = DATA_LABEL

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def default_obstacles() -> list[Obstacle]:
    """Fixed demo scenario: same every run, so demos are predictable."""
    return [
        Obstacle(80, "Loose gravel patch (simulated)", "INFO"),
        Obstacle(180, "Vibration anomaly zone (simulated)", "WARNING"),
        Obstacle(260, "Large object on track (simulated)", "CRITICAL"),
        Obstacle(350, "Rail-gap anomaly (simulated)", "WARNING"),
        Obstacle(440, "Fallen branch (simulated)", "CRITICAL"),
    ]


def random_obstacles(track_length_m: float, seed: int, count: int = 5,
                     stop_distance_m: float = 8.0) -> list[Obstacle]:
    """Optional random mode. Same seed -> same obstacles (reproducible)."""
    rng = random.Random(seed)
    kinds = ["Debris (simulated)", "Vibration anomaly zone (simulated)",
             "Object on track (simulated)", "Rail-gap anomaly (simulated)"]
    lo, hi, spacing = stop_distance_m + 20, track_length_m - 20, 40
    positions: list[float] = []
    for _ in range(2000):
        if len(positions) >= count:
            break
        p = round(rng.uniform(lo, hi), 1)
        if all(abs(p - q) >= spacing for q in positions):
            positions.append(p)
    return [Obstacle(p, rng.choice(kinds), rng.choice(SEVERITIES)) for p in sorted(positions)]


@dataclass
class SimulationConfig:
    track_length_m: float = 500.0
    speed_mps: float = 2.5
    tick_s: float = 1.0
    detection_range_m: float = 25.0
    stop_distance_m: float = 8.0
    mode: str = "scenario"  # "scenario" (fixed) or "random" (seeded)
    seed: int = 42
    obstacles: list[Obstacle] | None = None

    def validate(self) -> None:
        if self.track_length_m <= 0:
            raise ValueError("track_length_m must be positive")
        if self.speed_mps <= 0 or self.tick_s <= 0:
            raise ValueError("speed_mps and tick_s must be positive")
        if self.detection_range_m <= self.stop_distance_m or self.stop_distance_m <= 0:
            raise ValueError("detection_range_m must be larger than stop_distance_m (> 0)")
        if self.mode not in ("scenario", "random"):
            raise ValueError("mode must be 'scenario' or 'random'")
        seen = set()
        for o in self.obstacles or []:
            if o.severity not in SEVERITIES:
                raise ValueError(f"unknown severity: {o.severity}")
            if not 0 < o.position_m <= self.track_length_m:
                raise ValueError(f"obstacle at {o.position_m} m is outside the track")
            if o.severity == "CRITICAL" and o.position_m < self.stop_distance_m:
                raise ValueError("critical obstacle is too close to the start")
            if o.position_m in seen:
                raise ValueError("two obstacles share the same position")
            seen.add(o.position_m)


class Simulation:
    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()
        if self.config.obstacles is None:
            self.config.obstacles = (
                random_obstacles(self.config.track_length_m, self.config.seed,
                                 stop_distance_m=self.config.stop_distance_m)
                if self.config.mode == "random" else default_obstacles())
        self.config.validate()
        self._template = [Obstacle(o.position_m, o.kind, o.severity) for o in self.config.obstacles]
        self.reset()

    # ---------- state ----------
    def reset(self) -> None:
        self.obstacles = [Obstacle(o.position_m, o.kind, o.severity) for o in self._template]
        self.position_m = 0.0
        self.elapsed_s = 0.0
        self.status = IDLE
        self.events: list[Event] = []
        self.telemetry: list[dict] = []
        self.slowing = False
        self._log("INFO", "Simulation reset. Ready (SIMULATED).")
        self._record_telemetry()

    def _clock(self) -> str:
        return (SIM_START + timedelta(seconds=self.elapsed_s)).strftime("%Y-%m-%d %H:%M:%S")

    def _log(self, severity: str, message: str) -> None:
        self.events.append(Event(round(self.elapsed_s, 1), self._clock(),
                                 round(self.position_m, 1), severity, message))

    # ---------- controls ----------
    def start(self) -> None:
        if self.status not in (IDLE, PAUSED):
            raise InvalidTransitionError(f"cannot start/resume from {self.status}")
        self._log("INFO", "Inspection started." if self.status == IDLE else "Inspection resumed.")
        self.status = RUNNING

    def pause(self) -> None:
        if self.status != RUNNING:
            raise InvalidTransitionError(f"cannot pause from {self.status}")
        self.status = PAUSED
        self._log("INFO", "Inspection paused by operator.")

    def stop(self) -> None:
        if self.status not in (RUNNING, PAUSED, HAZARD_HOLD):
            raise InvalidTransitionError(f"cannot stop from {self.status}")
        self.status = STOPPED
        self._log("WARNING", "Inspection stopped by operator before completion.")

    def acknowledge_hazard(self) -> None:
        """Operator marks the simulated hazard as cleared; robot may continue."""
        if self.status != HAZARD_HOLD:
            raise InvalidTransitionError("no hazard to acknowledge")
        blocker = self._blocking_obstacle()
        if blocker:
            blocker.resolved = True
        self._log("INFO", "Operator cleared simulated hazard. Resuming.")
        self.status = RUNNING

    # ---------- sensors ----------
    def _unresolved_ahead(self) -> list[Obstacle]:
        return sorted((o for o in self.obstacles if not o.resolved and o.position_m >= self.position_m),
                      key=lambda o: o.position_m)

    def _blocking_obstacle(self) -> Obstacle | None:
        return next((o for o in self._unresolved_ahead() if o.severity == "CRITICAL"), None)

    def sensors(self) -> dict:
        """Deterministic example readings. All values are SIMULATED."""
        ahead = self._unresolved_ahead()
        dist = min(SENSOR_MAX_RANGE_M, ahead[0].position_m - self.position_m) if ahead else SENSOR_MAX_RANGE_M
        near = any(abs(o.position_m - self.position_m) <= 5 for o in self.obstacles)
        return {
            "distance_ahead_m": round(dist, 1),
            "vibration_g": round(0.20 + 0.04 * math.sin(self.position_m / 9) + (0.30 if near else 0), 3),
            "temperature_c": round(28 + 2 * math.sin(self.elapsed_s / 60), 1),
            "battery_pct": round(max(0.0, 100 - self.elapsed_s * 0.02), 1),
            "data_label": DATA_LABEL,
        }

    def _record_telemetry(self) -> None:
        s = self.sensors()
        self.telemetry.append({"position_m": round(self.position_m, 1), "elapsed_s": round(self.elapsed_s, 1),
                               "vibration_g": s["vibration_g"], "distance_ahead_m": s["distance_ahead_m"]})

    # ---------- simulation step ----------
    def step(self) -> None:
        """Advance one tick. Does nothing unless RUNNING."""
        if self.status != RUNNING:
            return
        cfg = self.config
        self.elapsed_s += cfg.tick_s

        for o in self._unresolved_ahead():  # detect obstacles entering sensor range
            if not o.detected and o.position_m - self.position_m <= cfg.detection_range_m:
                o.detected = True
                self._log(o.severity, f"{o.severity} obstacle detected: {o.kind} at {o.position_m:.0f} m (SIMULATED)")

        speed = cfg.speed_mps
        self.slowing = any(o.detected and not o.resolved and o.severity != "CRITICAL"
                           and 0 <= o.position_m - self.position_m <= cfg.detection_range_m
                           for o in self.obstacles)
        if self.slowing:
            speed *= 0.5

        new_pos = self.position_m + speed * cfg.tick_s
        blocker = self._blocking_obstacle()
        if blocker and new_pos >= blocker.position_m - cfg.stop_distance_m:
            self.position_m = max(self.position_m, blocker.position_m - cfg.stop_distance_m)
            self.status = HAZARD_HOLD
            self._log("CRITICAL", f"HAZARD: robot halted {cfg.stop_distance_m:.0f} m before "
                                  f"{blocker.kind}. Operator action needed (SIMULATED).")
            self._record_telemetry()
            return

        self.position_m = min(new_pos, cfg.track_length_m)
        for o in self.obstacles:
            if not o.resolved and o.severity != "CRITICAL" and o.position_m < self.position_m:
                o.resolved = True
                self._log("INFO", f"Passed {o.kind} at {o.position_m:.0f} m.")
        if self.position_m >= cfg.track_length_m:
            self.status = COMPLETED
            self._log("INFO", "Inspection of virtual track complete (SIMULATED).")
        self._record_telemetry()

    def advance(self, ticks: int) -> None:
        for _ in range(max(0, ticks)):
            if self.status != RUNNING:
                break
            self.step()

    # ---------- reporting ----------
    @property
    def is_finished(self) -> bool:
        return self.status in FINISHED_STATES

    def summary(self) -> dict:
        det = [o for o in self.obstacles if o.detected]
        return {
            "status": self.status,
            "inspected_m": round(self.position_m, 1),
            "track_length_m": self.config.track_length_m,
            "progress_pct": round(100 * self.position_m / self.config.track_length_m, 1),
            "obstacles_detected": len(det),
            "critical_detected": sum(o.severity == "CRITICAL" for o in det),
            "hazards_cleared": sum(o.severity == "CRITICAL" and o.resolved for o in self.obstacles),
            "elapsed_s": round(self.elapsed_s, 1),
            "event_count": len(self.events),
            "mode": self.config.mode,
            "seed": self.config.seed if self.config.mode == "random" else None,
            "data_label": DATA_LABEL,
        }

    def to_report(self) -> dict:
        return {"data_label": DATA_LABEL, "summary": self.summary(),
                "events": [e.to_dict() for e in self.events]}


def run_to_completion(sim: Simulation, auto_acknowledge: bool = True, max_ticks: int = 100_000) -> Simulation:
    """Run a whole simulated inspection without the UI (used by tests and sample data)."""
    if sim.status == IDLE:
        sim.start()
    for _ in range(max_ticks):
        if sim.status == HAZARD_HOLD and auto_acknowledge:
            sim.acknowledge_hazard()
        if sim.status != RUNNING:
            break
        sim.step()
    return sim


def save_report(sim: Simulation, path: str | Path) -> None:
    Path(path).write_text(json.dumps(sim.to_report(), indent=2), encoding="utf-8")
