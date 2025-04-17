#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <trajectory_msgs/msg/joint_trajectory_point.hpp>

#include <chrono>


using namespace std::chrono_literals;
using std::placeholders::_1;

class SliderControl : public rclcpp::Node
{
public:
  SliderControl() : Node("slider_control")
  {
    sub_ = create_subscription<sensor_msgs::msg::JointState>(
        "joint_commands", 10, std::bind(&SliderControl::sliderCallback, this, _1));
    rail_pub_ = create_publisher<trajectory_msgs::msg::JointTrajectory>("rail_controller/joint_trajectory", 10);
    neck_pub_ = create_publisher<trajectory_msgs::msg::JointTrajectory>("neck_controller/joint_trajectory", 10);
    RCLCPP_INFO(get_logger(), "Slider Control Node started");
  }

private:
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr sub_;
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr rail_pub_;
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr neck_pub_;

  void sliderCallback(const sensor_msgs::msg::JointState &msg) const
  {
    trajectory_msgs::msg::JointTrajectory rail_command;
    trajectory_msgs::msg::JointTrajectory neck_command;
    rail_command.joint_names = {"joint_1"};
    neck_command.joint_names = {"joint_2", "joint_3"};

    trajectory_msgs::msg::JointTrajectoryPoint rail_goal, neck_goal;
    rail_goal.positions.push_back(msg.position.at(2));  // joint_1
    neck_goal.positions.push_back(msg.position.at(3));  // joint_2
    neck_goal.positions.push_back(msg.position.at(4));  // joint_3
    
    rail_command.points.push_back(rail_goal);
    neck_command.points.push_back(neck_goal);
    
    rail_pub_->publish(rail_command);
    neck_pub_->publish(neck_command);
  }
};


int main(int argc, char* argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SliderControl>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
