#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from rclpy.action import ActionClient, CancelResponse

from nav2_msgs.action import NavigateToPose
from mobi_msgs.action import Undock  # ✅ Your custom Undock action

import asyncio

class TaskHandler(Node):
    def __init__(self):
        super().__init__('task_handler_node')
        self.get_logger().info("Task Handler Node Started")

        self.intent_sub = self.create_subscription(
            String, '/mobi/intents', self.intent_callback, 10)

        # Action clients
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.undock_client = ActionClient(self, Undock, 'undock')  # ✅ Undock client

        self.current_goal_handle = None

    def intent_callback(self, msg):
        it = msg.data.strip().lower()
        self.get_logger().info(f"Received intent: {it}")

        if it == 'go_to_kitchen':
            asyncio.create_task(self.go_to_kitchen())
        elif it == 'undock':
            asyncio.create_task(self.call_undock())
        elif it == 'stop':
            self.cancel_current_goal()
        else:
            self.get_logger().warn(f"Unknown intent: {it}")

    async def go_to_kitchen(self):
        self.nav_client.wait_for_server()
        self.get_logger().info("Navigating to kitchen...")

        goal = NavigateToPose.Goal()
        ps = PoseStamped()
        ps.header.frame_id = 'map'
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.pose.position.x = 4.0
        ps.pose.position.y = 1.0
        ps.pose.orientation.w = 1.0
        goal.pose = ps

        gh = await self.nav_client.send_goal_async(goal)
        if not gh.accepted:
            self.get_logger().warn("Nav2 goal rejected.")
            return

        self.current_goal_handle = gh
        res = await gh.get_result_async()
        self.get_logger().info(f"Navigation result: {res.result}")
        self.current_goal_handle = None

    async def call_undock(self):
        # DO NOT await here – it's a normal function
        self.undock_client.wait_for_server()
        self.get_logger().info("Sending undock request...")

        goal = Undock.Goal()

        # Define feedback callback
        def feedback_cb(feedback_msg):
            self.get_logger().info(f"Undock feedback: {feedback_msg.feedback.step}")

        # Send goal with feedback callback
        goal_future = self.undock_client.send_goal_async(goal, feedback_callback=feedback_cb)
        gh = await goal_future

        if not gh.accepted:
            self.get_logger().warn("Undock goal rejected.")
            return

        self.current_goal_handle = gh

        # Await result
        res = await gh.get_result_async()
        self.get_logger().info(f"Undock result: {res.result.success} - {res.result.message}")

        self.current_goal_handle = None



    def cancel_current_goal(self):
        if self.current_goal_handle:
            self.get_logger().info("Cancelling current goal...")
            cf = self.current_goal_handle.cancel_goal_async()
            cf.add_done_callback(lambda fut: 
                self.get_logger().info("Goal cancelled" if fut.result().goals_canceling else "Cancel failed")
            )
            self.current_goal_handle = None
        else:
            self.get_logger().info("No active goal to cancel")

def spin_async(node):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(_spin_loop(node))
    loop.run_forever()

async def _spin_loop(node):
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.1)
        await asyncio.sleep(0.01)

def main():
    rclpy.init()
    node = TaskHandler()
    spin_async(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
