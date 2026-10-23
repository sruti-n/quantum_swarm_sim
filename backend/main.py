"""FastAPI app for the quantum swarm simulation.

Serves the single-file frontend and exposes the WebSocket endpoint that carries
quantum results out to the browser. This layer replaces the serial/Arduino
transport used in the Stage 1 prototype: Python computes a quantum result,
sends it outward, the receiver acts on it. The serial port becomes a WebSocket.
"""

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from quantum_engine import QuantumEngine

app = FastAPI(title="Quantum Swarm Simulation")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = QuantumEngine()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_FILE = os.path.join(PROJECT_ROOT, "frontend", "index.html")

# Circuits run with the engine's default shot count (256) unless the user picks
# another value with the Shots slider; the prototype used 1024.
MIN_SHOTS = 1
MAX_SHOTS = 4096

MIN_ROBOTS = 1
MAX_ROBOTS = 20

VALID_GATES = ('h', 'x', 'id', 'sx', 'y', 'z')


@app.get("/")
def serve_frontend():
    if not os.path.exists(FRONTEND_FILE):
        return JSONResponse(
            status_code=404,
            content={"error": "frontend/index.html not found."},
        )
    return FileResponse(FRONTEND_FILE, media_type="text/html")


def clamp_robots(value):
    try:
        count = int(value)
    except (TypeError, ValueError):
        return MIN_ROBOTS
    return max(MIN_ROBOTS, min(MAX_ROBOTS, count))


def clamp_noise(value):
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, rate))


def clamp_shots(value):
    try:
        shots = int(value)
    except (TypeError, ValueError):
        return QuantumEngine.DEFAULT_SHOTS
    return max(MIN_SHOTS, min(MAX_SHOTS, shots))


def validate_gate(value):
    return value if value in VALID_GATES else 'h'


def validate_index(value, limit, name):
    try:
        index = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {name}: {value!r}")
    if not 0 <= index < limit:
        raise ValueError(f"{name} out of range: {index}")
    return index


def robot_noise_rates(message, num_robots, default):
    """Per-robot noise rates for a full measurement. The frontend sends
    `robot_noise` so a robot the user disturbed is measured at its local noise
    level; any robot without an entry uses the session noise rate."""
    rates = message.get("robot_noise")
    if not isinstance(rates, list):
        return [default] * num_robots
    return [
        clamp_noise(rates[i]) if i < len(rates) and rates[i] is not None else default
        for i in range(num_robots)
    ]


class SessionState:
    """Per-connection simulation state, so 'measure' knows what was simulated."""

    def __init__(self):
        self.gate = 'h'
        self.noise_rate = 0.1
        self.num_robots = MIN_ROBOTS
        self.shots = QuantumEngine.DEFAULT_SHOTS
        self.mode = 'superposition'
        self.knowledge_level = 'beginner'


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state = SessionState()

    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")

            if "knowledge_level" in message:
                state.knowledge_level = message["knowledge_level"]

            try:
                if message_type == "simulate":
                    await handle_simulate(websocket, state, message)
                elif message_type == "measure":
                    await handle_measure(websocket, state, message)
                elif message_type == "measure_robot":
                    await handle_measure_robot(websocket, state, message)
                elif message_type == "measure_pair":
                    await handle_measure_pair(websocket, state, message)
                elif message_type == "entangle":
                    await handle_entangle(websocket, state, message)
                elif message_type == "set_noise":
                    state.noise_rate = clamp_noise(message.get("noise_rate"))
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    })
            except Exception as exc:  # keep the socket alive on a bad request
                await websocket.send_json({"type": "error", "message": str(exc)})

    except WebSocketDisconnect:
        pass


