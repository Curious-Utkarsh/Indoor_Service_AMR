#!/usr/bin/env python3
import rclpy.time
import smbus
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from collections import deque  # Added for moving average filter

# MPU6050 Register Addresses
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47
DEVICE_ADDRESS = 0x68


class MPU6050_Driver(Node):

    def __init__(self):
        super().__init__("mpu6050_driver")
        
        # I2C Interface
        self.is_connected_ = False
        self.init_i2c()

        # ROS 2 Interface
        self.imu_pub_ = self.create_publisher(Imu, "/imu/out", qos_profile=qos_profile_sensor_data)
        self.imu_msg_ = Imu()
        self.imu_msg_.header.frame_id = "base_footprint"
        self.frequency_ = 0.01
        self.timer_ = self.create_timer(self.frequency_, self.timerCallback)

        # Moving Average Filter Buffers (window size = 5)
        self.window_size = 5
        self.acc_x_buffer = deque(maxlen=self.window_size)
        self.acc_y_buffer = deque(maxlen=self.window_size)
        self.acc_z_buffer = deque(maxlen=self.window_size)
        self.gyro_x_buffer = deque(maxlen=self.window_size)
        self.gyro_y_buffer = deque(maxlen=self.window_size)
        self.gyro_z_buffer = deque(maxlen=self.window_size)

    def moving_average(self, buffer, new_value):
        buffer.append(new_value)
        return sum(buffer) / len(buffer)

    def timerCallback(self):
        try:
            if not self.is_connected_:
                self.init_i2c()
            
            # Read Accelerometer raw values
            acc_x = self.read_raw_data(ACCEL_XOUT_H)
            acc_y = self.read_raw_data(ACCEL_YOUT_H)
            acc_z = self.read_raw_data(ACCEL_ZOUT_H)
            
            # Read Gyroscope raw values
            gyro_x = self.read_raw_data(GYRO_XOUT_H)
            gyro_y = self.read_raw_data(GYRO_YOUT_H)
            gyro_z = self.read_raw_data(GYRO_ZOUT_H)
            
            # Apply Moving Average Filter
            acc_x_avg = self.moving_average(self.acc_x_buffer, acc_x)
            acc_y_avg = self.moving_average(self.acc_y_buffer, acc_y)
            acc_z_avg = self.moving_average(self.acc_z_buffer, acc_z)
            gyro_x_avg = self.moving_average(self.gyro_x_buffer, gyro_x)
            gyro_y_avg = self.moving_average(self.gyro_y_buffer, gyro_y)
            gyro_z_avg = self.moving_average(self.gyro_z_buffer, gyro_z)
            
            # Convert to proper units and populate message
            self.imu_msg_.linear_acceleration.x = acc_x_avg / 1670.13
            self.imu_msg_.linear_acceleration.y = acc_y_avg / 1670.13
            self.imu_msg_.linear_acceleration.z = acc_z_avg / 1670.13
            self.imu_msg_.angular_velocity.x = gyro_x_avg / 7509.55
            self.imu_msg_.angular_velocity.y = gyro_y_avg / 7509.55
            self.imu_msg_.angular_velocity.z = gyro_z_avg / 7509.55

            self.imu_msg_.header.stamp = self.get_clock().now().to_msg()
            self.imu_pub_.publish(self.imu_msg_)

        except OSError:
            self.is_connected_ = False

    def init_i2c(self):
        try:
            self.bus_ = smbus.SMBus(1)
            self.bus_.write_byte_data(DEVICE_ADDRESS, SMPLRT_DIV, 7)
            self.bus_.write_byte_data(DEVICE_ADDRESS, PWR_MGMT_1, 1)
            self.bus_.write_byte_data(DEVICE_ADDRESS, CONFIG, 0)
            self.bus_.write_byte_data(DEVICE_ADDRESS, GYRO_CONFIG, 24)
            self.bus_.write_byte_data(DEVICE_ADDRESS, INT_ENABLE, 1)
            self.is_connected_ = True
        except OSError:
            self.is_connected_ = False
        
    def read_raw_data(self, addr):
        high = self.bus_.read_byte_data(DEVICE_ADDRESS, addr)
        low = self.bus_.read_byte_data(DEVICE_ADDRESS, addr + 1)
        value = (high << 8) | low
        if value > 32768:
            value -= 65536
        return value


def main():
    rclpy.init()
    mpu6050_driver = MPU6050_Driver()
    rclpy.spin(mpu6050_driver)
    mpu6050_driver.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
