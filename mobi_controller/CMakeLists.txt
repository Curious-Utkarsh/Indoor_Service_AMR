cmake_minimum_required(VERSION 3.5)
project(mobi_controller)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2 REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(twist_mux_msgs REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(mobi_utils REQUIRED)

add_executable(slider_control src/slider_control.cpp)
ament_target_dependencies(slider_control rclcpp trajectory_msgs sensor_msgs)

include_directories(include)
include_directories(${EIGEN3_INCLUDE_DIR})

install(TARGETS
  slider_control
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY include
  DESTINATION include
)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()