# Credit to Gemini for helping me understand the directions to take with this simulating different gates 
# and the results that can be obtained from the simulation, as wel as debugging the code and providing
# suggestions for improving the code and the data analysis.

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
from qiskit_aer.noise import NoiseModel, depolarizing_error

class QuantumRobot:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

        # Ensures the .csv file is created in the same file as this class
        self.csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quantum_tests_data.csv")
        
        # Ideal values for each gate, used while calculating the error
        self.IDEAL_VALUES = {
            'h':  {'prob': 0.5, 'angle': 90},
            'x':  {'prob': 1.0, 'angle': 180},
            'id': {'prob': 0.0, 'angle': 0},
            'sx': {'prob': 0.5, 'angle': 90},
            'y':  {'prob': 1.0, 'angle': 180},
            'z':  {'prob': 0.0, 'angle': 0}
        }

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            print(f"Connected to Arduino via {self.port} >:-->")
            time.sleep(2) # Wait for the connection to initialize
        except Exception as e:
            print(f"Failed to connect to Arduino on {self.port}: {e}")

    def simulate(self, gate_name, total_shots, error_rate):
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

        # Adding noise logic to the simulator
        noise_model = None 

        if (error_rate > 0.0):
            noise_model = NoiseModel()
            dep_error = depolarizing_error(error_rate, 1)  # Depolarizing error for single qubit gates
            noise_model.add_all_qubit_quantum_error(dep_error, [gate_name])  # Add the error to the specified gate
            noise_model.add_all_qubit_quantum_error(dep_error, ['measure'])  # Add the error to measurement


        # Simulate the circuit using AerSimulator
        simulator = AerSimulator()
        job = simulator.run(qc, shots=total_shots, noise_model=noise_model)
        result = job.result()
        counts = result.get_counts()

        num_ones = counts.get('1',0)
        probability = num_ones/total_shots
        return probability
    
    def convert_state_to_angle_for_arduino(self, gate_name, sleep_time, total_shots, error_rate):
        # Getting the probability of the state from the function simulate()
        prob = self.simulate(gate_name, total_shots, error_rate) 
        print(prob)
        
        angle = int(prob*180)
        print(angle)

        # Sending the angle to the Arduino
        if self.ser is not None:
            try:
                self.ser.write(f"{angle}\n".encode())  # Send angle followed by newline
                print(f"Sent angle {angle} to Arduino")
            except Exception as e:
                print(f"Failed to send data to Arduino: {e}")
        else:
            print("Serial connection not established. Cannot send data to Arduino.")
        
        time.sleep(sleep_time) # Wait for the Arduino to process the data and move the servo
        return prob, angle, sleep_time, gate_name
    
    def calculate_error(self, gate_name, prob, angle):
        ideal_prob = self.IDEAL_VALUES[gate_name]['prob']
        ideal_angle = self.IDEAL_VALUES[gate_name]['angle']

        prob_error = abs(prob - ideal_prob)
        angle_error = abs(angle - ideal_angle)

        return prob_error, angle_error

    def log_to_csv(self, prob, gate_name, angle, sleep_duration, prob_error, angle_error, noise_rate):
        write_header = not os.path.exists(self.csv_file) or os.stat(self.csv_file).st_size == 0

        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(['Timestamp', 'Gate Name', 'Probability', 'Angle', 'Sleep Duration', 'Probability Error', 'Angle Error', 'Noise Rate'])
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, gate_name, prob, angle, sleep_duration, prob_error, angle_error, noise_rate])
        
        # Printing the logged data to the console for verification purposes
        print(f"Logged: {gate_name} | Error: {angle_error} deg")
    
    def disconnect(self):
        if self.ser is not None:
            self.ser.close()
            print("Serial connection closed <:--<")
    
if __name__ == "__main__":
    

    servo = QuantumRobot(port='/dev/cu.usbmodem1301')  
    servo.connect()

    try:
        main_gate_name = 'sx' # Change this to test different gates
        main_sleep_time = 1.5 # Time to wait after sending data to Arduino, in seconds
        current_noise_rate = 1.0 # Adjust this value to simulate different levels of noise (0.0 for no noise, up to 1.0 for maximum noise)

        # Run the simulation and send data to Arduino 20 times
        for i in range(20):
            # Ideal simulation and error calculation for the current gate 
            ideal_current_probability, ideal_current_angle, ideal_current_sleep_duration, ideal_current_gate_name = servo.convert_state_to_angle_for_arduino(main_gate_name, main_sleep_time, 1024, 0.0)
            prob_error, angle_error = servo.calculate_error(main_gate_name, ideal_current_probability, ideal_current_angle)
            servo.log_to_csv(ideal_current_probability, ideal_current_gate_name, ideal_current_angle, ideal_current_sleep_duration, prob_error, angle_error, 0.0)

            # Noisy simulation and error calculation for the current gate
            noisy_current_probability, noisy_current_angle, noisy_current_sleep_duration, noisy_current_gate_name = servo.convert_state_to_angle_for_arduino(main_gate_name, main_sleep_time, 1024, current_noise_rate) # Introducing noise in the simulation
            prob_error, angle_error = servo.calculate_error(main_gate_name, noisy_current_probability, noisy_current_angle)
            print(f"Noisy simulation probability for {main_gate_name}: {noisy_current_probability} | Angle: {noisy_current_angle} | Error: {angle_error} deg | Expected Angle: {servo.IDEAL_VALUES[main_gate_name]['angle']} deg | Expected Probability: {servo.IDEAL_VALUES[main_gate_name]['prob']}")
            servo.log_to_csv(noisy_current_probability, noisy_current_gate_name, noisy_current_angle, noisy_current_sleep_duration, prob_error, angle_error, current_noise_rate)

    except Exception as e:
        print(f"Simulation yielded an exception: {e}")
    finally:
        servo.disconnect()