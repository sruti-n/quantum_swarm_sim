# Bridging the Quantum Gap: A Robotic Modeling System for Visualizing Decoherence and Qubit Behaviors

**Author:** Sruti Nallakukkala, PRISMS Applied Physics Research Lab

## Overview

This repository contains the quantum swarm simulation, Stage 1 of a two-stage
research project investigating how abstract quantum phenomena can be made
physically legible to learners with no quantum background. The simulation
models a swarm of robots in which each robot acts as a physical analog of a
qubit: robots wander independently to represent superposition, move as
correlated pairs to represent entanglement, and drift measurably away from
their ideal orientation as decoherence is introduced. Quantum results are not
faked for visual effect — they are computed by a live Qiskit backend running
real circuits under a depolarizing noise model, so what the viewer sees on
screen reflects genuine simulated quantum behavior. The system is designed as a
pedagogical tool for quantum computing education, engaging users at the Analyze
and Evaluate levels of Bloom's Taxonomy: users select gates, adjust the noise
rate, trigger measurement, and observe the consequences of their choices rather
than passively watching an animation. Stage 2 of the project extends this work
to a physical robot prototype.

## How to Run

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open <http://localhost:8000> in a browser.

The page connects back to the server it was loaded from, so if you run uvicorn
on a different port, the WebSocket follows automatically.

### Controls

| Control | Keys |
|---|---|
| Select gate (h, x, id, sx, y, z) | `1`–`6` |
| Simulate | `S` |
| Measure (collapse wavefunction) | `Space` |
| Reset | `R` |
| Toggle Entanglement mode | `E` |
| Noise rate ± 0.05 | `↑` / `↓` |
| Add / remove a robot (4–20) | `+` / `-` |

## Project Structure

```
quantum_swarm_sim/
├── backend/
│   ├── main.py                        # FastAPI app, WebSocket handler
│   ├── quantum_engine.py              # Qiskit simulation logic (adapted from quantum_robot_v1.py)
│   ├── quantum_robot_v1.py            # Stage 1 prototype, preserved unchanged for reference
│   └── requirements.txt               # fastapi, uvicorn, qiskit, qiskit-aer, websockets
├── frontend/
│   └── index.html                     # Single self-contained file — all CSS and JS inline
├── data/
│   ├── quantum_tests_data_stage1.csv  # Stage 1 experimental data (1,432 runs)
│   └── .gitkeep                        # Keeps data/ tracked; runtime CSVs are gitignored
├── docs/
│   ├── concept-map.png
│   ├── experiment-methodology.png
│   ├── blooms-taxonomy-ksu.png
│   ├── quantum_gates_fidelity_effect.png
│   └── quantum_gates_noise_effect.png
├── legacy/                            # Archived Stage 1 prototype files
│   ├── data_analysis.py
│   ├── h_gate.py
│   ├── python_test_bridge.py
│   ├── qiskit_test_bridge.py
│   ├── superposition_test_bridge.py
│   ├── servo_test.ino
│   ├── sketch_apr20a.ino
│   └── Quantum Bits, Gates, and Circuits.ipynb
└── spec/
    └── quantum_swarm_simulation_spec.md
```

### Data

`data/quantum_tests_data_stage1.csv` is preserved experimental data from the
Stage 1 servo prototype and is tracked in Git. Simulation runs append to
`data/quantum_swarm_data.csv`, which is generated at runtime and is **not**
tracked. Its columns extend the Stage 1 format so the two datasets remain
directly comparable:

```
Timestamp, Gate Name, Noise Rate, Num Robots, Mode, Probability, Angle,
Ideal Angle, Probability Error, Angle Error, Fidelity, Knowledge Level Selected
```
