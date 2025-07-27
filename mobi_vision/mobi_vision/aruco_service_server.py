#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from mobi_msgs.srv import DetectAruco
from sensor_msgs.msg import Image

import cv2
import numpy as np
from cv_bridge import CvBridge


class ArucoPoseService(Node):
    def __init__(self):
        super().__init__('aruco_detector_service')
        self.get_logger().info("Aruco Detector Service (Image Subscriber Mode) Started")

        self.bridge = CvBridge()
        self.latest_frame = None

        # Subscribe to camera topic
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # ArUco setup
        self.cam_mat = np.array([[931.18, 0.0, 640.0],
                                 [0.0, 931.18, 360.0],
                                 [0.0, 0.0, 1.0]])
        self.dist_mat = np.zeros((1, 5))
        self.marker_size = 0.6
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
        self.aruco_params = cv2.aruco.DetectorParameters()

        # ROS2 service
        self.srv = self.create_service(DetectAruco, 'detect_aruco', self.detect_aruco_callback)

    def image_callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge error: {e}")

    def detect_aruco_callback(self, request, response):
        if self.latest_frame is None:
            self.get_logger().warn("No image received yet.")
            return response  # Empty

        gray = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)

        if ids is not None:
            ids = ids.flatten()
            for i in range(len(ids)):
                center_x = int((corners[i][0][0][0] + corners[i][0][2][0]) / 2.0)
                center_y = int((corners[i][0][0][1] + corners[i][0][2][1]) / 2.0)

                response.center_x.append(center_x)
                response.center_y.append(center_y)
                response.ids.append(f"obj_{ids[i]}")
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ArucoPoseService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
