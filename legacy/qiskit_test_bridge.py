import serial
import time
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# --- 1. THE BRIDGE ---
PORT = '/dev/cu.usbmodem11401' 
try:
    ser = serial.Serial(PORT, 115200, timeout=1)
    time.sleep(2) 
    print("Bridge Online.")
except:
    print("Bridge Offline. Check your USB cable and Serial Monitor.")

# --- 2. THE QUANTUM FUNCTION ---
def run_quantum_logic():
    # Create a circuit: 1 Qubit, 1 Classical bit
    qc = QuantumCircuit(1)
    
    # Rotate the qubit by 1/4 of the way. 
    # This makes it much more likely to stay at 0 than go to 180.
    qc.ry(np.pi/4, 0)
    qc.measure_all()
    
    # Simulate the result
    sim = AerSimulator()
    job = sim.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    # Get the state ('0' or '1')
    state = list(counts.keys())[0]
    return state

# --- 3. THE MAPPING ---
try:
    while True:
        input("Press Enter to collapse the wave function...")
        
        outcome = run_quantum_logic()
        
        # Map Quantum state to Physical angle
        # |0> = 0 degrees, |1> = 180 degrees
        angle = 180 if outcome == '1' else 0
        
        print(f"Quantum Measurement: |{outcome}>")
        print(f"Action: Moving servo to {angle} degrees")
        
        print(f"Resulting State: {outcome}")
        if outcome == '1':
            print("  [##########] 100% Probability of State 1")
        else:
            print("  [----------] 100% Probability of State 0")

        # Send to Arduino
        ser.write(f"{angle}\n".encode())
        
except KeyboardInterrupt:
    print("\nShutting down robot...")
    ser.close()