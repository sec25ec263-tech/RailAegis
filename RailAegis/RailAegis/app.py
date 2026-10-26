"""RailAegis - SIMULATED railway inspection dashboard (Streamlit).

Run with:  streamlit run app.py
Everything shown is SIMULATED DATA. This is not a railway safety system.
"""
import json
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from simulation import (DATA_LABEL, HAZARD_HOLD, IDLE, PAUSED, RUNNING, Simulation,
                        SimulationConfig)

SAMPLE_FILE = Path(__file__).parent / "data" / "sample_inspections.json"
SEV_COLOR = {"INFO": "#3b82f6", "WARNING": "#f59e0b", "CRITICAL": "#dc2626"}

st.set_page_config(page_title="RailAegis Simulation", page_icon="🚆", layout="wide")
st.markdown("<style>.block-container{padding-top:1.5rem}</style>", unsafe_allow_html=True)

# ---------------- session state ----------------
if "sim" not in st.session_state:
    st.session_state.sim = Simulation(SimulationConfig())
    st.session_state.history = []
    st.session_state.recorded = False
sim: Simulation = st.session_state.sim

# ---------------- sidebar: settings ----------------
with st.sidebar:
    st.header("Scenario settings")
    st.caption("Applied only when you press the button below.")
    mode_label = st.radio("Scenario", ["Demo scenario (fixed, reproducible)", "Random scenario (seeded)"])
    random_mode = mode_label.startswith("Random")
    seed = st.number_input("Random seed", 0, 99999, 42, disabled=not random_mode)
    length = st.number_input("Track length (m) - random mode only", 200, 5000, 500, 50, disabled=not random_mode)
    speed = st.slider("Simulated robot speed (m/s)", 0.5, 5.0, 2.5, 0.5)
    det = st.slider("Sensor detection range (m)", 15, 50, 25)
    playback = st.slider("Playback speed (ticks per screen update)", 1, 20, 5)
    if st.button("Apply settings & reset", width="stretch"):
        try:
            cfg = SimulationConfig(track_length_m=float(length) if random_mode else 500.0,
                                   speed_mps=float(speed), detection_range_m=float(det),
                                   mode="random" if random_mode else "scenario", seed=int(seed))
            st.session_state.sim = Simulation(cfg)
            st.session_state.recorded = False
            st.rerun()
        except ValueError as err:
            st.error(f"Invalid settings: {err}")
    st.info(DATA_LABEL)

# ---------------- header ----------------
st.title("🚆 RailAegis - Inspection Simulation Dashboard")
st.warning("**SIMULATED DATA.** Software simulation only - no robot has been built or tested, "
           "and this is not a validated railway safety system.")

# advance the simulation BEFORE drawing controls, so button states match the new status
if sim.status == RUNNING:
    sim.advance(playback)

# ---------------- controls ----------------
c1, c2, c3, c4, c5 = st.columns(5)
action = None
if c1.button("▶ Start / Resume", disabled=sim.status not in (IDLE, PAUSED), width="stretch"):
    action = sim.start
if c2.button("⏸ Pause", disabled=sim.status != RUNNING, width="stretch"):
    action = sim.pause
if c3.button("⏹ Stop", disabled=sim.status not in (RUNNING, PAUSED, HAZARD_HOLD), width="stretch"):
    action = sim.stop
if c4.button("✅ Clear hazard", disabled=sim.status != HAZARD_HOLD, width="stretch"):
    action = sim.acknowledge_hazard
if c5.button("🔄 Reset", width="stretch"):
    action = sim.reset
    st.session_state.recorded = False
if action:
    action()
    st.rerun()

# store finished runs in the session history (once)
if sim.is_finished and not st.session_state.recorded:
    st.session_state.history.append(sim.summary())
    st.session_state.recorded = True

# ---------------- status & warnings ----------------
s = sim.summary()
if sim.status == HAZARD_HOLD:
    st.error("🚨 **SIMULATED HAZARD DETECTED** - robot halted. Press 'Clear hazard' to continue the simulation.")
elif sim.status == RUNNING and sim.slowing:
    st.warning("⚠️ Simulated obstacle ahead - robot slowing down.")
elif sim.status == "COMPLETED":
    st.success("Simulated inspection complete.")

