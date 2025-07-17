#include <PID_v1.h>
// Motor Driver Pins
#define LEFT_MOTOR_PWM_PIN 0
#define LEFT_MOTOR_DIR_PIN 1
#define RIGHT_MOTOR_PWM_PIN 4
#define RIGHT_MOTOR_DIR_PIN 5

// Motor Encoder Pins
#define LEFT_ENCODER_A_PIN 6
#define LEFT_ENCODER_B_PIN 7
#define RIGHT_ENCODER_A_PIN 8
#define RIGHT_ENCODER_B_PIN 9

#define MOTOR_PWM_MAX 200 //Can set to 150 (136 to be precise) to meet your controller set speed in controllers.yaml

#define ENCODER_CPR_LEFT  80000 
#define ENCODER_CPR_RIGHT 80000 

#define TWO_PI 6.28318530718

void leftEncoderISR();
void rightEncoderISR();

unsigned volatile long leftEncoderCount = 0;
unsigned volatile long rightEncoderCount = 0;
String right_wheel_sign = "p";  // 'p' = positive, 'n' = negative
String left_wheel_sign = "p";  // 'p' = positive, 'n' = negative
unsigned long last_millis = 0;
const unsigned long interval = 10; //100 Hz


bool is_right_wheel_cmd = false;
bool is_left_wheel_cmd = false;
bool is_right_wheel_forward = true;
bool is_left_wheel_forward = true;
char value[] = "00.00";
uint8_t value_idx = 0;
bool is_cmd_complete = false;


// PID
// Setpoint - Desired
double right_wheel_cmd_vel = 0.0;     // rad/s
double left_wheel_cmd_vel = 0.0;      // rad/s
// Input - Measurement
double right_wheel_meas_vel = 0.0;    // rad/s
double left_wheel_meas_vel = 0.0;     // rad/s
// Output - Command
double right_wheel_cmd = 0.0;             // 0-255 (PWM)
double left_wheel_cmd = 0.0;              // 0-255 (PWM)
// Tuning
double Kp_r = 12.0;
double Ki_r = 8.0;
double Kd_r = 0.1;
double Kp_l = 12.0;
double Ki_l = 8.0;
double Kd_l = 0.1;
// Controller
PID rightMotor(&right_wheel_meas_vel, &right_wheel_cmd, &right_wheel_cmd_vel, Kp_r, Ki_r, Kd_r, DIRECT);
PID leftMotor(&left_wheel_meas_vel, &left_wheel_cmd, &left_wheel_cmd_vel, Kp_l, Ki_l, Kd_l, DIRECT);

void setup() 
{
  pinMode(LEFT_MOTOR_DIR_PIN,  OUTPUT);
  pinMode(LEFT_MOTOR_PWM_PIN,  OUTPUT);
  pinMode(RIGHT_MOTOR_DIR_PIN, OUTPUT);
  pinMode(RIGHT_MOTOR_PWM_PIN, OUTPUT);

  pinMode(LEFT_ENCODER_A_PIN,  INPUT_PULLUP);
  pinMode(LEFT_ENCODER_B_PIN,  INPUT_PULLUP);
  pinMode(RIGHT_ENCODER_A_PIN, INPUT_PULLUP);
  pinMode(RIGHT_ENCODER_B_PIN, INPUT_PULLUP);

  rightMotor.SetMode(AUTOMATIC);
  leftMotor.SetMode(AUTOMATIC);

  attachInterrupt(digitalPinToInterrupt(LEFT_ENCODER_A_PIN), leftEncoderISR, RISING);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENCODER_A_PIN), rightEncoderISR, RISING);

  Serial.begin(500000);
}

