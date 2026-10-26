"""Regenerates data/sample_inspections.json from reproducible SIMULATED runs."""
import json
from pathlib import Path
from simulation import DATA_LABEL, Simulation, SimulationConfig, run_to_completion

runs = []
for cfg in (SimulationConfig(), SimulationConfig(mode="random", seed=7, track_length_m=400)):
    sim = run_to_completion(Simulation(cfg))
    report = sim.to_report()
    runs.append({"summary": report["summary"], "events": report["events"]})

out = Path(__file__).parent / "data" / "sample_inspections.json"
out.write_text(json.dumps({"data_label": DATA_LABEL, "inspections": runs}, indent=2), encoding="utf-8")
print("Wrote", out)
