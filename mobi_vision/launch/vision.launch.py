from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mobi_vision',
            executable='camera_publisher',
            name='camera_publisher_node',
            output='screen',
        ),

        Node(
            package='mobi_vision',
            executable='aruco_service_server',
            name='aruco_detector_node',
            output='screen',
        )
    ])
