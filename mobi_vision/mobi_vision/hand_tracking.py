#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import cv2
import mediapipe as mp
import numpy as np


class VisionBasedNeckControl(Node):
    def __init__(self):
        super().__init__('vision_rail_control')
        self.publisher_ = self.create_publisher(JointTrajectory, 'rail_controller/joint_trajectory', 10)
        self.get_logger().info('Vision-Based rail Control Node started')

        self.timer = self.create_timer(0.1, self.timer_callback)  # 10Hz
        self.cap = cv2.VideoCapture(0)

        self.mp_hand = mp.solutions.hands
        self.hands = self.mp_hand.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.mp_drawing = mp.solutions.drawing_utils

        # Min and max distance for finger separation (in pixels)
        self.min_distance = 30
        self.max_distance = 240

        # Corresponding joint values for min and max distance
        self.min_value = -0.35
        self.max_value = 0

    def timer_callback(self):
        success, frame = self.cap.read()
        if not success:
            self.get_logger().warn('Failed to capture frame')
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            # Finger landmarks: Thumb (4, 3) and Index Finger (8, 6)
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            index_base = hand_landmarks.landmark[6]

            # 2D coordinates of thumb and index finger tips
            thumb_x, thumb_y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
            index_x, index_y = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])

            # Calculate distance between index finger tip and thumb tip
            finger_distance = np.sqrt((index_x - thumb_x) ** 2 + (index_y - thumb_y) ** 2)

            # Debugging: Print the finger distance
            self.get_logger().info(f'Finger distance: {finger_distance:.2f} px')

            # Only change joint position if the distance is within the range
            if self.min_distance <= finger_distance <= self.max_distance:
                # Normalize the finger distance within the threshold range [min_distance, max_distance]
                normalized_distance = (finger_distance - self.min_distance) / (self.max_distance - self.min_distance)
                
                # Interpolate the normalized distance to the joint value range [min_value, max_value]
                joint_1 = self.min_value + normalized_distance * (self.max_value - self.min_value)

                # Create trajectory message for joint_1
                traj = JointTrajectory()
                traj.joint_names = ['joint_1']

                point = JointTrajectoryPoint()
                point.positions = [joint_1]
                point.time_from_start.sec = 0
                point.time_from_start.nanosec = int(1e8)
                traj.points.append(point)

                # Publish the trajectory to the 'neck_controller/joint_trajectory' topic
                self.publisher_.publish(traj)
                self.get_logger().info(f'joint_1 (up/down): {joint_1:.3f}')
            else:
                self.get_logger().info('Finger distance outside valid range')

            # Draw a yellow line between thumb and index finger
            cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (0, 255, 255), 2)

            # Draw green circles on thumb and index finger
            cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 255, 0), -1)
            cv2.circle(frame, (index_x, index_y), 10, (0, 255, 0), -1)

        else:
            self.get_logger().info('No hand detected')

        try:
            cv2.imshow("Finger Tracking", frame)
        except Exception as e:
            self.get_logger().error(f"Error displaying frame: {e}")

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            self.get_logger().info("Shutting down...")
            self.destroy_node()
            rclpy.shutdown()

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VisionBasedNeckControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Interrupted by user. Shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
