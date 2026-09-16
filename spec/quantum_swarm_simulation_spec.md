# Quantum Swarm Simulation — System Specification
**Project:** Bridging the Quantum Gap: A Robotic Modeling System for Visualizing
Decoherence and Qubit Behaviors
**Author:** Sruti Nallakukkala
**Institution:** Princeton International School of Mathematics and Science (PRISMS)
**Stage:** Simulation (Stage 1 of 2 — Physical prototype is Stage 2)
**Last Updated:** 16 September 2026 (see Section 13 for revision history)

---

## 1. Project Purpose

This simulation is the first dimension of a two-stage research project. It
demonstrates quantum computing concepts — superposition, entanglement, and
decoherence — through the behavior of a swarm of simulated robots. Each robot
acts as a physical analog of a qubit. The simulation is designed to be
intuitively legible to users with no quantum background, while also being
scientifically grounded through a live Qiskit backend.

The simulation fulfills the pedagogical goals of the project by engaging users
at the Analyze and Evaluate levels of Bloom's Taxonomy: users do not just watch,
they interact, make choices, and observe consequences.

---

## 2. System Architecture

The system is split into two layers that communicate over a WebSocket connection.

```
[ Python Backend ]  <——WebSocket——>  [ Browser Frontend ]
  - FastAPI server                     - HTML5 Canvas
  - Qiskit / Qiskit Aer                - Vanilla JavaScript
  - Quantum circuit simulation         - Robot swarm rendering
  - Noise model (depolarizing error)   - Boids algorithm
  - Gate logic                         - User interaction layer
  - Data logging to CSV                - Explanation panel
```

### Why this architecture
The Python backend already exists in the project (quantum_robot.py,
superposition_test_bridge.py, qiskit_test_bridge.py). The browser frontend
replaces the Arduino/serial layer with a visual simulation layer. The
communication pattern is identical in concept: Python computes a quantum
result, sends it outward, the receiver acts on it. The serial port becomes
a WebSocket.

---

## 3. Quantum Backend (Python / FastAPI)

### 3.1 Supported Quantum Gates
The following gates are supported, carried over directly from quantum_robot.py:

| Gate | ID  | Ideal P(|1⟩) | Ideal Angle | Description                        |
|------|-----|--------------|-------------|------------------------------------|
| Hadamard | h | 0.5       | 90°         | Creates superposition              |
| Pauli-X  | x | 1.0       | 180°        | Flips qubit state                  |
| Identity | id | 0.0      | 0°          | Does nothing to the qubit          |
| √X   | sx  | 0.5          | 90°         | Half-flip, partial superposition   |
| Pauli-Y  | y | 1.0       | 180°        | Rotates around Y-axis              |
| Pauli-Z  | z | 0.0       | 0°          | Rotates around Z-axis (phase flip) |

### 3.2 Simulation Logic
Carried over from quantum_robot.py with the following behavior:
- Each robot is its own qubit, so each robot gets its own circuit run
- Run the Qiskit circuit with a user-selected number of shots:
  default 256, adjustable from 1 to 4096 in powers of two (Section 4.4).
  The Stage 1 prototype used 1024; 256 was chosen as the default because it
  is statistically sufficient for a pedagogical demonstration (standard
  error on P(|1⟩) is at most 0.5/√256 ≈ 0.03) and returns results faster
- The backend clamps shots to 1–4096; a missing or invalid value falls back to 256
- Apply depolarizing noise model at the user-specified noise rate
- Return: probability of |1⟩, computed angle (prob × 180), ideal angle,
  probability error, angle error, gate name, noise rate
- Every measurement is logged to data/quantum_swarm_data.csv (Section 7)

### 3.3 Entanglement Simulation (New)
For entangled robot pairs:
- Run a 2-qubit Bell state circuit: H gate on qubit 0, then CNOT gate
  (qubit 0 controls qubit 1)
- Measure both qubits
- Return both outcomes: the state of qubit 0 drives Robot A's behavior,
  the state of qubit 1 drives Robot B's behavior
- Because of the Bell state, outcomes are always correlated:
  both |00⟩ or both |11⟩
- Noise is applied to both qubits via the same depolarizing error model
- Each pair runs a single shot, so the Shots setting does not affect Entanglement mode
- **Measuring entangled pairs:** when Measure is triggered in Entanglement mode,
  each pair runs a fresh Bell state circuit (one shot) and both robots collapse
  together to that outcome (0° or 180°). Each robot's ideal is its partner's
  outcome, so its error is 0° if the pair stayed correlated and 180° if
  decoherence broke the correlation. Fidelity is the fraction of pairs that
  stayed correlated. Measured with the simulator over 80 pairs: 80/80
  correlated at noise 0.0 and 50/80 at noise 0.6
