# hardware.launch
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    serial_port = LaunchConfiguration('serial_port')

    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port to use for RPLIDAR',
    )

    # Pass “is_sim:=False” and “serial_port:=<value>” as flat tokens (no nested lists).
    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                os.path.join(
                    get_package_share_directory("mobi_description"),
                    "urdf",
                    "mobi.urdf.xacro",
                ),
            " is_sim:=false",
            " serial_port:=", serial_port,
            ]
        ),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': robot_description, 'use_sim_time': False},
            os.path.join(
                get_package_share_directory('mobi_controller'),
                'config',
                'mobi_controllers.yaml',
            ),
        ],
        output='screen',
    )

    return LaunchDescription([
        serial_port_arg,
        robot_state_publisher_node,
        controller_manager_node,
    ])
