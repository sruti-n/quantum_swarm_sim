import serial
import time

# --- CONFIGURATION ---
# Your Mac port from earlier. 
# Double-check this in Arduino IDE > Tools > Port if it fails!
PORT = '/dev/cu.usbmodem11401' 
BAUD = 115200

try:
    # 1. Open the connection
    print(f"Connecting to Arduino on {PORT}...")
    ser = serial.Serial(PORT, BAUD, timeout=1)
    
    # 2. The "Wake Up" Wait
    # Arduinos auto-reset when the serial port opens. 
    # If you send data too fast, the Arduino is still "booting" and misses it.
    time.sleep(2) 
    print("Arduino is awake!")

    # 3. The Test Loop
    angles = [0, 90, 180, 90, 0]
    for a in angles:
        print(f"Commanding Servo to: {a} degrees")
        # We convert the int to a string, add a newline, and encode to bytes
        message = f"{a}\n".encode('utf-8')
        ser.write(message)
        
        time.sleep(1.5) # Wait for the physical arm to move

    print("Test complete! Great job.")
    ser.close()

except serial.SerialException as e:
    print(f"ERROR: Could not open port {PORT}.")
    print("Is the Arduino plugged in? Is the Serial Monitor in the Arduino IDE closed?")
except Exception as e:
    print(f"An unexpected error occurred: {e}")