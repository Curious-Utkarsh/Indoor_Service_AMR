#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from mobi_msgs.action import Undock
from std_msgs.msg import Float32
import time
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import qos_profile_sensor_data

class UndockActionServer(Node):
    def __init__(self):
        super().__init__('undock_action_server')

        self.undock_server = ActionServer(
            self,
            Undock,
            'undock',
            self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.ultrasonic_sub = self.create_subscription(Float32, '/obstacle_distance', self.ultrasonic_callback, 10)
        self.imu_sub = self.create_subscription(Imu, '/imu/out', self.imu_callback, qos_profile_sensor_data)

        self.ultrasonic_distance = None
        # ⭐ 1. Set the new threshold as requested
        self.threshold = 0.35
        self.angular_velocity_z = 0.0
        self._cancel_requested = False

        self.get_logger().info("Undock Action Server started.")

    def goal_callback(self, goal_request):
        self.get_logger().info("Undock goal received.")
        self._cancel_requested = False
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Undock cancel requested.")
        self._cancel_requested = True
        return CancelResponse.ACCEPT

    def ultrasonic_callback(self, msg):
        self.ultrasonic_distance = msg.data

    def imu_callback(self, msg):
        self.angular_velocity_z = msg.angular_velocity.z

    def execute_callback(self, goal_handle):
        feedback = Undock.Feedback()
        result = Undock.Result()

        try:
            feedback.step = "Reversing from dock"
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(feedback.step)

            twist = Twist()
            twist.linear.x = -0.1

            # ⭐ 2. This is the main change. We combine waiting and reversing.
            # The loop runs if the distance is unknown (None) OR if it's too close.
            reverse_start = time.time()
            while self.ultrasonic_distance is None or self.ultrasonic_distance <= self.threshold:
                # Log the current state
                if self.ultrasonic_distance is None:
                    self.get_logger().info("Reversing blindly... sensor has no reading.")
                else:
                    self.get_logger().info(f"Reversing... Ultrasonic front = {self.ultrasonic_distance:.2f} m")

                # Timeout check
                if time.time() - reverse_start > 15: # Increased timeout for safety
                    self.get_logger().error("Timeout: Could not reverse to the target distance.")
                    result.success = False
                    result.message = "Reverse action timed out"
                    goal_handle.abort()
                    # Stop the robot before returning
                    self.cmd_pub.publish(Twist())
                    return result

                # Check for cancel requests
                if self._cancel_requested:
                    self.cmd_pub.publish(Twist())
                    goal_handle.canceled()
                    result.success = False
                    result.message = "Undock canceled during reverse"
                    return result

                self.cmd_pub.publish(twist)
                time.sleep(0.1)


            # Stop movement after reversing
            self.get_logger().info("Target distance reached. Stopping reverse motion.")
            self.cmd_pub.publish(Twist())
            time.sleep(1)

            # STEP 3: Rotate (This part remains the same)
            # ... rotation logic ...
            feedback.step = "Rotating 90 degrees from dock"
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(feedback.step)

            twist = Twist()
            twist.angular.z = -0.3 #+ve left rotate -ve right rotate
            
            angle_rotated = 0.0
            prev_time = time.time()
            rotate_start = prev_time

            while angle_rotated < 0.185: #Its 90 degree
                # ...
                self.get_logger().info(f"Angle Rotated = {angle_rotated}")

                if self._cancel_requested:
                    self.cmd_pub.publish(Twist())
                    goal_handle.canceled()
                    result.success = False
                    result.message = "Undock canceled during rotation"
                    return result

                current_time = time.time()
                dt = current_time - prev_time
                angle_rotated += abs(self.angular_velocity_z) * dt
                prev_time = current_time

                self.cmd_pub.publish(twist)
                time.sleep(0.01)

                if current_time - rotate_start > 15:
                    self.get_logger().warn("Rotation timeout reached.")
                    break
            
            # Stop after rotation
            self.cmd_pub.publish(Twist())
            time.sleep(1)
            
            result.success = True
            result.message = "Undocked successfully"
            goal_handle.succeed()
            return result

        except Exception as e:
            self.cmd_pub.publish(Twist())
            result.success = False
            result.message = f"Undock failed: {str(e)}"
            goal_handle.abort()
            return result

def main(args=None):
    rclpy.init(args=args)
    node = UndockActionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
