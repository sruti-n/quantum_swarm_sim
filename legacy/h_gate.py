import os
import csv
import qiskit
from qiskit import QuantumCircuit
from qiskit.result.distributions import probability
from qiskit_aer import AerSimulator
import serial 
import time
import numpy as np
from datetime import datetime

# Initialize the serial connection to the Arduino
PORT = '/dev/cu.usbmodem11301'

# Credit to Gemini for providing me with the ideal probabilities and angles for each gate, used to calculate the angle the servo needs to turned
# Dictionary to store the "Theoretical" outcome of each gate
# This is used to calculate the Error/Difference
IDEAL_VALUES = {
    'h':  {'prob': 0.5, 'angle': 90},
    'x':  {'prob': 1.0, 'angle': 180},
    'id': {'prob': 0.0, 'angle': 0},
    'sx': {'prob': 0.5, 'angle': 90},
    'y':  {'prob': 1.0, 'angle': 180},
    'z':  {'prob': 0.0, 'angle': 0}
}

try:
    ser_arduino = serial.Serial(PORT, baudrate=115200, timeout=1)
    print(f"Connected to Arduino via {PORT}")
    time.sleep(2) # Wait for the connection to initialize
except:
    print(f"Failed to connect to Arduino on {PORT}")

# Create a quantum circuit with one qubit and one classical bit for measurement, 
# and simulate after applying a Hadamard gate
def simulate_quantum_circuit(gate_name):
    # Create and draw a quantum circuit with one qubit and one classical bit for measurement
    qc = QuantumCircuit(1,1)

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
    
    measurement_dict = qc.measure(0,0) # Measure the qubit

    # Simulate the circuit using AerSimulator
    simulator = AerSimulator()
    job = simulator.run(qc, shots=1024)
    result = job.result()
    counts = result.get_counts()

    num_ones = counts.get('1',0)
    total_shots = 1024
    probability = num_ones/total_shots
    return probability

def convert_state_to_angle_for_arduino(gate_name, sleep_time):
    # Getting the probability of the state from the function simulate_quantum_circuit()
    prob = simulate_quantum_circuit(gate_name) 
    print(prob)
    
    angle = int(prob*180)
    print(angle)

    # Sending the angle to the Arduino
    ser_arduino.write(f"{angle}\n".encode())
    time.sleep(sleep_time) # Wait for the Arduino to process the data and move the servo

    return prob, angle, sleep_time, gate_name

# Credit to Gemini for providing me with the code to log data to a CSV file, which I adapted to saving the data run through these simulations. 
def log_to_csv(probability, gate_name, angle, sleep_duration, prob_error, angle_error): 
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'quantum_tests_data.csv')
    
    write_header = not os.path.exists(file_path) or os.stat(file_path).st_size == 0
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(['Timestamp', 'Gate Name', 'Probability', 'Angle', 'Sleep Duration', 'Prob_Error', 'Angle_Error'])
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, gate_name, probability, angle, sleep_duration, prob_error, angle_error])
        
    print(f"Logged: {gate_name} | Error: {angle_error} deg")

try:
    main_gate_name = 'x' # Change this to test different gates
    main_sleep_time = 1.5 # Time to wait after sending data to Arduino, in seconds

    # Run the simulation and send data to Arduino 20 times
    for i in range(20): 
        current_gate = simulate_quantum_circuit(main_gate_name)
        current_probability, current_angle, current_sleep_duration, current_gate_name = convert_state_to_angle_for_arduino(main_gate_name,main_sleep_time)

        probability_error = abs(current_probability-IDEAL_VALUES[main_gate_name]['prob'])
        angle_error = abs(current_angle-IDEAL_VALUES[main_gate_name]['angle'])

        log_to_csv(current_probability, current_gate_name, current_angle, current_sleep_duration, probability_error, angle_error)

except Exception as e:
    print(f"Simulation yielded an exception {e}")
finally: 
    if "ser_arduino" in locals() or "ser_arduino" in globals():
        ser_arduino.close()
        print("Serial connection closed")