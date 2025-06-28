import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    use_slam = LaunchConfiguration("use_slam")
    serial_port = LaunchConfiguration("serial_port") #Port For RpLidar, based on this, arduino port is automatically decided in urdf, done.
    map_name = LaunchConfiguration("map_name")

    use_slam_arg = DeclareLaunchArgument(
        "use_slam",
        default_value="false"
    )

    serial_port_arg = DeclareLaunchArgument(
        "serial_port",
        default_value="/dev/ttyUSB0", #By Default Lidar USB 0 kiya hua hai, if doesnot work then give arg as usb1, internal chnages will happen.
        description="Serial port for RPLIDAR"
    )

    map_name_arg = DeclareLaunchArgument(
        "map_name",
        default_value="Room1"
    )


    hardware_interface = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_firmware"),
                "launch",
                "hardware_interface.launch.py"
            )
        ),
        launch_arguments={
            "serial_port": serial_port #Passes serial port to urdf
        }.items()
    )

    laser_driver = Node(
        package="rplidar_ros",
        executable="rplidar_node",
        name="rplidar_node",
        parameters=[{
            "channel_type": "serial",
            "serial_port": serial_port,
            "serial_baudrate": 115200,
            "frame_id": "laser_link",
            "inverted": False,
            "angle_compensate": True,
            "scan_mode": "Sensitivity",
            "range_min": 0.40
        }],
        output="screen"
    )


    controller_only = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mobi_controller"),
            "launch",
            "controller.launch.py"
        ),
    )

    controller_with_slider = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mobi_controller"),
            "launch",
            "slider_controller.launch.py"
        ),
    )

    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_controller"),
                "launch",
                "joystick.launch.py"
            )
        ),
        launch_arguments={"use_sim_time": "False"}.items()
    )

    imu_driver_node = Node(
        package="mobi_firmware",
        executable="mpu6050_driver.py",
        output="screen"
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_localization"),
                "launch",
                "global_localization.launch.py"
            )
        ),
        launch_arguments={
            "use_sim_time": "False",
            "map_name": map_name
        }.items(),
        condition=UnlessCondition(use_slam)
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_mapping"),
                "launch",
                "slam.launch.py"
            )
        ),
        launch_arguments={"use_sim_time": "False"}.items(),
        condition=IfCondition(use_slam)
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_navigation"),
                "launch",
                "navigation.launch.py"
            )
        ),
        launch_arguments={"use_sim_time": "False"}.items()
    )

    ekf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_localization"),
                "launch",
                "ekf.launch.py"
            )
        ),
        launch_arguments={"use_sim_time": "False"}.items()
    )

    return LaunchDescription([
        use_slam_arg,
        serial_port_arg,
        map_name_arg,
        hardware_interface,
        laser_driver,
        controller_only,
        # controller_with_slider,
        joystick,
        imu_driver_node,
        localization,
        slam,
        #navigation,
        #ekf,
    ])