async def handle_simulate(websocket, state, message):
    state.gate = validate_gate(message.get("gate", state.gate))
    state.noise_rate = clamp_noise(message.get("noise_rate", state.noise_rate))
    state.num_robots = clamp_robots(message.get("num_robots", state.num_robots))
    state.shots = clamp_shots(message.get("shots", state.shots))
    state.mode = 'superposition'

    # Each robot is its own qubit, so each gets its own circuit run.
    robots = []
    for robot_id in range(state.num_robots):
        prob = engine.simulate(state.gate, state.shots, state.noise_rate)
        robots.append({
            "id": robot_id,
            "angle": int(prob * 180),
            "prob": prob,
        })

    await websocket.send_json({
        "type": "superposition_state",
        "robots": robots,
        "gate": state.gate,
        "noise_rate": state.noise_rate,
        "ideal_angle": engine.IDEAL_VALUES[state.gate]["angle"],
        "shots": state.shots,
    })


async def handle_measure(websocket, state, message):
    # The spec'd message is just {type: "measure"}; the frontend also sends the
    # simulated context so a reconnect (fresh SessionState) still measures the
    # circuit the robots are showing.
    if "gate" in message:
        state.gate = validate_gate(message["gate"])
    if "noise_rate" in message:
        state.noise_rate = clamp_noise(message["noise_rate"])
    if "num_robots" in message:
        state.num_robots = clamp_robots(message["num_robots"])
    if "shots" in message:
        state.shots = clamp_shots(message["shots"])
    if message.get("mode") in ("superposition", "entanglement"):
        state.mode = message["mode"]

    noise_rates = robot_noise_rates(message, state.num_robots, state.noise_rate)

    if state.mode == 'entanglement':
        await handle_measure_bell_pairs(websocket, state, noise_rates)
        return

    robots = []
    fidelities = []

    # Measuring collapses the state: each robot draws one random outcome rather
    # than the averaged probability, so |0> lands on 0 deg and |1> on 180 deg.
    # Two measurements of the same H circuit can therefore disagree.
    for robot_id in range(state.num_robots):
        outcome = engine.measure_once(state.gate, noise_rates[robot_id])
        angle_error, fidelity = log_single_shot(state, state.gate, noise_rates[robot_id], outcome)
        fidelities.append(fidelity)

        robots.append({
            "id": robot_id,
            "angle": outcome["angle"],
            "prob": outcome["prob"],
            "error": angle_error,
        })

    swarm_fidelity = sum(fidelities) / len(fidelities) if fidelities else 0.0

    await websocket.send_json({
        "type": "measurement_result",
        "robots": robots,
        "fidelity": swarm_fidelity,
        "gate": state.gate,
        "shots": 1,
        "mode": "superposition",
    })


def log_single_shot(state, gate, noise_rate, outcome):
    """Log one robot's single-shot gate measurement; returns (angle_error, fidelity)."""
    prob_error, angle_error = engine.calculate_error(gate, outcome["prob"], outcome["angle"])
    fidelity = engine.calculate_fidelity(prob_error)
    engine.log_to_csv(
        prob=outcome["prob"],
        gate_name=gate,
        angle=outcome["angle"],
        prob_error=prob_error,
        angle_error=angle_error,
        noise_rate=noise_rate,
        num_robots=state.num_robots,
        mode='superposition',
        fidelity=fidelity,
        knowledge_level=state.knowledge_level,
        shots=1,
    )
    return angle_error, fidelity


def bell_pair_robots(state, pair_index, outcome, noise_rate):
    """Log both robots of one measured Bell pair and return their result dicts.

    Each robot's ideal is its partner's outcome, so a robot's error is 0 when
    the pair stayed correlated and 180 when decoherence broke it.
    """
    pair_fidelity = 1.0 if outcome["correlated"] else 0.0
    members = (
        (pair_index * 2, outcome["qubit_0"], outcome["angle_0"], outcome["angle_1"], outcome["qubit_1"]),
        (pair_index * 2 + 1, outcome["qubit_1"], outcome["angle_1"], outcome["angle_0"], outcome["qubit_0"]),
    )
    robots = []
    for robot_id, bit, angle, partner_angle, partner_bit in members:
        angle_error = abs(angle - partner_angle)
        robots.append({
            "id": robot_id,
            "angle": angle,
            "prob": float(bit),
            "error": angle_error,
            "ideal_angle": partner_angle,
        })
        engine.log_to_csv(
            prob=float(bit),
            gate_name='bell',
            angle=angle,
            prob_error=float(abs(bit - partner_bit)),
            angle_error=angle_error,
            noise_rate=noise_rate,
            num_robots=state.num_robots,
            mode='entanglement',
            fidelity=pair_fidelity,
            knowledge_level=state.knowledge_level,
            shots=1,
            ideal_angle=partner_angle,
        )
    return robots


