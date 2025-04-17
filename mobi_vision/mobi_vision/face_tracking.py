#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

import cv2
import mediapipe as mp
import numpy as np


class VisionBasedNeckControl(Node):
    def __init__(self):
        super().__init__('vision_neck_control')
        self.publisher_ = self.create_publisher(JointTrajectory, 'neck_controller/joint_trajectory', 10)
        self.get_logger().info('Vision-Based Neck Control Node started')

        self.timer = self.create_timer(0.1, self.timer_callback)  # 10Hz
        self.cap = cv2.VideoCapture(0)

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.mp_drawing = mp.solutions.drawing_utils

    def timer_callback(self):
        success, frame = self.cap.read()
        if not success:
            self.get_logger().warn('Failed to capture frame')
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]

            # 3D landmark points
            image_points = []
            model_points = []

            # Nose tip, Chin, Left eye, Right eye, Left mouth, Right mouth
            landmark_ids = [1, 152, 263, 33, 287, 57]
            for idx in landmark_ids:
                lm = face_landmarks.landmark[idx]
                h, w, _ = frame.shape
                x, y = int(lm.x * w), int(lm.y * h)
                image_points.append((x, y))
                model_points.append(np.array([x, y, 0.0]))

            image_points = np.array(image_points, dtype='double')
            model_points = np.array([
                [0.0, 0.0, 0.0],      # Nose tip
                [0.0, -330.0, -65.0], # Chin
                [-225.0, 170.0, -135.0], # Left eye
                [225.0, 170.0, -135.0],  # Right eye
                [-150.0, -150.0, -125.0], # Left mouth
                [150.0, -150.0, -125.0]   # Right mouth
            ])

            # Camera parameters
            focal_length = frame.shape[1]
            center = (frame.shape[1] / 2, frame.shape[0] / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype='double')

            dist_coeffs = np.zeros((4, 1))  # No lens distortion

            # Solve PnP
            success, rotation_vector, _ = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs
            )

            if not success:
                self.get_logger().warn('solvePnP failed')
                return

            # Rotation matrix
            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

            # Euler angles
            pitch, yaw, _ = self.rotationMatrixToEulerAngles(rotation_matrix)

            # Remapping:
            # joint_2 → yaw (turn head left/right) = -1.0 to 1.0
            # joint_3 → pitch (up/down) = -0.5 to 0.5
            joint_2 = float(np.clip(yaw, -1.0, 1.0))                      # head turning
            joint_3 = float(np.clip(pitch / 1.3, -0.5, 0.5))              # head nodding

            # Create trajectory message
            traj = JointTrajectory()
            traj.joint_names = ['joint_2', 'joint_3']

            point = JointTrajectoryPoint()
            point.positions = [joint_2, joint_3]
            point.time_from_start.sec = 0
            point.time_from_start.nanosec = int(1e8)
            traj.points.append(point)

            self.publisher_.publish(traj)
            self.get_logger().info(f'joint_2 (yaw): {joint_2:.3f}, joint_3 (pitch): {joint_3:.3f}')

            # Visual feedback
            self.mp_drawing.draw_landmarks(
                frame,
                face_landmarks,
                self.mp_face_mesh.FACEMESH_CONTOURS,
                self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1),
                self.mp_drawing.DrawingSpec(color=(0,0,255), thickness=1)
            )

        else:
            self.get_logger().info('No face detected')

        try:
            cv2.imshow("Head Orientation Tracking", frame)
        except Exception as e:
            self.get_logger().error(f"Error displaying frame: {e}")

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            self.destroy_node()
            rclpy.shutdown()

    def rotationMatrixToEulerAngles(self, R):
        sy = np.sqrt(R[0,0] ** 2 + R[1,0] ** 2)
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2,1], R[2,2])  # pitch
            y = np.arctan2(-R[2,0], sy)     # yaw
            z = np.arctan2(R[1,0], R[0,0])  # roll
        else:
            x = np.arctan2(-R[1,2], R[1,1])
            y = np.arctan2(-R[2,0], sy)
            z = 0

        return x, y, z  # pitch, yaw, roll

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
