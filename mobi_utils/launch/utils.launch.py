from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mobi_utils',
            executable='lidar_testing.py',
            name='lidar_testing',
            output='screen',
        ),

        Node(
            package='mobi_utils',
            executable='ultrasonic.py',
            name='ultrasonic',
            output='screen',
        ),

        # Node(
        #     package='mobi_utils',
        #     executable='safety_stop.py',
        #     name='safety_stop',
        #     output='screen',
        # )
    ])
