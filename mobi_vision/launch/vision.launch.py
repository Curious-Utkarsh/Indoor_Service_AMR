from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mobi_vision',
            executable='face_tracking',
            name='face_tracking_node',
            output='screen',
            parameters=[],
        )
    ])
