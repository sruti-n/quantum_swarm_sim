"""FastAPI app for the quantum swarm simulation.

Serves the single-file frontend and exposes the WebSocket endpoint that carries
quantum results out to the browser. This layer replaces the serial/Arduino
transport used in the Stage 1 prototype: Python computes a quantum result,
sends it outward, the receiver acts on it. The serial port becomes a WebSocket.
"""

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from quantum_engine import QuantumEngine

app = FastAPI(title="Quantum Swarm Simulation")

engine = QuantumEngine()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_FILE = os.path.join(PROJECT_ROOT, "frontend", "index.html")

# Every circuit is run with the engine's default shot count (256), reduced from the
# Stage 1 prototype's 1024 for faster feedback in the browser.
TOTAL_SHOTS = QuantumEngine.DEFAULT_SHOTS

MIN_ROBOTS = 4
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


def validate_gate(value):
    return value if value in VALID_GATES else 'h'


class SessionState:
    """Per-connection simulation state, so 'measure' knows what was simulated."""

    def __init__(self):
        self.gate = 'h'
        self.noise_rate = 0.1
        self.num_robots = MIN_ROBOTS
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
    state.mode = 'superposition'

    # Each robot is its own qubit, so each gets its own circuit run.
    robots = []
    for robot_id in range(state.num_robots):
        prob = engine.simulate(state.gate, TOTAL_SHOTS, state.noise_rate)
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

    robots = []
    fidelities = []

    for robot_id in range(state.num_robots):
        prob = engine.simulate(state.gate, TOTAL_SHOTS, state.noise_rate)
        angle = int(prob * 180)
        prob_error, angle_error = engine.calculate_error(state.gate, prob, angle)
        fidelity = engine.calculate_fidelity(prob_error)
        fidelities.append(fidelity)

        robots.append({
            "id": robot_id,
            "angle": angle,
            "prob": prob,
            "error": angle_error,
        })

        engine.log_to_csv(
            prob=prob,
            gate_name=state.gate,
            angle=angle,
            prob_error=prob_error,
            angle_error=angle_error,
            noise_rate=state.noise_rate,
            num_robots=state.num_robots,
            mode=state.mode,
            fidelity=fidelity,
            knowledge_level=state.knowledge_level,
        )

    swarm_fidelity = sum(fidelities) / len(fidelities) if fidelities else 0.0

    await websocket.send_json({
        "type": "measurement_result",
        "robots": robots,
        "fidelity": swarm_fidelity,
        "gate": state.gate,
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
