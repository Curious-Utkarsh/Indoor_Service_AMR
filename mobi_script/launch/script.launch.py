from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mobi_script',
            executable='task_handler',
            name='task_handler_node',
            output='screen',
        ),

        Node(
            package='mobi_script',
            executable='undock_action_server',
            name='undock_action_node',
            output='screen',
        )

    ])
