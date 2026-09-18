# Adapted from quantum_robot_v1.py (Stage 1 prototype) for the Stage 1 simulation.
# The serial/Arduino transport layer has been removed; the WebSocket layer in main.py
# takes its place. All quantum logic below is carried over unchanged.
#
# Original credit note from quantum_robot_v1.py:
# Credit to Gemini for helping me understand the directions to take with this simulating
# different gates and the results that can be obtained from the simulation, as well as
# debugging the code and providing suggestions for improving the code and the data analysis.

import os
import csv
from datetime import datetime

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


class QuantumEngine:
    # 256 shots is statistically sufficient for a pedagogical demo (standard error on
    # P(|1>) is at most ~0.03) and returns results faster than the prototype's 1024.
    DEFAULT_SHOTS = 256

    def __init__(self):
        # The simulation CSV lives in data/ at the project root, one level up from backend/.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_file = os.path.join(project_root, "data", "quantum_swarm_data.csv")

        # Ideal values for each gate, used while calculating the error
        self.IDEAL_VALUES = {
            'h':  {'prob': 0.5, 'angle': 90},
            'x':  {'prob': 1.0, 'angle': 180},
            'id': {'prob': 0.0, 'angle': 0},
            'sx': {'prob': 0.5, 'angle': 90},
            'y':  {'prob': 1.0, 'angle': 180},
            'z':  {'prob': 0.0, 'angle': 0}
        }

    def _build_circuit(self, gate_name):
        # Create and draw a quantum circuit with one qubit and one classical bit for measurement
        qc = QuantumCircuit(1, 1)

        if gate_name == 'h':
            qc.h(0)  # Apply Hadamard gate to create superposition
        elif gate_name == 'x':
            qc.x(0)  # Apply X gate to flip the qubit state
        elif gate_name == 'id':
            pass  # Identity gate does nothing
        elif gate_name == 'sx':
            qc.sx(0)  # Apply square root of X gate
        elif gate_name == 'y':
            qc.y(0)  # Apply Y gate to rotate the qubit state around the Y-axis
        elif gate_name == 'z':
            qc.z(0)  # Apply Z gate to rotate the qubit state around the Z-axis
        else:
            print(f"Unknown gate name: {gate_name}. Defaulting to Hadamard.")
            qc.h(0)  # Apply Hadamard gate to create superposition

        return qc

    def _noise_model(self, gate_name, error_rate):
        # Adding noise logic to the simulator
        if error_rate <= 0.0:
            return None

        noise_model = NoiseModel()
        dep_error = depolarizing_error(error_rate, 1)  # Depolarizing error for single qubit gates
        noise_model.add_all_qubit_quantum_error(dep_error, [gate_name])  # Add the error to the specified gate
        noise_model.add_all_qubit_quantum_error(dep_error, ['measure'])  # Add the error to measurement
        return noise_model

    def simulate(self, gate_name, total_shots=DEFAULT_SHOTS, error_rate=0.0):
        """
        Run the gate over many shots and return P(|1>) — the distribution the
        superposition display is built from, not a single collapsed outcome."""
        qc = self._build_circuit(gate_name)
        qc.measure(0, 0)  # Measure the qubit

        # Simulate the circuit using AerSimulator
        simulator = AerSimulator()
        job = simulator.run(qc, shots=total_shots, noise_model=self._noise_model(gate_name, error_rate))
        result = job.result()
        counts = result.get_counts()

        num_ones = counts.get('1', 0)
        probability = num_ones / total_shots
        return probability

    def measure_once(self, gate_name, error_rate=0.0):
        """
        Collapse the qubit with a single shot and return that one outcome.

        `simulate` averages over many shots to establish the probability
        distribution; a real measurement draws from that distribution exactly
        once. So this runs shots=1 and returns the bit that came back: |0> maps
        to 0 degrees, |1> to 180 degrees. Repeated measurements after an H gate
        therefore land on 0 or 180 at random, which is the physical behaviour.
        """
        qc = self._build_circuit(gate_name)
        qc.measure(0, 0)

        simulator = AerSimulator()
        job = simulator.run(qc, shots=1, noise_model=self._noise_model(gate_name, error_rate))
        counts = job.result().get_counts()

        # A single shot yields exactly one bitstring, either '0' or '1'.
        bit = int(list(counts.keys())[0].replace(" ", ""))

        return {
            'bit': bit,
            'prob': float(bit),
            'angle': bit * 180,
        }

    def simulate_bell_state(self, noise_rate):
        """
        Run a 2-qubit Bell state circuit and return one correlated outcome pair.

        H on qubit 0, then CNOT with qubit 0 controlling qubit 1. Because of the
        Bell state the two measured bits are correlated: |00> or |11> in the
        noiseless case. Qubit 0 drives Robot A, qubit 1 drives Robot B.
        """
        qc = QuantumCircuit(2, 2)
        qc.h(0)         # Put qubit 0 into superposition
        qc.cx(0, 1)     # Entangle qubit 1 with qubit 0
        qc.measure([0, 1], [0, 1])

        # Noise is applied to both qubits via the same depolarizing error model.
        noise_model = None

        if (noise_rate > 0.0):
            noise_model = NoiseModel()
            one_qubit_error = depolarizing_error(noise_rate, 1)
            two_qubit_error = depolarizing_error(noise_rate, 2)
            noise_model.add_all_qubit_quantum_error(one_qubit_error, ['h'])
            noise_model.add_all_qubit_quantum_error(two_qubit_error, ['cx'])
            noise_model.add_all_qubit_quantum_error(one_qubit_error, ['measure'])

        simulator = AerSimulator()
        job = simulator.run(qc, shots=1, noise_model=noise_model)
        result = job.result()
        counts = result.get_counts()

        # A single shot yields a single bitstring, e.g. '01'. Qiskit orders the
        # bitstring with the highest-index qubit first, so reverse it to index by qubit.
        bitstring = list(counts.keys())[0].replace(" ", "")
        bits = bitstring[::-1]

        qubit_0 = int(bits[0])
        qubit_1 = int(bits[1])

        return {
            'qubit_0': qubit_0,
            'qubit_1': qubit_1,
            'angle_0': qubit_0 * 180,
            'angle_1': qubit_1 * 180,
            'correlated': qubit_0 == qubit_1,
        }

    def calculate_error(self, gate_name, prob, angle):
        ideal_prob = self.IDEAL_VALUES[gate_name]['prob']
        ideal_angle = self.IDEAL_VALUES[gate_name]['angle']

        prob_error = abs(prob - ideal_prob)
        angle_error = abs(angle - ideal_angle)

        return prob_error, angle_error

    def calculate_fidelity(self, prob_error):
        """Fidelity reported to the UI: 1.0 means the measured probability matched
        the ideal value exactly. Derived from probability error, not a new circuit."""
        return max(0.0, 1.0 - prob_error)

    # Shots is appended last so the earlier columns keep their Stage 1 positions.
    CSV_HEADER = [
        'Timestamp', 'Gate Name', 'Noise Rate', 'Num Robots', 'Mode',
        'Probability', 'Angle', 'Ideal Angle', 'Probability Error',
        'Angle Error', 'Fidelity', 'Knowledge Level Selected', 'Shots'
    ]

    def _archive_csv_if_old_format(self):
        """A CSV written before a column was added has a different header. Appending
        to it would misalign rows, so move it aside and start a fresh file."""
        if not os.path.exists(self.csv_file) or os.stat(self.csv_file).st_size == 0:
            return
        with open(self.csv_file, newline='') as file:
            header = next(csv.reader(file), [])
        if header != self.CSV_HEADER:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            root, ext = os.path.splitext(self.csv_file)
            os.rename(self.csv_file, f"{root}_old_format_{stamp}{ext}")

    def log_to_csv(self, prob, gate_name, angle, prob_error, angle_error, noise_rate,
                   num_robots, mode, fidelity, knowledge_level, shots, ideal_angle=None):
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        self._archive_csv_if_old_format()
        write_header = not os.path.exists(self.csv_file) or os.stat(self.csv_file).st_size == 0

        # Bell pair rows pass the partner's angle as the ideal; gate rows use the gate's ideal.
        if ideal_angle is None:
            ideal_angle = self.IDEAL_VALUES[gate_name]['angle']

        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(self.CSV_HEADER)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                timestamp, gate_name, noise_rate, num_robots, mode,
                prob, angle, ideal_angle, prob_error,
                angle_error, fidelity, knowledge_level, shots
            ])

        # Printing the logged data to the console for verification purposes
        print(f"Logged: {gate_name} | Error: {angle_error} deg | Fidelity: {fidelity:.3f}")
