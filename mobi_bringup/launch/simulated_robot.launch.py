import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    use_slam = LaunchConfiguration("use_slam")
    map_name = LaunchConfiguration("map_name")
    world_name = LaunchConfiguration("world_name")

    use_slam_arg = DeclareLaunchArgument(
        "use_slam",
        default_value="false"
    )

    map_name_arg = DeclareLaunchArgument(
        "map_name",
        default_value="small_house"
    )

    world_name_arg = DeclareLaunchArgument(
        "world_name",
        default_value="small_house" #Change this when using slam
    )

    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mobi_description"),
            "launch",
            "gazebo.launch.py"
        ),
        launch_arguments={
            "world_name": world_name
        }.items()
    )
    
    controller_only = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mobi_controller"),
            "launch",
            "controller.launch.py"
        ),
    )

    controller_with_slider = IncludeLaunchDescription( #Use this when slider needed else use above one
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
        launch_arguments={"use_sim_time": "True"}.items()
    )

    localization = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mobi_localization"),
            "launch",
            "global_localization.launch.py"
        ),
        launch_arguments={
            "use_sim_time": "True",
            "map_name": map_name
        }.items(),
        condition=UnlessCondition(use_slam)
    )

    navigation = IncludeLaunchDescription(
            os.path.join(
                get_package_share_directory("mobi_navigation"),
                "launch",
                "navigation.launch.py"
            ),
        )

    slam = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("mobi_mapping"),
            "launch",
            "slam.launch.py"
        ),
        launch_arguments={"use_sim_time": "True"}.items(),
        condition=IfCondition(use_slam)
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(
                get_package_share_directory("mobi_localization"),
                "rviz",
                "global_localization.rviz"
            )
        ],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    ekf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("mobi_localization"),
                "launch",
                "ekf.launch.py"
            )
        ),
        launch_arguments={"use_sim_time": "True"}.items()
    )

    vision = IncludeLaunchDescription( 
        os.path.join(
            get_package_share_directory("mobi_vision"),
            "launch",
            "vision.launch.py"
        ),
    )

    speech = IncludeLaunchDescription( 
        os.path.join(
            get_package_share_directory("mobi_speech"),
            "launch",
            "speech.launch.py"
        ),
    )

    script = IncludeLaunchDescription( 
        os.path.join(
            get_package_share_directory("mobi_script"),
            "launch",
            "script.launch.py"
        ),
    )
    
    return LaunchDescription([
        use_slam_arg,
        map_name_arg,
        world_name_arg,
        gazebo,
        controller_only,
        #controller_with_slider,
        joystick,
        localization,
        slam,
        rviz,
        navigation,
        # ekf,
        # vision,
        speech,
        script,
    ])