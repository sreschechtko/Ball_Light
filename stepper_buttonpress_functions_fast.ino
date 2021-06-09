#include <SpeedyStepper.h>

// also intialize an enable pin...
const int MOTOR_STEP_PIN = 2;
const int MOTOR_DIRECTION_PIN = 4;
const int LIMIT_SWITCH_PIN = 7;


SpeedyStepper stepper;


void setup() {
  // put your setup code here, to run once:
  pinMode(6, OUTPUT); //This is the enable pin
  pinMode(8, OUTPUT); //This is the TTL trigger pin
  pinMode(10, OUTPUT); //This is the light for the stick
  pinMode(11, OUTPUT); //This is the center light
  pinMode(12, OUTPUT); //This is right light
  pinMode(9, OUTPUT); //This is the left light
  pinMode(LIMIT_SWITCH_PIN, INPUT); //the homing switch
  pinMode(5, OUTPUT); //This is the speaker
  digitalWrite(6, HIGH); //Enable set to ON
  digitalWrite(8, LOW); //Tigger set to LOW
  Serial.begin(115200);
  stepper.connectToPins(MOTOR_STEP_PIN, MOTOR_DIRECTION_PIN);
  stepper.setSpeedInStepsPerSecond(40000);
  stepper.setAccelerationInStepsPerSecondPerSecond(120000);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0) {
    char incomingCharacter = Serial.read();
    switch (incomingCharacter) {
      case 'a': //this is the leftward (CCW) case
        movestepper(42); //42 is 15 degrees
        break;
      case 'b': //this is the rightward (CW) case
        movestepper(-42);
        break;
      case 'c': //this is the no movement case
        movestepper(0);
        break;
      case 'h':
        digitalWrite(6, HIGH); //Enable set to ON
        stepper.setSpeedInStepsPerSecond(200); //low speed for return move
        stepper.setAccelerationInStepsPerSecondPerSecond(200); //low speed for return move
        homestepper(129);
        break;
        
      case 'o': // turn off motor
        stepper.setSpeedInStepsPerSecond(200); //low speed for return move
        stepper.setAccelerationInStepsPerSecondPerSecond(200); //low speed for return move 
        homestepper(300);
        digitalWrite(6, LOW); //Enable set to OFF
        digitalWrite(10,LOW); //Turn off stick light
        break;

      case 'r': // 
        movelight(12);
        break;
        
      case 'l': // 
        movelight(9);
        break;
        
      case 'm': // 
        movelight(11);
        break;

      case 'n': //
        makenoise(440);
        break;
        
    }
  }
}

void movestepper(int steps){
  Serial.println("Received input, waiting to move");
  digitalWrite(10, HIGH); //turn on light on the stick
  tone(5,440,100);
  while (analogRead(A0) < 300) {}
  delay(20); //debounce
  //Serial.println(analogRead(A0));
  Serial.println("Button Activated");
  while (analogRead(A0) > 1000) {}
  //Serial.println(analogRead(A0));
  delay(30); //delay before motor moves
  digitalWrite(8,HIGH); //move trigger ON
  Serial.println("moved");
  stepper.moveRelativeInSteps(steps);
  delay(220);
  tone(5,440,100);
  delay(200);
  tone(5,440,100);
  delay(500);
  digitalWrite(8,LOW); //move trigger OFF
  digitalWrite(10, LOW); //turn on light on the stick
  stepper.setSpeedInStepsPerSecond(200); //low speed for return move
  stepper.setAccelerationInStepsPerSecondPerSecond(400); //low speed for return move
  stepper.moveRelativeInSteps(-1*steps);
  stepper.setSpeedInStepsPerSecond(40000); //high speed for next move
  stepper.setAccelerationInStepsPerSecondPerSecond(120000); //high speed for next move
  
}

void movelight(int dir){
  Serial.println("Received input, waiting to move");
  digitalWrite(11,HIGH); //Turn on center light
  tone(5,440,100);
  while (analogRead(A0) < 300) {} // 
  delay(20); //debounce
  //Serial.println(analogRead(A0));
  Serial.println("Button Activated");
  while (analogRead(A0) > 1000) {}
  //Serial.println(analogRead(A0));
  delay(30);
  digitalWrite(8,HIGH); //move trigger ON
  Serial.println("moved");
  digitalWrite(11,LOW); //Turn off center light
  digitalWrite(dir,HIGH); //Turn on move light
  delay(270);
  tone(5,440,100);
  delay(200);
  tone(5,440,100);
  delay(700);
  digitalWrite(8,LOW); //move trigger OFF
  digitalWrite(dir, LOW); //turn off light
  
}

void homestepper(int center){
  Serial.println("Homing Sequence Started");
  const float homingSpeedInStepsPerSec = -200;
  const float maxHomingDistanceInSteps = 2000;   // max distance to move for homing
  const int directionTowardHome = -1;        // direction to move toward limit switch: 1 goes positive direction, -1 backward

  stepper.moveToHomeInSteps(directionTowardHome, homingSpeedInStepsPerSec, maxHomingDistanceInSteps, LIMIT_SWITCH_PIN);


  //
  // homing is now complete, the motor is stopped at position 0mm
  //
  delay(500);

  stepper.setSpeedInStepsPerSecond(400);
  stepper.moveRelativeInSteps(center); //need to just tune this to figure out how far from 0
  stepper.setAccelerationInStepsPerSecondPerSecond(120000); //set speed high for next moves
  stepper.setSpeedInStepsPerSecond(40000);


}

void makenoise(int freq){
  Serial.println("Making Noise");
  tone(5, freq, 100);
  delay(200);
  tone(5, freq, 100);
}
