import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped, Twist, TransformStamped
import tf_transformations
from sensor_msgs.msg import Image, LaserScan, Imu
from cv_bridge import CvBridge
import cv2
import numpy as np
import math
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from tf2_ros import TransformException
from tf2_ros import TransformBroadcaster
from std_msgs.msg import Int64

class BotNavNode(Node):
    def __init__(self):
        super().__init__("bot_nav_node")

        self.nav = BasicNavigator()
        self.tf_buffer = Buffer(cache_time=rclpy.time.Duration(seconds=10.0))
        self.listener = TransformListener(self.tf_buffer, self)
        self.br = TransformBroadcaster(self)
        self.bridge = CvBridge()
        self.frame = None
        self.front_ray = 0.0
        self.left_ray = 0.0
        self.right_ray = 0.0
        self.trans_x = 0.0
        self.yaw = 0.0
        self.is_docking = False
        self.is_align = False
        self.flag = False

        self.velocity_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.sub_camera = self.create_subscription(Image, "/camera/image_raw", self.cameraCallback, 10)
        self.sub_lidar = self.create_subscription(LaserScan, "/scan", self.lidarCallback, 10)
        self.sub_imu = self.create_subscription(Imu, "/imu", self.imuCallback, 10)
        self.battery_sub = self.create_subscription(Int64, "/battery", self.batteryCallback, 10)

        self.set_and_follow_goal(3.0, -0.8, 0.0)

    # Create PoseStamped for navigation
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

    # Navigate to a predefined waypoint
    def set_and_follow_goal(self, x, y, yaw):
        self.nav.waitUntilNav2Active()
        P1 = self.create_pose_stamped(x, y, yaw)

        waypoint = [P1]
        self.nav.followWaypoints(waypoint)

        while not self.nav.isTaskComplete():
            feedback = self.nav.getFeedback()
            print(feedback)

        print(self.nav.getResult())

    # Camera callback for ArUco detection
    def cameraCallback(self, img):
        self.frame = self.bridge.imgmsg_to_cv2(img, 'bgr8')
        if self.frame is not None:
            center_aruco_list, id_list = self.detect_aruco_pose(self.frame)
            for i in range(0, len(id_list)):
                if id_list[i] == 'obj_23': 
                    # Broadcast transform from `camera_link` to ArUco marker
                    t_camera_to_aruco = TransformStamped()
                    t_camera_to_aruco.header.stamp = self.get_clock().now().to_msg()
                    t_camera_to_aruco.header.frame_id = 'camera_link'
                    t_camera_to_aruco.child_frame_id = id_list[i]
                    t_camera_to_aruco.transform.translation.x = float(center_aruco_list[i][0])
                    t_camera_to_aruco.transform.translation.y = float(center_aruco_list[i][1])
                    t_camera_to_aruco.transform.translation.z = 0.0
                    t_camera_to_aruco.transform.rotation.x = 0.0
                    t_camera_to_aruco.transform.rotation.y = 0.0
                    t_camera_to_aruco.transform.rotation.z = 0.0
                    t_camera_to_aruco.transform.rotation.w = 1.0

                    self.br.sendTransform(t_camera_to_aruco)
                    self.trans_x = t_camera_to_aruco.transform.translation.x

                    # # Try to get transform from `map` to ArUco frame for docking control
                    # try:
                    #     t_map_to_aruco = self.tf_buffer.lookup_transform('map', id_list[i], rclpy.time.Time(), rclpy.duration.Duration(seconds=0.1))  # Setting a small tolerance
                    #     self.perform_docking(t_map_to_aruco)
                    # except TransformException as e:
                    #     self.get_logger().warn(f"Transform error: {e}")
                    #     return

                    cv2.circle(self.frame, (920, 540), radius=5, color=(255, 0, 0), thickness=-1)
                    cv2.circle(self.frame, (center_aruco_list[i][0], center_aruco_list[i][1]), radius=7, color=(255, 0, 0), thickness=2)

            if self.is_docking == True:
                self.perform_docking()

            elif self.is_align == True and self.is_docking == False:
                #self.alignLidar()
                self.alignIMU()

        cv2.imshow('Frame', self.frame)
        cv2.waitKey(1)

    # Docking logic based on TF
    def perform_docking(self):
        
        error = 920 - self.trans_x

        distance_threshold = 0.4

        # print("Front ray" + str(self.front_ray)) 

        if self.trans_x == 0.0:
            self.set_and_follow_goal(-4.5, -1.0, -1.57)
            self.flag = True
        else:
            self.flag = False

        if abs(error) > 0.0 or self.flag == True:
            ang = 0.0005 * error  # Adjust angle proportionally
        else:
            ang = 0.0  # Stop angular adjustment

        if self.front_ray > distance_threshold or self.flag == True:
            lin = 0.1  # Move forward
        else:
            lin = 0.0  # Stop linear motion
            ang = 0.0
            self.is_docking = False
            self.flag = False
            error = 0.0
            self.trans_x = 0.0
            self.is_align = True

        if lin == 0.0 and ang == 0.0:
            self.get_logger().info("Docking complete.")
            self.vel_pub(lin, ang)
        else:
            self.vel_pub(lin, ang)

        # print("lin" + str(lin))
        # print("ang" + str(ang))

    # Publish velocity commands
    def vel_pub(self, lin, ang):
        twist = Twist()
        twist.linear.x = lin
        twist.angular.z = ang
        self.velocity_pub.publish(twist)

    # ArUco detection and pose estimation
    def detect_aruco_pose(self, image):
        marker_size = 0.60  
        axis_size = 0.3

        center_aruco_list = []
        id_list = []

        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
        aruco_params = cv2.aruco.DetectorParameters()

        cam_mat = np.array([[931.1829833984375, 0.0, 640.0], [0.0, 931.1829833984375, 360.0], [0.0, 0.0, 1.0]])
        dist_mat = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray_img, aruco_dict, parameters=aruco_params)

        if len(corners) > 0:
            ids = ids.flatten()
            for i in range(len(ids)):
                rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners[i], marker_size, cam_mat, dist_mat)
                cv2.aruco.drawDetectedMarkers(image, corners)
                cv2.drawFrameAxes(image, cam_mat, dist_mat, rvec, tvec, axis_size)

                center_x = int((corners[i][0][0][0] + corners[i][0][2][0]) / 2.0)
                center_y = int((corners[i][0][0][1] + corners[i][0][2][1]) / 2.0)
                center_aruco_list.append((center_x, center_y))
                id_list.append(f'obj_{ids[i]}')

        return center_aruco_list, id_list

    # LIDAR callback for distance tracking
    def lidarCallback(self, scan):
        self.front_ray = min(scan.ranges[1], 100)  
        self.right_ray = min(scan.ranges[350], 100)
        self.left_ray = min(scan.ranges[10], 100)

        # print("Right Ray : " + str(self.right_ray))
        # print("Left Ray : " + str(self.left_ray))
        # print("- - - - - -")
        print("is_docking || is_align: " + str(self.is_docking) + " || " + str(self.is_align))

    def imuCallback(self, imu):
        # Access orientation (quaternion format)
        orientation = imu.orientation
        orientation_x = orientation.x
        orientation_y = orientation.y
        orientation_z = orientation.z
        orientation_w = orientation.w

        r, p, y = tf_transformations.euler_from_quaternion(
            [orientation_x, orientation_y, orientation_z, orientation_w]
        )
        self.yaw = y 

    def batteryCallback(self, status):
        if status.data <= 20 and self.is_docking == False and self.flag == False:
            self.set_and_follow_goal(-0.6, 5.2, -0.1)
            self.is_docking = True
        if status.data > 20:
            self.is_docking = False

    def alignLidar(self):
        error = self.left_ray - self.right_ray
        # print("Error = " + str(error))
        if abs(error) < 0.005: 
            ang = 0.0
            self.is_align = False
        else :
            ang = -0.5*error

        self.vel_pub(0.0, ang)

    def alignIMU(self):
        print("YAW = " + str(self.yaw))
        if abs(self.yaw) < 0.005: 
            ang = 0.0
            self.is_align = False
        else :
            ang = 0.05

        self.vel_pub(0.0, ang)
        

def main(args=None):
    rclpy.init(args=args)
    bot_nav_node = BotNavNode()
    rclpy.spin(bot_nav_node)
    bot_nav_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()