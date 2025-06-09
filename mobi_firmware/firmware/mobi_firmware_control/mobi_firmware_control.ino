#include <PID_v1.h>
// Motor Driver Pins
#define LEFT_MOTOR_DIR_PIN   4
#define LEFT_MOTOR_PWM_PIN   15
#define RIGHT_MOTOR_DIR_PIN  23
#define RIGHT_MOTOR_PWM_PIN  22

// Motor Encoder Pins
#define LEFT_ENCODER_A_PIN   17 
#define LEFT_ENCODER_B_PIN   16  
#define RIGHT_ENCODER_A_PIN  18
#define RIGHT_ENCODER_B_PIN   5

#define MOTOR_SPEED 100 //30RPM at 100 value, donot increase more than 100.

#define ENCODER_CPR_LEFT  159200 //works for 100 Motor Speed
#define ENCODER_CPR_RIGHT 159200 //works for 100 Motor Speed

void IRAM_ATTR leftEncoderISR();
void IRAM_ATTR rightEncoderISR();

unsigned volatile long leftEncoderCount = 0;
unsigned volatile long rightEncoderCount = 0;
String right_wheel_sign = "p";  // 'p' = positive, 'n' = negative
String left_wheel_sign = "p";  // 'p' = positive, 'n' = negative
unsigned long last_millis = 0;
const unsigned long interval = 100;

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
double right_wheel_cmd = 0.0;             // 0-255
double left_wheel_cmd = 0.0;              // 0-255
// Tuning
double Kp_r = 8.0; //10.0
double Ki_r = 7.0;
double Kd_r = 0.1;
double Kp_l = 8.0; //10.0
double Ki_l = 7.0;
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

  pinMode(LEFT_ENCODER_A_PIN,  INPUT);
  pinMode(LEFT_ENCODER_B_PIN,  INPUT);
  pinMode(RIGHT_ENCODER_A_PIN, INPUT);
  pinMode(RIGHT_ENCODER_B_PIN, INPUT);

  rightMotor.SetMode(AUTOMATIC);
  leftMotor.SetMode(AUTOMATIC);

  attachInterrupt(digitalPinToInterrupt(LEFT_ENCODER_A_PIN), leftEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENCODER_A_PIN), rightEncoderISR, CHANGE);

  Serial.begin(115200);
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
    // Left Wheel Mo tor
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
  if(current_millis - last_millis >= interval)
  {
    right_wheel_meas_vel = 10*(rightEncoderCount/2)*(60.0/(270.0*334.0*1.87)) * 0.10472; //Hit and Trial Factor 1.88 done manually
    left_wheel_meas_vel = 10*(leftEncoderCount/2)*(60.0/(270.0*334.0*1.87)) * 0.10472; 

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

    //Serial.println(left_wheel_cmd);
    analogWrite(LEFT_MOTOR_PWM_PIN, left_wheel_cmd);
    analogWrite(RIGHT_MOTOR_PWM_PIN, right_wheel_cmd);
  }
}

void IRAM_ATTR leftEncoderISR() 
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

void IRAM_ATTR rightEncoderISR() 
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

