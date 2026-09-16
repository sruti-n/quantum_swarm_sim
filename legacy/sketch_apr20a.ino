#include <Servo.h>
Servo myServo;
void setup() {
  Serial.begin(115200); // Set the speed to 115200
  myServo.attach(9);    // Connect servo to Pin 9
  myServo.write(90);    // Start at a neutral 90 degrees
}
void loop() {
  // Check if Python has sent any data
  if (Serial.available() > 0) {
    // Read the incoming number until it hits a newline (\n)
    int angle = Serial.parseInt(); 
    // Safety check: only move if the number is valid
    if (angle >= 0 && angle <= 180) {
      myServo.write(angle);
    }
  }
}

