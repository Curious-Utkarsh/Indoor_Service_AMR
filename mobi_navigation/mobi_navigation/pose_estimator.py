#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import tf_transformations
    
    
class PoseNode(Node): 
    def __init__(self):
        super().__init__("pose_estimator_node") 
        self.nav = BasicNavigator()
        self.set_and_follow_goal()

    def create_pose_stamped(self, x, y, yaw):
        q_x, q_y, q_z, q_w = tf_transformations.quaternion_from_euler(0.0, 0.0, yaw)
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.nav.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.position.z = 0.0
        goal_pose.pose.orientation.x = q_x
        goal_pose.pose.orientation.y = q_y
        goal_pose.pose.orientation.z = q_z
        goal_pose.pose.orientation.w = q_w
        return goal_pose
        
    def set_and_follow_goal(self):
        # Set Initial Pose/ Starting Point on Map (2D Pose Estimator)
        initial_pose = self.create_pose_stamped(0.0, 0.0, 0.0)
        self.nav.setInitialPose(initial_pose)
    
def main(args=None):
    rclpy.init(args=args)
    node = PoseNode() 
    rclpy.spin_once(node)
    rclpy.shutdown()
    
if __name__ == "__main__":
    main()

