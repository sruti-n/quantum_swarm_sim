#include <Servo.h>

Servo testServo;

void setup() {
  testServo.attach(9);
}

void loop() {
  // 1. STAIRCASE TEST (Precision)
  // Moves in 30-degree "steps" and pauses to check stability.
  for (int angle = 0; angle <= 180; angle += 30) {
    testServo.write(angle);
    delay(500); // Half-second pause at each step
  }

  delay(1000); // Wait at the end

  // 2. THE FLUTTER (Micro-movements)
  // Rapidly oscillates in a tiny 10-degree window.
  for (int i = 0; i < 10; i++) {
    testServo.write(85);
    delay(100);
    testServo.write(95);
    delay(100);
  }

  // 3. THE LONG GLIDE (Smoothness)
  // A very slow, cinematic crawl back to zero.
  for (int angle = 180; angle >= 0; angle--) {
    testServo.write(angle);
    delay(30); 
  }

  delay(2000); // Big pause before restarting
}