async def handle_measure_bell_pairs(websocket, state, noise_rates):
    """Measure each entangled pair with the Bell state circuit (one shot per pair).

    Both robots in a pair collapse together: in the noiseless case they land on
    the same angle. Fidelity is the fraction of pairs that stayed correlated.
    A pair runs at the higher of its two robots' noise rates. With an odd robot
    count the last robot has no partner and is not measured.
    """
    robots = []
    correlated_pairs = 0
    num_pairs = state.num_robots // 2

    for pair_index in range(num_pairs):
        noise_rate = max(noise_rates[pair_index * 2], noise_rates[pair_index * 2 + 1])
        outcome = engine.simulate_bell_state(noise_rate)
        if outcome["correlated"]:
            correlated_pairs += 1
        robots.extend(bell_pair_robots(state, pair_index, outcome, noise_rate))

    await websocket.send_json({
        "type": "measurement_result",
        "robots": robots,
        "fidelity": correlated_pairs / num_pairs if num_pairs else 0.0,
        "gate": "bell",
        "shots": 1,
        "mode": "entanglement",
        "pairs_total": num_pairs,
        "pairs_correlated": correlated_pairs,
    })


async def handle_measure_robot(websocket, state, message):
    """Measure one robot's qubit with a single shot; the rest of the swarm is untouched.

    The robots are independent qubits, so this is the same one-shot circuit a
    full measurement runs for each robot, just for one of them. The noise rate
    is the robot's own (local disturbance or the slider) and does not change
    the session's noise rate.
    """
    robot_id = validate_index(message.get("id"), MAX_ROBOTS, "robot id")
    gate = validate_gate(message.get("gate", state.gate))
    noise_rate = clamp_noise(message.get("noise_rate", state.noise_rate))

    outcome = engine.measure_once(gate, noise_rate)
    log_single_shot(state, gate, noise_rate, outcome)

    await websocket.send_json({
        "type": "robot_measured",
        "id": robot_id,
        "outcome": outcome["bit"],
        "angle": outcome["angle"],
        "ideal_angle": engine.IDEAL_VALUES[gate]["angle"],
        "noise_rate": noise_rate,
    })


async def handle_measure_pair(websocket, state, message):
    """Measure one entangled pair with a single run of the Bell state circuit."""
    pair_id = validate_index(message.get("pair_id"), MAX_ROBOTS // 2, "pair id")
    noise_rate = clamp_noise(message.get("noise_rate", state.noise_rate))

    outcome = engine.simulate_bell_state(noise_rate)
    bell_pair_robots(state, pair_id, outcome, noise_rate)

    await websocket.send_json({
        "type": "pair_measured",
        "pair_id": pair_id,
        "outcome_a": outcome["qubit_0"],
        "outcome_b": outcome["qubit_1"],
        "noise_rate": noise_rate,
    })


async def handle_entangle(websocket, state, message):
    state.noise_rate = clamp_noise(message.get("noise_rate", state.noise_rate))
    if "num_robots" in message:
        state.num_robots = clamp_robots(message["num_robots"])
    state.mode = 'entanglement'

    # Two robots per pair; an odd robot out is left unpaired and not simulated.
    num_pairs = state.num_robots // 2

    pairs = []
    for pair_index in range(num_pairs):
        outcome = engine.simulate_bell_state(state.noise_rate)
        pairs.append({
            "a": {"id": pair_index * 2, "angle": outcome["angle_0"]},
            "b": {"id": pair_index * 2 + 1, "angle": outcome["angle_1"]},
            "correlated": outcome["correlated"],
        })

    await websocket.send_json({
        "type": "entanglement_state",
        "pairs": pairs,
        "noise_rate": state.noise_rate,
    })
