# Bridging the Quantum Gap: A Robotic Modeling System for Visualizing Decoherence and Qubit Behaviors

**Author:** Sruti Nallakukkala, Princeton International School of Mathematics and Science: Applied Physics Research Lab

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

## About This Project

Quantum computing is one of the fastest-growing fields in science and
engineering, but it remains inaccessible to most people because of the advanced
prerequisites needed to understand it. This simulation was built to change that.

Bridging the Quantum Gap is an interactive web simulation that uses a swarm of
robots to model the behavior of quantum bits (qubits). Each robot represents a
qubit, and the way the robots move, synchronize, and respond to your input
reflects real quantum phenomena — superposition, entanglement, and decoherence —
simulated through IBM's Qiskit framework in real time.

You do not need a background in physics or computer science to use it. Select a
gate, watch the robots enter superposition, and press Space to collapse the
wavefunction. The explanation panel adjusts to your level of knowledge, from
complete beginner to advanced.

This project is Stage 1 of a two-stage research project conducted at the
Applied Physics Research Laboratory at Princeton International School of
Mathematics and Science (PRISMS). Stage 2 will translate this simulation into a
physical robot swarm, adding a tactile dimension to the learning experience.

## Research Background

This simulation is grounded in published research across two areas: quantum
computing and educational technology.

On the quantum side, Hung et al. (2019) established that quantum programs are
almost certain to contain errors, and that no principled method yet exists to
reason about erroneous quantum behavior — motivating the need for accessible
tools that make these errors visible and understandable. Nachman et al. (2020)
identified readout noise as a significant source of quantum error and explored
unfolding methods to correct it. Steane (1996) laid foundational groundwork for
quantum error correction by adapting classical error correction codes to
quantum systems. Abdisatarov et al. (2025) demonstrated that magnetic field
engineering can reduce temporal noise in transmon qubits, showing that
decoherence is an active and solvable problem.

On the educational side, Mannone, Seidita, and Chella (2023) demonstrated that
quantum computing can be directly applied to model swarm robot interactions
through quantum circuits, establishing a precedent for the approach this
simulation takes. Hany, Akl, Ramadan, and Atia (2023) conducted a controlled
experiment showing that tangible user interfaces outperformed traditional
textbook instruction by 25.4% in learning gains and produced significantly
better retention two weeks later (1.5% loss versus 7.2% loss for the textbook
group) — providing empirical support for why interactive, physical interaction
with abstract concepts produces deeper understanding than passive instruction.

### Full citations

- Abdisatarov, B., et al. (2025). Demonstrating magnetic field robustness and
  reducing temporal T1 noise in transmon qubits through magnetic field
  engineering. *arXiv*. <https://doi.org/10.48550/arXiv.2506.02187>
- Hany, A., Akl, A., Ramadan, E., & Atia, A. (2023). The effect of using
  tangible user interfaces compared to traditional learning for teaching
  programming in higher education: An experimental study. *2023 Intelligent
  Methods, Systems, and Applications (IMSA)*.
  <https://doi.org/10.1109/IMSA58542.2023.10217780>
- Hung, S.-H., et al. (2019). Quantitative robustness analysis of quantum
  programs. *Proceedings of the ACM on Programming Languages, 3*(POPL), Article
  31. <https://doi.org/10.1145/3290344>
- Mannone, M., Seidita, V., & Chella, A. (2023). Modeling and designing a
  robotic swarm: A quantum computing approach. *Swarm and Evolutionary
  Computation, 79*, 101297. <https://doi.org/10.1016/j.swevo.2023.101297>
- Nachman, B., et al. (2020). Unfolding quantum computer readout noise. *npj
  Quantum Information, 6*, Article 84.
  <https://doi.org/10.1038/s41534-020-00309-7>
- Steane, A. M. (1996). Multiple-particle interference and quantum error
  correction. *Proceedings of the Royal Society of London. Series A,
  452*(1954), 2551–2577. <https://doi.org/10.1098/rspa.1996.0136>

## How to Run

**Live demo:** <https://sruti-n.github.io/quantum_swarm_sim> — no installation
needed. The backend may take up to 60 seconds to wake from sleep on first load.

The simulation is available as a live demo at
<https://sruti-n.github.io/quantum_swarm_sim> — no installation needed. If you
want to run it locally or contribute to development, follow the steps below.

To run locally, you need Python 3 and `pip` installed.

### Option 1: One-click script

From the project root:

```
./run.sh
```

The script installs the dependencies from `backend/requirements.txt` and starts
the server.

### Option 2: Manual terminal setup

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

With either option, open <http://localhost:8000> in a browser once the server
has started. Press `Ctrl+C` in the terminal to stop it.

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
| Add / remove a robot (1–20; Entanglement needs 2+) | `+` / `-` |
| Halve / double shots (1–4096, default 256) | `[` / `]` |

### Robot Design

Open **Robot Design** at the bottom of the controls panel to change how the
robots look. Edit the JSON (body `oval` / `rect` / `diamond` / `arrow`, size,
color, sensor dots, trail) and press **Apply Shape**. If you write JavaScript,
turn on **Advanced: Custom Draw Code** and write your own
`drawRobot(ctx, x, y, angle, color, size)` function. **Reset to Default**
brings back the standard vehicle. See Section 4.5 of the spec for details.

## Deployment

The simulation is deployed as two separate services:

- **Frontend:** GitHub Pages (static HTML)
- **Backend:** Render (FastAPI + Qiskit)

To deploy your own instance:

1. Deploy the backend to Render by connecting your GitHub repository and
   pointing it at the `backend/` folder.
2. Enable GitHub Pages in your repository settings, set source to `main`
   branch and root folder.
3. The frontend will be available at
   <https://sruti-n.github.io/quantum_swarm_sim>.

> **Note:** The free tier backend may take 30–60 seconds to wake up after
> inactivity. The loading indicator in the simulation will display during
> this time.

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
├── spec/
│   └── quantum_swarm_simulation_spec.md
└── LICENSE                            # MIT License
```

### Data

`data/quantum_tests_data_stage1.csv` is preserved experimental data from the
Stage 1 servo prototype and is tracked in Git. Simulation runs append to
`data/quantum_swarm_data.csv`, which is generated at runtime and is **not**
tracked. Its columns extend the Stage 1 format so the two datasets remain
directly comparable:

```
Timestamp, Gate Name, Noise Rate, Num Robots, Mode, Probability, Angle,
Ideal Angle, Probability Error, Angle Error, Fidelity, Knowledge Level Selected,
Shots
```

`Shots` was added when the Shots slider was introduced. If an existing
`quantum_swarm_data.csv` has the older header, the backend renames it to
`quantum_swarm_data_old_format_<timestamp>.csv` and starts a new file rather
than appending misaligned rows.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## About the Researcher

Sruti Nallakukkala is a senior at Princeton International School of
Mathematics and Science (PRISMS), conducting independent research in the
Applied Physics Research Laboratory under the mentorship of Mr. George Heim.
This project is part of a two-year research arc exploring how robotic systems
can make quantum computing concepts accessible to broader audiences.