void loop() 
{  
  // Read and Interpret Wheel Velocity Commands
  if (Serial.available())
  {
    char chr = Serial.read();
    // Right Wheel Motor
    if(chr == 'r')
    {
      is_right_wheel_cmd = true;
      is_left_wheel_cmd = false;
      value_idx = 0;
      is_cmd_complete = false;
    }
    // Left Wheel Motor
    else if(chr == 'l')
    {
      is_right_wheel_cmd = false;
      is_left_wheel_cmd = true;
      value_idx = 0;
    }
    // Positive direction
    else if(chr == 'p')
    {
      if(is_right_wheel_cmd && !is_right_wheel_forward)
      {
        // change the direction of the rotation
        digitalWrite(RIGHT_MOTOR_DIR_PIN, HIGH - digitalRead(RIGHT_MOTOR_DIR_PIN));
        is_right_wheel_forward = true;
      }
      else if(is_left_wheel_cmd && !is_left_wheel_forward)
      {
        // change the direction of the rotation
        digitalWrite(LEFT_MOTOR_DIR_PIN, HIGH - digitalRead(LEFT_MOTOR_DIR_PIN));
        is_left_wheel_forward = true;
      }
    }
    // Negative direction
    else if(chr == 'n')
    {
      if(is_right_wheel_cmd && is_right_wheel_forward)
      {
        // change the direction of the rotation
        digitalWrite(RIGHT_MOTOR_DIR_PIN, HIGH - digitalRead(RIGHT_MOTOR_DIR_PIN));
        is_right_wheel_forward = false;
      }
      else if(is_left_wheel_cmd && is_left_wheel_forward)
      {
        // change the direction of the rotation
        digitalWrite(LEFT_MOTOR_DIR_PIN, HIGH - digitalRead(LEFT_MOTOR_DIR_PIN));
        is_left_wheel_forward = false;
      }
    }
    // Separator
    else if(chr == ',')
    {
      if(is_right_wheel_cmd)
      {
        right_wheel_cmd_vel = atof(value);
      }
      else if(is_left_wheel_cmd)
      {
        left_wheel_cmd_vel = atof(value);
        is_cmd_complete = true;
      }
      // Reset for next command
      value_idx = 0;
      value[0] = '0';
      value[1] = '0';
      value[2] = '.';
      value[3] = '0';
      value[4] = '0';
      value[5] = '\0';
    }
    // Command Value
    else
    {
      if(value_idx < 5)
      {
        value[value_idx] = chr;
        value_idx++;
      }
    }
  }

    // Encoder
  unsigned long current_millis = millis();
  unsigned long delta_millis = current_millis - last_millis;
  if(delta_millis >= interval) //20Hz (50 ms)
  {
    double delta_t = delta_millis / 1000.0;  // Convert to seconds

    right_wheel_meas_vel = (rightEncoderCount * TWO_PI) / (ENCODER_CPR_RIGHT * delta_t);
    left_wheel_meas_vel  = (leftEncoderCount  * TWO_PI) / (ENCODER_CPR_LEFT  * delta_t);

    rightMotor.Compute();
    leftMotor.Compute();

    // Ignore commands smaller than inertia
    if(right_wheel_cmd_vel == 0.0)
    {
      right_wheel_cmd = 0.0;
    }
    if(left_wheel_cmd_vel == 0.0)
    {
      left_wheel_cmd = 0.0;
    }

    String encoder_read = "r" + right_wheel_sign + String(right_wheel_meas_vel) + ",l" + left_wheel_sign + String(left_wheel_meas_vel) + ",";
    Serial.println(encoder_read);
    last_millis = current_millis;
    rightEncoderCount = 0;
    leftEncoderCount = 0;

    // Constrain motor commands to valid PWM range
    left_wheel_cmd = constrain(left_wheel_cmd, 0, MOTOR_PWM_MAX);
    right_wheel_cmd = constrain(right_wheel_cmd, 0, MOTOR_PWM_MAX);

    analogWrite(LEFT_MOTOR_PWM_PIN, left_wheel_cmd);
    analogWrite(RIGHT_MOTOR_PWM_PIN, right_wheel_cmd);
  }
}

void leftEncoderISR() 
{
  leftEncoderCount++;
  if (digitalRead(LEFT_ENCODER_A_PIN) == digitalRead(LEFT_ENCODER_B_PIN)) 
  {
    left_wheel_sign = "p";
  }
  else
  {
    left_wheel_sign = "n";
  }
}

void rightEncoderISR() 
{
  rightEncoderCount++;
  if (digitalRead(RIGHT_ENCODER_A_PIN) == digitalRead(RIGHT_ENCODER_B_PIN)) 
  {
    right_wheel_sign = "n";
  }
  else
  {
    right_wheel_sign = "p";
  }
}

