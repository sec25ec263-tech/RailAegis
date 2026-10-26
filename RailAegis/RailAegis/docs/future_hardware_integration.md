# Future Hardware Integration (ideas only - NOTHING here has been built or tested)

This document is a *possible* path, not a description of existing work.

## Possible building blocks to research
- **Microcontroller:** e.g. an Arduino-class or ESP32-class board to read sensors and drive motors.
- **Obstacle sensing:** ultrasonic or time-of-flight distance sensors (matches the simulated "distance ahead").
- **Vibration / motion:** an inertial measurement unit (IMU) for vibration (matches the simulated "vibration").
- **Environment and power:** temperature sensor, battery voltage monitoring.
- **Drive:** DC or stepper motors with a suitable motor driver, wheel encoders for distance.
- **Link to dashboard:** serial/USB or Wi-Fi sending readings that the dashboard replaces the simulator with.

## Suggested staged approach
1. Keep the simulator as the reference behaviour.
2. Bench test individual sensors on a desk and compare real readings with expectations.
3. Build a small wheeled prototype and test it indoors on a **safe, isolated test track** (for example a model track
   or a marked floor line), with an emergency stop.
4. Only with proper supervision and approvals consider anything further.

## Hard rules
- Do not test on operational railway tracks. Do not enter railway property without authorisation.
- Do not claim accuracy or defect-detection ability without documented validation.
- Real deployment needs engineering review, extensive validation, railway-authority approval and compliance with
  relevant safety standards.
