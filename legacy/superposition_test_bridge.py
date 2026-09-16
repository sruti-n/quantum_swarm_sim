import serial
import time
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# --- CONNECT ---
PORT = '/dev/cu.usbmodem11401' 
ser = serial.Serial(PORT, 115200, timeout=1)
time.sleep(2)

def get_quantum_probability(angle_rad):
    qc = QuantumCircuit(1)
    # We use RY (Rotation around Y-axis) to "tilt" the superposition
    qc.ry(angle_rad, 0) 
    qc.measure_all()
    
    sim = AerSimulator()
    # Run 1024 times to get a solid average
    result = sim.run(qc, shots=1024).result()
    counts = result.get_counts()
    
    # Calculate the probability of '1'
    prob_1 = counts.get('1', 0) / 1024
    return prob_1

try:
    # Test 1: Pure |0> state (No rotation)
    print("Testing State |0>...")
    p = get_quantum_probability(0)
    ser.write(f"{int(p * 180)}\n".encode())
    time.sleep(2)

    # Test 2: Perfect Superposition (Hadamard-like rotation)
    print("Testing Superposition (90 degrees)...")
    p = get_quantum_probability(np.pi / 2) # 90-degree rotation on Bloch Sphere
    ser.write(f"{int(p * 180)}\n".encode())
    time.sleep(2)

    # Test 3: Pure |1> state (180-degree rotation)
    print("Testing State |1>...")
    p = get_quantum_probability(np.pi) 
    ser.write(f"{int(p * 180)}\n".encode())
    time.sleep(2)

    print("Superposition mapping complete!")

except Exception as e:
    print(f"Error: {e}")
finally:
    ser.close()