# RailAegis - Autonomous Railway Track Inspection Robot (Software Simulation)

> **Status: software simulation only.** No robot or hardware prototype has been built. No field testing has
> taken place. All readings, obstacles and events are **SIMULATED DATA**. This project is **not** a validated
> railway safety system and must never be used to judge whether a real track is safe.

## 1. Overview and objectives
RailAegis is a *proposed* robot that would help railway inspection teams monitor track conditions. This repository
contains a web dashboard that **simulates** such an inspection so the concept, the operator workflow and the
software logic can be demonstrated and explained.

Objectives of this repository:
- Demonstrate the inspection workflow (start, pause, hazard warning, operator action, stop, reset).
- Show how sensor readings, obstacle detection and an event log could be presented to an operator.
- Provide a clean, tested software base that future hardware work could build on.

## 2. Problem statement
Manual track inspection is slow, repetitive and exposes staff to risk. An automated inspection aid could
support inspectors by covering long distances consistently and flagging items for human review.

## 3. Proposed solution
A small robot that travels along a track, reads sensors, flags possible obstacles or abnormalities, and reports
to an operator dashboard. **This repository implements only the dashboard and a simulated robot.**

## 4. Key features
- Live simulated robot status and movement along a virtual 500 m track
- Start / Resume, Pause, Stop, Clear hazard and Reset controls
- Track visualisation with inspected section, sensor range, obstacles and robot position
- Simulated sensors: distance ahead, vibration, temperature, battery
- Severity levels (INFO / WARNING / CRITICAL), timestamped event log, inspection history
- Clear on-screen hazard warning; robot halts before CRITICAL obstacles until the operator clears them
- JSON export, responsive layout (laptop and phone browsers), 14 automated tests

## 5. System architecture
```
 app.py (Streamlit UI)  --->  simulation.py (pure Python engine)  --->  data/*.json (sample records)
 buttons, charts, log          robot, sensors, obstacles, events        exported / sample runs
```
Details: [docs/system_architecture.md](docs/system_architecture.md), scope: [docs/project_scope.md](docs/project_scope.md),
future hardware ideas (untested): [docs/future_hardware_integration.md](docs/future_hardware_integration.md).

## 6. Technology stack
Python 3.10+, Streamlit 1.66.1 (UI), Plotly 7.1.0 (charts), JSON (data), pytest (tests). All free and open source; no paid APIs,
cloud services or databases.

## 7. Windows setup (complete beginner)
1. Install Python 3.10 or newer from https://www.python.org/downloads/ . On the first installer screen,
   **tick "Add python.exe to PATH"**, then click Install.
2. Download this repository (green **Code** button on GitHub > **Download ZIP**) and unzip it, or use `git clone`.
3. Open the folder in File Explorer, click the address bar, type `cmd`, press Enter. A black window opens in that folder.
4. Create a virtual environment (a private box for this project's libraries):
```
python -m venv venv
```
5. Activate it (you should see `(venv)` at the start of the line):
```
venv\Scripts\activate
```
   If PowerShell blocks this, use the `cmd` window instead, or run `Set-ExecutionPolicy -Scope Process Bypass`.
6. Install dependencies:
```
python -m pip install -r requirements.txt
```
7. Launch the app:
```
streamlit run app.py
```
   Your browser opens at http://localhost:8501 . If Streamlit asks for an email, just press Enter. Stop the app with `Ctrl+C`.

Next time: open `cmd` in the folder, run `venv\Scripts\activate`, then `streamlit run app.py`.

## 8. Using the dashboard
| Control | What it does |
|---|---|
| **Start / Resume** | Starts the simulated inspection, or continues after a pause |
| **Pause** | Freezes the robot in place |
| **Stop** | Ends the run early; it is saved to Inspection history |
| **Clear hazard** | Enabled only after a CRITICAL halt; simulates a human clearing the obstacle so the robot continues |
| **Reset** | Returns to the start of the same scenario |
| Sidebar: **Scenario** | *Demo* = fixed obstacles at 80, 180, 260, 350, 440 m (same every time). *Random* = obstacles from a seed (same seed = same layout) |
| Sidebar: **speed / range / playback** | Robot speed, sensor range, and how fast the simulation plays on screen |
| **Apply settings & reset** | Applies sidebar changes (they never change a run in progress) |
| **Export tab** | Downloads the current run as JSON, labelled SIMULATED |

Suggested demo for judges: press Start, watch the INFO and WARNING obstacles slow the robot, wait for the red
CRITICAL hazard at 260 m, press **Clear hazard**, then show the Event log and Inspection history.

## 9. Running the tests
With the virtual environment active:
```
python -m pytest
```
The tests cover movement, pause/resume/stop, invalid actions, hazard halting, reproducibility, input validation and
the SIMULATED labelling. To regenerate the sample file: `python generate_sample_data.py`.

## 10. Limitations
- Software simulation only: no hardware, no real sensors, no real track data, no machine-vision or defect detection.
- Sensor values come from simple formulas; obstacle detection is geometric (distance), not perception.
- Not validated. It **cannot** certify track safety or replace any railway inspection.
- Real deployment would require proper engineering, extensive validation, railway-authority approval and compliance
  with relevant safety standards. Any future hardware testing must use a safe, isolated test setup, **never an
  operational railway track**.

## 11. Possible future improvements
Configurable scenarios from a file, map/GPS-style view, simulated camera frames, a data-logging back end,
and (separately, and only after proper planning) a bench-top prototype - see the future hardware document.

## 12. Publishing to GitHub
1. Create a free account at https://github.com and click **New repository**. Name it `RailAegis`, keep it Public,
   do **not** tick "Add a README" (you already have one), and click **Create repository**.
2. Install Git for Windows (https://git-scm.com/download/win), then in your project folder run:
```
git init
git add .
git commit -m "Initial commit: RailAegis software simulation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/RailAegis.git
git push -u origin main
```
3. Refresh the GitHub page. Your repository URL is `https://github.com/YOUR-USERNAME/RailAegis`.
   (No Git? On the repository page use **Add file > Upload files** and drag in the project files, keeping the folders.)

## License
MIT - see [LICENSE](LICENSE).
