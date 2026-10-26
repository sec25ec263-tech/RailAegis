# System Architecture (current: software simulation)

**All data is SIMULATED.**

## Components
- `simulation.py` - the engine. Holds the robot state machine, virtual track, obstacles, simulated sensors,
  event log and telemetry. No UI code, so it is easy to test.
- `app.py` - Streamlit dashboard. Calls the engine, draws charts, forwards button presses.
- `data/sample_inspections.json` - sample records from reproducible simulated runs.
- `tests/test_simulation.py` - automated tests of the engine.

## Robot state machine
`IDLE -> RUNNING <-> PAUSED`, `RUNNING -> HAZARD_HOLD -> RUNNING` (operator clears), `RUNNING/PAUSED/HAZARD_HOLD -> STOPPED`,
`RUNNING -> COMPLETED`. Reset returns to `IDLE`. Invalid actions raise `InvalidTransitionError`.

## Behaviour per tick (1 simulated second)
1. Detect obstacles that enter the sensor range and log them with their severity.
2. Slow to half speed near INFO/WARNING obstacles.
3. Advance; if a CRITICAL obstacle would be reached within the stop distance, halt and raise a hazard.
4. Mark passed obstacles, update telemetry, finish at the end of the track.

## Reproducibility
The demo scenario is fixed and sensor values are deterministic formulas, so every run is identical. Random mode
uses a seed: the same seed always gives the same obstacles.

## Data flow
Operator -> buttons -> engine state -> dashboard charts, metrics, event log -> optional JSON export.
