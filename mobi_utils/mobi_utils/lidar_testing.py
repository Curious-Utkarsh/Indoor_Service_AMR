#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
import math
import json


class LidarReader(Node):
    def __init__(self):
        super().__init__('lidar_reader')

        # Subscribe to /scan topic
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        # Publisher to /lidar_angle_data
        self.publisher_ = self.create_publisher(
            String,
            'lidar_angle_data',
            10
        )

    def scan_callback(self, msg: LaserScan):
        angles = {
            '0° (front)': 0,
            '30°': 30,
            '90° (left)': 90,
            '135°': 135,
            '180° (back)': 180,
            '225°': 225,
            '270° (right)': 270,
            '300°': 300
        }

        results = {}
        for label, angle in angles.items():
            distance = self.average_range_near_angle(angle, msg, window=2.0)
            results[label] = distance

        #self.get_logger().info(f"LIDAR Ranges: {results}")

        # Publish to topic as JSON string
        msg_out = String()
        msg_out.data = json.dumps(results)
        self.publisher_.publish(msg_out)

    def average_range_near_angle(self, angle_deg, msg, window=2.0):
        # Normalize angle to [-180, 180]
        angle_deg = (angle_deg + 360) % 360
        if angle_deg > 180:
            angle_deg -= 360
        angle_rad = math.radians(angle_deg)

        window_rad = math.radians(window)
        start_angle = angle_rad - window_rad
        end_angle = angle_rad + window_rad

        start_idx = int((start_angle - msg.angle_min) / msg.angle_increment)
        end_idx = int((end_angle - msg.angle_min) / msg.angle_increment)

        # Clamp indices
        start_idx = max(0, start_idx)
        end_idx = min(len(msg.ranges), end_idx)

        valid_ranges = [
            r for r in msg.ranges[start_idx:end_idx]
            if math.isfinite(r)
        ]

        if valid_ranges:
            return round(sum(valid_ranges) / len(valid_ranges), 2)
        else:
            return None


def main(args=None):
    rclpy.init(args=args)
    node = LidarReader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