m = st.columns(5)
m[0].metric("Status", s["status"])
m[1].metric("Inspected distance", f'{s["inspected_m"]} / {s["track_length_m"]:.0f} m')
m[2].metric("Obstacles detected", s["obstacles_detected"])
m[3].metric("Critical hazards", s["critical_detected"])
m[4].metric("Sim. elapsed", f'{s["elapsed_s"]:.0f} s')
st.progress(min(1.0, s["progress_pct"] / 100), text=f'Inspection progress: {s["progress_pct"]}%  (SIMULATED)')

# ---------------- track visualisation ----------------
L = sim.config.track_length_m
fig = go.Figure()
fig.add_shape(type="rect", x0=0, x1=L, y0=-0.35, y1=0.35, fillcolor="#e5e7eb", line_width=0, layer="below")
fig.add_shape(type="rect", x0=0, x1=sim.position_m, y0=-0.35, y1=0.35, fillcolor="#bbf7d0", line_width=0, layer="below")
fig.add_shape(type="rect", x0=sim.position_m, x1=min(L, sim.position_m + sim.config.detection_range_m),
              y0=-0.35, y1=0.35, line=dict(color="#6366f1", dash="dot"), fillcolor="rgba(99,102,241,0.08)")
for y in (-0.15, 0.15):
    fig.add_shape(type="line", x0=0, x1=L, y0=y, y1=y, line=dict(color="#374151", width=3))
for sev, col in SEV_COLOR.items():
    obs = [o for o in sim.obstacles if o.severity == sev]
    fig.add_trace(go.Scatter(
        x=[o.position_m for o in obs], y=[0] * len(obs), mode="markers", name=sev,
        marker=dict(size=14, color=[("#9ca3af" if o.resolved else col) for o in obs],
                    symbol="x", line=dict(width=2)),
        text=[f"{o.kind}<br>{o.position_m:.0f} m" for o in obs], hoverinfo="text"))
fig.add_trace(go.Scatter(x=[sim.position_m], y=[0], mode="markers+text", name="Robot (simulated)",
                         marker=dict(size=22, symbol="diamond", color="#2563eb"),
                         text=["🤖"], textposition="top center", hoverinfo="skip"))
fig.update_yaxes(visible=False, range=[-1, 1])
fig.update_xaxes(title="Distance along virtual track (m) - SIMULATED DATA", range=[0, L])
fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.25))
st.plotly_chart(fig, width="stretch")

# ---------------- sensors ----------------
st.subheader("Simulated sensor readings")
sn = sim.sensors()
k = st.columns(4)
k[0].metric("Distance ahead", f'{sn["distance_ahead_m"]} m')
k[1].metric("Vibration", f'{sn["vibration_g"]} g')
k[2].metric("Temperature", f'{sn["temperature_c"]} °C')
k[3].metric("Battery", f'{sn["battery_pct"]} %')
st.caption("Example values from a mathematical model, not from real sensors.")

tel = sim.telemetry[-600:]
vf = go.Figure(go.Scatter(x=[t["position_m"] for t in tel], y=[t["vibration_g"] for t in tel],
                          mode="lines", line=dict(color="#7c3aed")))
vf.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=10), title="Simulated vibration vs position",
                 xaxis_title="Position (m)", yaxis_title="g (simulated)")
st.plotly_chart(vf, width="stretch")

# ---------------- logs & history ----------------
tab1, tab2, tab3 = st.tabs(["Event log", "Inspection history", "Export"])
with tab1:
    rows = [{"Time (simulated)": e.timestamp, "Position (m)": e.position_m,
             "Severity": e.severity, "Event": e.message} for e in reversed(sim.events)]
    st.dataframe(rows, width="stretch", hide_index=True)
with tab2:
    st.markdown("**Runs finished in this session (SIMULATED):**")
    if st.session_state.history:
        st.dataframe(st.session_state.history, width="stretch", hide_index=True)
    else:
        st.caption("No finished runs yet. Complete or stop a run to add it here.")
    st.markdown("**Sample records from `data/sample_inspections.json` (SIMULATED):**")
    try:
        sample = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
        st.dataframe([r["summary"] for r in sample["inspections"]], width="stretch", hide_index=True)
    except (OSError, ValueError, KeyError):
        st.caption("Sample file not found or unreadable.")
with tab3:
    st.download_button("Download current run as JSON (SIMULATED)",
                       json.dumps(sim.to_report(), indent=2), "railaegis_simulated_run.json",
                       "application/json")

# keep the simulation ticking while it is running
if sim.status == RUNNING:
    time.sleep(0.4)
    st.rerun()