- Robots are paired in order (0–1, 2–3, …). With an odd robot count the last
  robot is left unpaired and is not simulated. Entanglement mode therefore
  requires at least 2 robots (Section 4.4)

### 3.4 API Endpoints (FastAPI + WebSocket)

```
GET  /                         Serve the frontend HTML file
WS   /ws                       Main WebSocket connection

WebSocket message types (frontend → backend):
  { type: "simulate",  gate: "h", noise_rate: 0.1, num_robots: 4, shots: 256 }
  { type: "measure" }          Trigger wavefunction collapse
  { type: "measure",   gate: "h", noise_rate: 0.1, num_robots: 4, shots: 256,
    mode: "superposition" }    Same, with optional context (see note)
  { type: "entangle",  noise_rate: 0.1, num_robots: 4 }
  { type: "set_noise", noise_rate: 0.3 }

  Any message may also carry knowledge_level: "beginner" | "intermediate" |
  "advanced", which is recorded for CSV logging.

WebSocket message types (backend → frontend):
  { type: "superposition_state", robots: [ {id, angle, prob}, ... ],
    gate: "h", noise_rate: 0.1, ideal_angle: 90, shots: 256 }
  { type: "measurement_result", robots: [ {id, angle, prob, error}, ... ],
    fidelity: 0.92, gate: "h", shots: 256, mode: "superposition" }
  { type: "measurement_result",            (Entanglement mode)
    robots: [ {id, angle, prob, error, ideal_angle}, ... ],
    fidelity: 0.75, gate: "bell", shots: 1, mode: "entanglement",
    pairs_total: 4, pairs_correlated: 3 }
  { type: "entanglement_state",
    pairs: [ {a: {id, angle}, b: {id, angle}, correlated: true}, ... ],
    noise_rate: 0.1 }
  { type: "error", message: "..." }
```

