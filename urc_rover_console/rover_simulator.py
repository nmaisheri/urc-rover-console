import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class RoverSimulator(Node):
    def __init__(self):
        super().__init__("rover_simulator")

        self.battery_percentage = 100.0

        self.battery_publisher = self.create_publisher(
            Float32,
            "/rover/battery_percentage",
            10,
        )

        self.timer = self.create_timer(1.0, self.publish_battery)
        self.get_logger().info("Rover simulator started")

    def publish_battery(self):
        message = Float32()
        message.data = self.battery_percentage
        self.battery_publisher.publish(message)

        self.get_logger().info(
            f"Battery percentage: {self.battery_percentage:.1f}%"
        )

        self.battery_percentage -= 0.5

        if self.battery_percentage < 20.0:
            self.battery_percentage = 100.0


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
