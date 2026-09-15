import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


class RoverSimulator(Node):
    def __init__(self):
        super().__init__("rover_simulator")

        self.battery_percentage = 100.0
        self.navigation_state = "NAVIGATING"

        self.battery_publisher = self.create_publisher(
            Float32,
            "/rover/battery_percentage",
            10,
        )

        self.state_publisher = self.create_publisher(
            String,
            "/rover/navigation_state",
            10,
        )

        self.command_subscription = self.create_subscription(
            String,
            "/operator/command",
            self.receive_command,
            10,
        )

        self.timer = self.create_timer(1.0, self.publish_telemetry)
        self.get_logger().info("Rover simulator started")

    def publish_telemetry(self):
        battery_message = Float32()
        battery_message.data = self.battery_percentage
        self.battery_publisher.publish(battery_message)

        state_message = String()
        state_message.data = self.navigation_state
        self.state_publisher.publish(state_message)

        self.get_logger().info(
            f"Battery: {self.battery_percentage:.1f}% | "
            f"State: {self.navigation_state}"
        )

        self.battery_percentage -= 0.5

        if self.battery_percentage < 20.0:
            self.battery_percentage = 100.0

    def receive_command(self, message):
        self.get_logger().info(f"Command received: {message.data}")

        if message.data == "ABORT_AND_RETURN":
            self.navigation_state = "RETURNING"
            self.get_logger().warning(
                "Current attempt aborted. Returning to previous target."
            )


def main(args=None):
    rclpy.init(args=args)
    node = RoverSimulator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
