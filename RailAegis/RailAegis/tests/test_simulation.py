import json
import pytest
from simulation import (COMPLETED, HAZARD_HOLD, IDLE, PAUSED, RUNNING, STOPPED, DATA_LABEL,
                        InvalidTransitionError, Obstacle, Simulation, SimulationConfig,
                        random_obstacles, run_to_completion, save_report)


def make(obstacles=None, **kw):
    return Simulation(SimulationConfig(obstacles=obstacles, **kw))


def test_starts_idle_at_zero():
    sim = make()
    assert sim.status == IDLE and sim.position_m == 0


def test_step_does_nothing_when_not_running():
    sim = make()
    sim.step()
    assert sim.position_m == 0


def test_robot_advances_when_running():
    sim = make(obstacles=[])
    sim.start()
    sim.step()
    assert sim.position_m == pytest.approx(2.5)


def test_pause_and_resume():
    sim = make(obstacles=[])
    sim.start(); sim.step(); sim.pause()
    pos = sim.position_m
    sim.step()
    assert sim.status == PAUSED and sim.position_m == pos
    sim.start()
    assert sim.status == RUNNING


def test_invalid_transitions_raise():
    sim = make()
    with pytest.raises(InvalidTransitionError):
        sim.pause()
    with pytest.raises(InvalidTransitionError):
        sim.stop()
    with pytest.raises(InvalidTransitionError):
        sim.acknowledge_hazard()


def test_stop_ends_run():
    sim = make()
    sim.start(); sim.step(); sim.stop()
    assert sim.status == STOPPED and sim.is_finished


def test_critical_obstacle_halts_robot_before_it():
    sim = make(obstacles=[Obstacle(100, "Test object", "CRITICAL")])
    sim.start()
    sim.advance(1000)
    assert sim.status == HAZARD_HOLD
    assert sim.position_m == pytest.approx(100 - sim.config.stop_distance_m)
    assert any(e.severity == "CRITICAL" for e in sim.events)


def test_acknowledge_lets_robot_continue_to_end():
    sim = make(obstacles=[Obstacle(100, "Test object", "CRITICAL")])
    run_to_completion(sim)
    assert sim.status == COMPLETED
    assert sim.summary()["hazards_cleared"] == 1


def test_warning_obstacle_does_not_halt_but_is_logged():
    sim = make(obstacles=[Obstacle(100, "Test anomaly", "WARNING")])
    run_to_completion(sim, auto_acknowledge=False)
    assert sim.status == COMPLETED
    assert sim.summary()["obstacles_detected"] == 1


def test_reset_restores_initial_state():
    sim = make()
    run_to_completion(sim)
    sim.reset()
    assert sim.status == IDLE and sim.position_m == 0 and sim.summary()["obstacles_detected"] == 0


def test_demo_scenario_is_reproducible():
    a = run_to_completion(Simulation(SimulationConfig())).to_report()
    b = run_to_completion(Simulation(SimulationConfig())).to_report()
    assert a == b


def test_random_mode_same_seed_same_obstacles():
    assert [o.position_m for o in random_obstacles(500, 1)] == [o.position_m for o in random_obstacles(500, 1)]


def test_validation_rejects_bad_config():
    with pytest.raises(ValueError):
        make(obstacles=[Obstacle(9999, "Outside", "INFO")])
    with pytest.raises(ValueError):
        make(obstacles=[Obstacle(50, "Bad", "SEVERE")])
    with pytest.raises(ValueError):
        make(speed_mps=0)
    with pytest.raises(ValueError):
        make(detection_range_m=5, stop_distance_m=8)


def test_all_outputs_are_labelled_simulated(tmp_path):
    sim = run_to_completion(Simulation(SimulationConfig()))
    assert sim.sensors()["data_label"] == DATA_LABEL
    assert all(e.data_label == DATA_LABEL for e in sim.events)
    path = tmp_path / "r.json"
    save_report(sim, path)
    assert json.loads(path.read_text())["data_label"] == DATA_LABEL
