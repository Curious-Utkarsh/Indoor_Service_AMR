#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from visualization_msgs.msg import Marker
import RPi.GPIO as GPIO
import time

# GPIO pin numbers for the ultrasonic sensor (BCM mode)
TRIG_PIN = 4
ECHO_PIN = 17

class DistancePublisher(Node):
    def __init__(self):
        super().__init__('ultrasonic_publisher')

        # Distance publisher
        self.distance_pub = self.create_publisher(Float32, 'obstacle_distance', 10)

        # Marker publisher for RViz2
        self.marker_pub = self.create_publisher(Marker, 'ultrasonic_marker', 10)

        # Timer to publish data at 5Hz
        self.timer = self.create_timer(0.2, self.measure_and_publish_distance)

        # GPIO setup
        self.setup_gpio()

        self.get_logger().info('Ultrasonic Publisher Node started.')
        self.get_logger().info('Publishing distance and visualization marker.')

    def setup_gpio(self):
        try:
            GPIO.setmode(GPIO.BCM)  # BCM pin numbering
            GPIO.setup(TRIG_PIN, GPIO.OUT)
            GPIO.setup(ECHO_PIN, GPIO.IN)
            GPIO.output(TRIG_PIN, False)
            time.sleep(2)  # Sensor settle time
        except Exception as e:
            self.get_logger().error(f'GPIO Setup Error: {e}')
            GPIO.cleanup()
            rclpy.shutdown()

    def measure_and_publish_distance(self):
        try:
            # Trigger ultrasonic pulse
            GPIO.output(TRIG_PIN, True)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(TRIG_PIN, False)

            # Wait for echo to go HIGH
            timeout = time.time() + 1
            while GPIO.input(ECHO_PIN) == 0:
                pulse_start = time.time()
                if pulse_start > timeout:
                    raise TimeoutError("Timeout waiting for ECHO high")

            # Wait for echo to go LOW
            while GPIO.input(ECHO_PIN) == 1:
                pulse_end = time.time()
                if pulse_end > timeout:
                    raise TimeoutError("Timeout waiting for ECHO low")

            # Calculate distance in cm
            pulse_duration = pulse_end - pulse_start
            distance_cm = (pulse_duration * 34300) / 2
            distance_cm = round(distance_cm, 2)

            # Publish Float32 distance
            msg = Float32()
            msg.data = float(distance_cm)
            self.distance_pub.publish(msg)
            self.get_logger().info(f'Distance: {distance_cm:.2f} cm')

            # Publish RViz2 marker
            self.publish_marker(distance_cm)

        except TimeoutError as e:
            self.get_logger().warn(str(e))
        except Exception as e:
            self.get_logger().error(f'Error measuring distance: {e}')

    def publish_marker(self, distance_cm):
        marker = Marker()
        marker.header.frame_id = "base_link"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "ultrasonic"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        # Position marker at measured distance (forward direction)
        marker.pose.position.x = distance_cm / 100.0  # convert to meters
        marker.pose.position.y = 0.0
        marker.pose.position.z = 0.1  # slight lift for visibility

        marker.pose.orientation.w = 1.0

        marker.scale.x = 0.1
        marker.scale.y = 0.1
        marker.scale.z = 0.1

        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 1.0

        self.marker_pub.publish(marker)

    def destroy_node(self):
        self.get_logger().info('Cleaning up GPIO...')
        GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = DistancePublisher()
    except Exception as e:
        print(f"[FATAL] Failed to start node: {e}")
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