**Session state and the measure context.** The backend keeps per-connection
state (gate, noise rate, robot count, shots, mode) so a bare
`{ type: "measure" }` measures whatever was last simulated or entangled. That
state is lost if the WebSocket reconnects, so the frontend also sends the
simulated gate, noise rate, robot count, shots, and mode with every measure.
The mode decides which circuit is measured: the selected gate per robot, or a
Bell state per pair. In Entanglement mode each robot carries `ideal_angle`
(its partner's outcome), and an unpaired odd robot is left out of `robots`. Fields that are present
override the session state; fields that are absent leave it unchanged.

**Validation.** Robot count is clamped to 1–20, noise rate to 0.0–1.0, and
shots to 1–4096. An unknown gate falls back to h. An unknown message type or a
failed request returns an `error` message and keeps the connection open.

---

## 4. Browser Frontend (HTML5 Canvas + Vanilla JavaScript)

### 4.1 Layout

```
+--------------------------------------------------+
|  HEADER: Project title + mode indicator          |
+-------------------+------------------------------+
|                   |                              |
|   SIMULATION      |   CONTROL PANEL              |
|   CANVAS          |   - Gate selector            |
|   (robots move    |   - Robot count (1–20)       |
|    here; loading  |   - Noise rate slider        |
|    overlay shows  |   - Shots slider             |
|    here while a   |   - Mode buttons             |
|    circuit runs)  |   - Simulate/Measure/Reset   |
|                   |   - Keypress hints           |
+-------------------+------------------------------+
|  EXPLANATION PANEL (changes dynamically)         |
|  [ Beginner | Intermediate | Advanced ] toggle   |
|  Status label, gate/mode explanation, Shots      |
+--------------------------------------------------+
|  DATA PANEL: gate | prob | angle | ideal | error |
|              noise | shots | fidelity            |
+--------------------------------------------------+
```

Below 860px wide, the canvas and control panel stack vertically.

### 4.2 Simulation Canvas
- HTML5 Canvas, 2D rendering context
- Dark background (space/quantum aesthetic)
- Robots are rendered as directional vehicles inspired by Braitenberg vehicles:
  - Body: a chassis 24px long by 16px wide
  - Front: a flat edge with two small light sensor dots, one on each side,
    like headlights or eyes. These make the facing direction obvious, so there
    is no separate needle
  - Back: a rounded rear edge
  - The whole vehicle rotates to face its current heading. A measured angle
    of 0° faces up, 90° faces right, and 180° faces down
  - Size: full size up to 8 robots, shrinking gradually to 75% at 20 robots
    to reduce crowding
- Robot color indicates state:
  - Blue, wandering: superposition (pre-measurement)
  - Gold, synchronized: entangled pair
  - Green: measured, at ideal position
  - Red/orange: measured, with visible decoherence error
    (the further from ideal, the more orange/red; full red at 90° of error)
- Entangled pairs are joined by a dashed gold line that fades as noise rises
- Trail effect: faint path laid down from the center of each vehicle's rear
  edge, showing recent movement. The trail breaks rather than drawing a line
  across the canvas when a robot wraps to the opposite edge
- Robots that leave one edge of the canvas reappear at the opposite edge

**Loading overlay**
While the backend is running a circuit, a translucent overlay covers the
canvas so the user knows a result is on its way:
- Simulate: "Running quantum circuit..." with a detail line such as
  "Simulating H gate with noise rate 0.10 · 256 shots"
  (in Entanglement mode: "Simulating Bell pairs (H + CNOT) with noise rate 0.10")
- Measure: "Collapsing wavefunction..." with a detail line such as
  "Measuring H gate with noise rate 0.10 · 256 shots"
  (in Entanglement mode: "Measuring Bell pairs with noise rate 0.10 · 1 shot per pair")
- Below the text, a thin animated scanning line. It stays still when the
  user's system is set to reduce motion
- The overlay disappears as soon as superposition_state, entanglement_state,
  or measurement_result arrives, and also on an error, Reset, or disconnect
- While the overlay is showing, further Simulate and Measure triggers are
  ignored so repeated clicks or a held key cannot queue up circuit runs

### 4.3 Robot Behavior by Mode

**Superposition Mode**
- Robots move independently, each with its own randomized velocity
  and wandering pattern
- Movement is genuinely chaotic and individualistic — no coordination
- Each vehicle turns to face the direction it is driving, with a slight
  wobble, so it always moves nose-first
- Robots do not collide with each other (pass through)
- This represents the undefined, probabilistic nature of superposition
- On measurement trigger: all robots snap to an angle determined by
  the Qiskit simulation result for the selected gate + noise rate
- The snap is animated: robots slow to a stop while smoothly rotating to
  their final angle over ~0.5 seconds, then hold
- A single robot is a valid configuration in this mode

**Entanglement Mode**
- Requires at least 2 robots. Switching to this mode with 1 robot raises the
  count to 2 and the status label explains why
- Robots organized into pairs (2 robots per pair); with an odd count the last
  robot is unpaired and wanders on its own as in Superposition Mode
- Within each pair, robots use a simplified Boids algorithm:
  - Alignment: each robot steers its velocity toward its partner's, so the
    pair travels in the same direction
  - Cohesion: robots in a pair are drawn toward each other
  - Separation: robots maintain a minimum distance within the pair
  - Vehicles face the direction they are driving and keep a minimum cruising
    speed so a balanced pair never stalls
- Different pairs do NOT coordinate with each other
- When one robot in a pair receives a measurement result,
  its partner instantly mirrors the correlated outcome: on Measure, each pair
  is measured with a Bell state circuit and both robots snap to the same
  angle (0° or 180°) unless decoherence broke the pair (Section 3.3)
- A measured robot whose pair stayed correlated turns green; one whose pair
  broke turns red, and its ghost faces its partner's angle. An unpaired odd
  robot is not measured and stays blue
- Decoherence is visible as the alignment gradually breaking down
  over time — random jitter proportional to the noise rate is added to each
  robot's direction, so the pair drifts apart in heading as noise increases

**Decoherence Visualization (both modes)**
- A visible "ghost" shows where the robot would be at ideal (zero noise):
  the same vehicle shape at 20% opacity, facing the ideal angle for the gate
- The ghost appears after measurement, drawn beneath the robot, so the part
  that shows is the angular gap between ideal and actual
- The gap between ghost and actual robot is the decoherence
- As noise rate increases via the slider, the gap grows visibly

### 4.4 User Interaction

**Controls Panel**

| Control | Type | Function |
|---------|------|----------|
| Gate selector | Dropdown | Choose quantum gate (h, x, id, sx, y, z) |
| Robot count | Number input + slider | Set number of robots (1–20, default 4; minimum 2 in Entanglement mode) |
| Noise rate | Slider (0.0–1.0, default 0.1) | Set depolarizing noise rate |
| Shots | Slider (1–4096 in powers of two, default 256) | Set how many times each robot's circuit is run; applies on the next Simulate or Measure |
| Mode | Toggle buttons | Switch between Superposition / Entanglement |
| Simulate | Button | Run quantum circuit, enter superposition/entangle mode |
| Measure | Button | Collapse wavefunction, snap robots to result |
| Reset | Button | Return all robots to neutral state |

In Entanglement mode a note under the Shots slider explains that entangling
and measuring both run one shot per pair, so the setting does not apply there.

**Button behavior**
- Simulate, Measure, and Reset are disabled only while the WebSocket is
  disconnected
- Measure stays clickable before anything has been simulated; it then shows
  "Nothing to measure yet — press S or Simulate first." instead of sending
- Measure always measures the gate that was last simulated, even if the gate
  selector has changed since
- Changing the robot count or the mode resets the simulation to idle

**Keyboard Shortcuts**
| Key | Action |
|-----|--------|
| Space | Measure (collapse wavefunction) |
| S | Simulate (run circuit) |
| R | Reset |
| E | Toggle Entanglement mode |
| 1–6 | Select gate (1=h, 2=x, 3=id, 4=sx, 5=y, 6=z) |
| ↑ / ↓ | Increase / decrease noise rate by 0.05 |
| + / - | Add / remove a robot (within cap) |
| [ / ] | Halve / double the number of shots |

All keyboard shortcuts are displayed as small hints next to their
corresponding controls in the UI.

Space works wherever keyboard focus is, including on the gate dropdown,
sliders, robot count box, and buttons, and is only ignored while typing in a
text field or on a checkbox. It never scrolls the page, opens the dropdown, or
activates a focused button, and holding it down triggers a single measurement.
The other shortcuts are ignored while a dropdown, input, or text area has
focus, so those controls keep their normal keyboard behavior.

**Robot count cap:** Maximum 20 robots. Above this, performance on
a standard laptop degrades noticeably. A warning appears at 15+.

### 4.5 Robot Design (Custom Shape Loader)

A collapsible "Robot Design" section at the bottom of the controls panel lets
users replace the robot shape. It is closed by default. The canvas has its own
height, so opening the section does not resize the simulation, and on wide
screens the canvas stays in view while the panel scrolls. The shape is purely
visual: WebSocket messages, quantum logic, and data logging are unaffected.

It works at two levels.

**Level 1 — JSON config (for non-coders)**

A text area pre-filled with:

```json
{
  "body": "oval",
  "width": 24,
  "height": 16,
  "color": null,
  "sensors": true,
  "trail": true
}
```

| Field | Allowed values | Effect |
|-------|----------------|--------|
| body | "oval", "rect", "diamond", "arrow" | Body outline; the front always faces the heading |
| width | number, 10–40 | Length along the heading, in px at default robot count |
| height | number, 10–30 | Width across the heading, in px at default robot count |
| color | null, or a hex color such as "#ff6600" | null keeps the state color coding (Section 4.2); a hex color overrides it for every state |
| sensors | true / false | Show the two sensor dots at the front |
| trail | true / false | Show the trail |

- **Apply Shape** validates the text and immediately redraws every robot and
  ghost. Fields left out take the values above.
- Text that is not valid JSON (including single-quoted keys) shows:
  "Invalid shape config — check your JSON syntax"
- Valid JSON with a bad value shows a specific message in the same style,
  for example: "Invalid shape config — "width" must be a number from 10 to 40",
  "Invalid shape config — unknown field "colour"", or
  "Invalid shape config — it must be a { ... } object"
- On any error the current shape is kept and the simulation keeps running.

**Level 2 — Custom draw code (for coders)**

Turning on the "Advanced: Custom Draw Code" checkbox replaces the JSON text
area with a larger code text area, under the warning
"Advanced mode — JavaScript knowledge required". It is pre-filled with:

```js
// ctx is the HTML5 Canvas 2D context
// x, y is the robot center position
// angle is the robot heading in radians
// color is the current state color string
// size is the base size unit (default 20)
function drawRobot(ctx, x, y, angle, color, size) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  // draw your robot here
  ctx.fillStyle = color;
  ctx.fillRect(-size/2, -size/3, size, size*0.67);
  ctx.restore();
}
```

- **Apply Code** compiles the code, requires a function named `drawRobot`,
  and test-draws it once on an off-screen canvas before using it.
- A syntax error, a missing `drawRobot`, or an error during the test draw is
  shown inline ("Code error — TypeError: …") and the current shape is kept.
- If the function throws later while animating, the simulation switches back to
  the default vehicle and shows the error inline. It never stops the animation.
- After every call the canvas drawing state is reset, so code that forgets
  `ctx.restore()` or changes transparency cannot distort the rest of the canvas.
- `size` follows the robot count scaling (20 at up to 8 robots, down to 15 at 20).
- The code runs only in the user's own browser tab and is not saved. An
  infinite loop in the code cannot be caught and will freeze the tab.

**Shared behavior**
- **Reset to Default** restores the built-in Braitenberg vehicle (Section 4.2)
  and refills both text areas with their templates. The JSON template's "oval"
  is a starting point to edit, so applying it unchanged gives an oval, not the
  default vehicle.
- Ghost outlines use the same custom shape, drawn in a neutral gray at 20%
  opacity (a JSON `color` override does not tint ghosts). Custom code receives
  that gray as `color` with transparency already set to 20%.
- The trail starts at the center of the rear edge: half of `width` behind
  the center for JSON shapes, and `size / 2` behind it for custom code.
- The shape stays in effect across Simulate, Measure, Reset, and mode changes,
  and resets on page reload.

---

## 5. Explanation Panel

The explanation panel sits below the canvas and updates dynamically
based on the current mode, gate, and simulation state.

### 5.1 Knowledge Level Toggle
Three modes, user-selectable via a toggle at the top of the panel:

**Beginner** (no prerequisites assumed)
- Uses everyday analogies
- Example for H gate in superposition:
  "Think of a coin spinning in the air. While it's spinning, it's
  neither heads nor tails — it's both at once. That's superposition.
  The robots are doing the same thing right now. Press Space to
  'catch' the coin and see which way it lands."
- Example for entanglement:
  "These robots are connected like twins who always wear matching
  outfits, no matter how far apart they are. Watch what happens
  when you change one."

**Intermediate** (high school physics background)
- Uses quantum vocabulary with brief definitions
- Example for H gate:
  "The Hadamard gate puts the qubit into an equal superposition of
  |0⟩ and |1⟩ — P(|1⟩) = 0.5. Each robot's wandering represents
  this undefined state. Measurement forces a definite outcome."
- Mentions probability, gates, measurement

**Advanced** (quantum computing background)
- Full technical description
- Example for H gate:
  "H = (1/√2)[[1,1],[1,-1]]. Applied to |0⟩, produces
  (|0⟩ + |1⟩)/√2. Depolarizing noise at rate ε maps ρ →
  (1-ε)ρ + (ε/3)(XρX + YρY + ZρZ). The servo angle maps
  P(|1⟩) × 180°, consistent with Nallakukkala (2026)."

### 5.2 Shots Explanation
Below the gate or entanglement explanation, a second paragraph headed
"Shots" explains the Shots control. It follows the same knowledge level
toggle and is shown in both modes.

**Beginner**
  "A shot is one run of the experiment. Each run only ever gives a yes or a
  no — like one toss of a coin, which lands heads or tails, never
  half-and-half. To find out how likely heads really is, you toss it many
  times and count. More shots means a more trustworthy answer. Try 1 shot
  with the H gate and watch the robots jump all the way to 0° or 180°."

**Intermediate**
  "A single measurement returns only 0 or 1, so P(|1⟩) has to be estimated
  by running the circuit many times (shots) and counting the 1s. For the H
  gate that estimate scatters by about ±0.5/√N: roughly ±0.03 at 256 shots
  and ±0.016 at 1024. This sampling scatter is separate from noise — more
  shots shrink it, but they cannot remove the error that noise causes."

**Advanced**
  "The reported probability is the estimator p̂ = k/N, where
  k ~ Binomial(N, p) over N shots. It is unbiased with standard error
  √(p(1−p)/N), largest at p = 0.5 (0.5/√N) and zero at p = 0 or 1, so X, Y,
  ID and Z are exact at ε = 0 while H and SX are not. Because fidelity is
  computed as 1 − |p̂ − p_ideal|, finite sampling lowers it even without noise
  (mean |p̂ − p| ≈ 0.4/√N at p = 0.5 for large N). The angle int(p̂ × 180)
  also has a resolution of 180/N degrees, so at N = 1 only 0° or 180° is
  possible."

These figures were checked against the simulator: with 20 robots on the H
gate and no noise, the observed spread of P(|1⟩) was 0.028 at 256 shots
(predicted 0.031) and 0.0085 at 4096 shots (predicted 0.0078).

### 5.3 Dynamic Status Label
A single line above the explanation that changes based on simulation state:

| State | Label |
|-------|-------|
| Idle | "Select a gate and press S or Simulate to begin." |
| Circuit running (after Simulate) | "Quantum circuit running..." |
| Superposition active | "Robots are in superposition — state undefined." |
| Measuring | "Collapsing wavefunction..." |
| Measured, fidelity ≥ 0.8 | "Measurement complete. Fidelity: [value]" |
| Measured, fidelity < 0.8 | "High decoherence detected. Results unreliable." |
| Bell pairs measured, fidelity ≥ 0.8 | "Measurement complete. [n] of [total] pairs stayed correlated. Fidelity: [value]" |
| Bell pairs measured, fidelity < 0.8 | "High decoherence detected. Only [n] of [total] pairs stayed correlated." |
| Entangled | "Robots entangled. Observe correlated behavior." |
| Decoherence breaking entanglement (any pair uncorrelated) | "Decoherence is breaking entanglement." |
| Measure pressed while idle | "Nothing to measure yet — press S or Simulate first." |
| Entanglement selected with 1 robot | "Entanglement needs a pair of qubits, so the robot count was raised to 2." |
| Simulate or Measure while disconnected | "Not connected to the backend — cannot simulate yet." / "… cannot measure yet." |
| Connection lost while a circuit was running | "Connection lost while the circuit was running — retrying." |
| Backend error | "Error: [message]" |

---

## 6. Data Panel

A compact bar below the explanation panel showing live values:

```
Gate: H  |  P(|1⟩): 0.487  |  Angle: 87°  |  Ideal: 90°  |
Error: 3°  |  Noise Rate: 0.10  |  Shots: 256  |  Fidelity: 0.97
```

Values update after each measurement. P(|1⟩), Angle, and Error are averages
across all robots, and Fidelity is the swarm average. Fidelity is displayed as
both a number and a small color-coded bar (green above 0.85, gold above 0.6,
red below). Shots shows the slider value and, after a result, the shot count
the backend actually used. All values are logged to CSV (Section 7).

After measuring Bell pairs, Gate shows BELL, P(|1⟩) is the fraction of
measured robots that landed on |1⟩, Ideal shows — (each robot's ideal is its
partner's outcome), Shots shows 1, and Fidelity is the fraction of pairs that
stayed correlated.

---

## 7. Data Logging

Every measurement event is logged to data/quantum_swarm_data.csv, one row per
robot, with columns:

```
Timestamp, Gate Name, Noise Rate, Num Robots, Mode,
Probability, Angle, Ideal Angle, Probability Error,
Angle Error, Fidelity, Knowledge Level Selected, Shots
```

This extends the existing data format from quantum_robot_v1.py and
data/quantum_tests_data_stage1.csv, making the simulation data directly
comparable to the physical prototype data collected in Stage 1 of the project.

Bell pair measurements (Entanglement mode) are logged with Gate Name `bell`,
Shots `1`, Probability `0` or `1` (the single-shot outcome), Ideal Angle set to
the partner's angle, and Fidelity `1` if the pair stayed correlated, else `0`.

`Shots` was added with the Shots slider. It is the last column so the earlier
columns keep their Stage 1 positions, and it matters for analysis: the same
probability error means something very different at 1 shot than at 4096.

If an existing quantum_swarm_data.csv has a different header (for example, one
written before the Shots column existed), the backend does not append to it.
It renames the file to `quantum_swarm_data_old_format_<timestamp>.csv` and
starts a new file, so rows are never misaligned. Rows in an archived file have
no recorded shot count; they were run at 1024 shots before the default changed
and at 256 afterwards, and the two cannot be told apart.

Runtime CSVs in data/ are gitignored; only the Stage 1 dataset is tracked.

---

## 8. File Structure

```
quantum_swarm_sim/
├── backend/
│   ├── main.py                        # FastAPI app, WebSocket handler
│   ├── quantum_engine.py              # Qiskit simulation logic (adapted from quantum_robot_v1.py)
│   ├── quantum_robot_v1.py            # Stage 1 prototype, preserved unchanged for reference
│   └── requirements.txt               # fastapi, uvicorn, qiskit, qiskit-aer, websockets
├── frontend/
│   └── index.html                     # Single HTML file, all CSS and JS inline, no external deps
├── data/
│   ├── quantum_tests_data_stage1.csv  # Stage 1 experimental data (tracked)
│   ├── .gitkeep                       # Keeps data/ tracked
│   ├── quantum_swarm_data.csv         # Auto-created on first measurement (gitignored)
│   └── quantum_swarm_data_old_format_<timestamp>.csv   # Archived older-format logs, if any (gitignored)
├── docs/                              # Figures: concept map, methodology, Bloom's taxonomy, gate results
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
│   └── quantum_swarm_simulation_spec.md   # This document
└── README.md
```

---

## 9. Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Quantum simulation | Qiskit + Qiskit Aer | Already in use in project |
| Backend server | FastAPI + Uvicorn | Lightweight, WebSocket-native, Python |
| Frontend rendering | HTML5 Canvas + Vanilla JS | No framework overhead, co-principal's architecture philosophy |
| Communication | WebSocket | Real-time, bidirectional, needed for live robot updates |
| Data storage | CSV | Consistent with existing project data format |
| Physics | Custom (no library) | Boids implemented from scratch for full control |

---

## 10. What This Specification Does NOT Include

The following are explicitly out of scope for Stage 1 (simulation):

- A noise-correcting AI model (removed by researcher decision)
- Physical robot control (Arduino/serial — this is Stage 2)
- Multi-user co-op mode (may be added later, not required for proof-of-concept)
- Authentication or user accounts
- Mobile-specific layout (desktop browser only for now)
- 3D rendering

---

## 11. Relationship to Existing Code

| Existing File | Role in Simulation |
|--------------|-------------------|
| backend/quantum_robot_v1.py (originally quantum_robot.py) | quantum_engine.py is a direct adaptation — serial removed, WebSocket added |
| legacy/superposition_test_bridge.py | RY rotation logic informs superposition mode |
| legacy/qiskit_test_bridge.py | Single-shot measurement logic informs Measure trigger |
| legacy/data_analysis.py | Data panel visualizations inspired by existing graphs |
| data/quantum_tests_data_stage1.csv (originally quantum_tests_data.csv) | New CSV extends same column format |
| legacy/sketch_apr20a.ino | Not used in simulation; relevant in Stage 2 |

---

## 12. Claude Code Prompt Sequence

> **Historical record.** These are the original prompts used to build the
> first version of the project, kept unchanged. Some details in them are now
> out of date (for example, circular robots with a directional needle, a
> 4-robot minimum, and 1024 shots). Sections 1–11 describe the current system,
> and Section 13 lists what changed afterwards.

Run these prompts in order, one at a time. Wait for Claude Code to finish
each step before sending the next. Do not combine them into one message —
Claude Code does better work when each task is clearly bounded.

---

### PROMPT 1 — GitHub Repository Setup

Paste this first, before any files exist:

> "I need to set up a GitHub repository for my Applied Physics research
> project. My VS Code and GitHub are already connected.
>
> Please do the following:
> 1. Initialize a new Git repository in the current folder
> 2. Create a .gitignore file appropriate for a Python + JavaScript project
>    (ignore __pycache__, .env, node_modules, *.pyc, .DS_Store, and
>    any .csv files in the data/ folder since those are generated at runtime)
> 3. Create a README.md with the following content:
>    - Project title: Bridging the Quantum Gap: A Robotic Modeling System
>      for Visualizing Decoherence and Qubit Behaviors
>    - Author: Sruti Nallakukkala, PRISMS Applied Physics Research Lab
>    - One paragraph describing the project (quantum swarm simulation,
>      Stage 1 of a two-stage research project, pedagogical tool for
>      quantum computing education)
>    - A section called 'How to Run' (leave it as TODO for now)
>    - A section called 'Project Structure' (leave it as TODO for now)
> 4. Make an initial commit with message: 'Initial commit — project setup'
>
> Do not push to GitHub yet. I will do that manually once the structure
> looks right."

---

### PROMPT 2 — Folder Structure and Existing File Organization

Paste this after Prompt 1 is complete:

> "Now create the full folder structure for this project and organize
> the existing files I already have.
>
> Create these folders:
> - backend/
> - frontend/
> - data/
> - spec/
> - legacy/
>
> Then move or copy the following existing files into the correct locations:
> - quantum_robot.py → backend/quantum_robot_v1.py (rename to v1 so we
>   preserve the original while building the new version beside it)
> - data_analysis.py → legacy/data_analysis.py
> - h_gate.py → legacy/h_gate.py
> - python_test_bridge.py → legacy/python_test_bridge.py
> - qiskit_test_bridge.py → legacy/qiskit_test_bridge.py
> - superposition_test_bridge.py → legacy/superposition_test_bridge.py
> - sketch_apr20a.ino → legacy/sketch_apr20a.ino
> - servo_test.ino → legacy/servo_test.ino
> - quantum_tests_data.csv → data/quantum_tests_data_stage1.csv
> - quantum_swarm_simulation_spec.md → spec/quantum_swarm_simulation_spec.md
>
> Create an empty placeholder file called .gitkeep inside the data/ folder
> so Git tracks the folder even when no CSV exists yet.
>
> Then commit everything with message: 'feat: organize project structure
> and archive Stage 1 prototype files'"

---

### PROMPT 3 — Python Backend

Paste this after Prompt 2 is complete:

> "Now build the Python backend. Read the full specification at
> spec/quantum_swarm_simulation_spec.md before writing any code.
> Also read backend/quantum_robot_v1.py — the new quantum_engine.py
> should be a direct adaptation of that file.
>
> Create the following files in backend/:
>
> 1. requirements.txt — containing exactly:
>    fastapi
>    uvicorn[standard]
>    qiskit
>    qiskit-aer
>    websockets
>
> 2. quantum_engine.py — adapted from quantum_robot_v1.py with:
>    - Serial/Arduino code completely removed
>    - All gate logic and IDEAL_VALUES preserved exactly
>    - simulate() method preserved exactly, including noise model
>    - New method simulate_bell_state(noise_rate) for entanglement mode
>      (H gate on qubit 0, CNOT targeting qubit 1, measure both,
>      return correlated outcomes for robot pair)
>    - calculate_error() and log_to_csv() preserved
>    - log_to_csv() updated to also accept num_robots, mode, and
>      knowledge_level columns, writing to data/quantum_swarm_data.csv
>    - No changes to any quantum logic
>
> 3. main.py — FastAPI app with:
>    - GET / that serves frontend/index.html
>    - WebSocket endpoint at /ws
>    - Handles all four message types from the spec:
>      simulate, measure, entangle, set_noise
>    - Returns all four response types from the spec:
>      superposition_state, measurement_result, entanglement_state, error
>    - Imports QuantumEngine from quantum_engine.py
>
> Do not use any libraries not in requirements.txt.
> Commit when done with message: 'feat: implement Python backend
> with FastAPI and Qiskit quantum engine'"

---

### PROMPT 4 — Browser Frontend

Paste this after Prompt 3 is complete:

> "Now build the browser frontend. Read the full specification at
> spec/quantum_swarm_simulation_spec.md, specifically sections 4 and 5,
> before writing any code.
>
> Create frontend/index.html as a single self-contained file with all
> CSS and JavaScript inline. No external dependencies, no frameworks,
> no CDN links.
>
> The file must implement exactly:
>
> Layout (Section 4.1 of spec):
> - Header with project title and current mode indicator
> - Left: simulation canvas (dark background, quantum aesthetic)
> - Right: controls panel with all controls from Section 4.4
> - Below: explanation panel with Beginner/Intermediate/Advanced toggle
> - Below: data panel showing live values
>
> Canvas rendering (Section 4.2):
> - Robots as circular agents with directional needle
> - Color coding: blue=superposition, gold=entangled, green=measured
>   ideal, red/orange=measured with decoherence error
> - Ghost outline showing ideal position
> - Trail effect behind each robot
>
> Robot behavior (Section 4.3):
> - Superposition mode: independent chaotic wandering, snap on measure
> - Entanglement mode: Boids algorithm within pairs, correlated outcomes
> - Decoherence: gap between ghost and actual robot grows with noise
>
> All controls and keyboard shortcuts from Section 4.4.
> All explanation text for all three knowledge levels from Section 5.1.
> All dynamic status labels from Section 5.2.
> All data panel fields from Section 6.
>
> WebSocket connection to ws://localhost:8000/ws.
>
> Do not use any JavaScript frameworks.
> Commit when done with message: 'feat: implement browser frontend
> with canvas simulation and explanation panel'"

---

### PROMPT 5 — Final Checks and README Update

Paste this after Prompt 4 is complete:

> "Do a final review of the complete project. Check that:
> 1. backend/main.py correctly serves frontend/index.html at GET /
> 2. The WebSocket message types in main.py exactly match the spec
> 3. The frontend WebSocket address matches what the backend serves
> 4. quantum_engine.py has no remaining serial/Arduino imports or code
> 5. requirements.txt has all necessary packages
>
> Then update README.md:
> - Fill in the 'How to Run' section with exact terminal commands:
>   cd backend
>   pip install -r requirements.txt
>   uvicorn main:app --reload
>   Then open http://localhost:8000 in a browser
> - Fill in the 'Project Structure' section with the actual folder
>   structure as it now exists
>
> Then make a final commit with message: 'docs: complete README and
> final project review'
>
> Then tell me if there is anything I need to do manually before
> pushing to GitHub."

---

## 13. Revision History

Changes made after the original build (Prompts 1–5), newest first.

| Commit | Change |
|--------|--------|
| feat: add two-tier custom robot shape loader | Robot Design section (Section 4.5): Level 1 JSON shape config (oval, rect, diamond, arrow; size, color override, sensors, trail) and Level 2 custom `drawRobot` code, both applied to robots and ghosts with inline errors. Canvas given its own sticky height so the panel can grow |
| 5e681f5 | Measure in Entanglement mode now measures each pair with the Bell state circuit, so partners collapse together; error is against the partner's outcome and fidelity is the fraction of pairs that stayed correlated. Bell rows are logged with gate `bell` |
| 75aeaab | Spec brought up to date with all changes below |
| dddd208 | Robots redesigned as Braitenberg-style vehicles with a flat front, two sensor dots, and a rounded rear; the needle was removed. The ghost uses the same shape at 20% opacity and the trail follows the rear edge. Vehicles face their direction of travel, and entangled pairs use velocity alignment. Minimum robot count lowered from 4 to 1, with at least 2 required in Entanglement mode |
| a6d4935, 934d64e | Shots slider (1–4096, default 256) with `[` / `]` shortcuts and a Shots explanation at all three knowledge levels. Backend accepts `shots` on simulate and measure and echoes it back. CSV gains a trailing Shots column; older-format files are archived. Active knowledge-level button no longer loses its label on hover |
| b76767c | Default shots reduced from 1024 to 256. Loading overlay on the canvas while a circuit runs, with matching "Quantum circuit running..." and "Collapsing wavefunction..." status labels |
| 528a5ee | Measure button and Space shortcut repaired. Space now works while a control has focus and cannot re-trigger a focused button; holding it sends one request. Measure is clickable before simulating and explains what to do. Measure sends the simulated gate, noise rate, and robot count so reconnects and gate changes do not measure the wrong circuit; measurement_result includes the gate |
