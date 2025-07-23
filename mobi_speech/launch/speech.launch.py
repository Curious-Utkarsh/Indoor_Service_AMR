from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mobi_speech',
            executable='voice_llm_node',
            name='voice_llm_node',
            output='screen',
        )
    ])
