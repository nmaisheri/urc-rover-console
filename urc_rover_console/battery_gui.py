import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QProgressBar, QVBoxLayout, QWidget


class BatteryGui(QWidget):
    def __init__(self, ros_node):
        super().__init__()

        self.ros_node = ros_node

        self.setWindowTitle("URC Rover Console - Battery Test")
        self.setMinimumSize(420, 220)

        title = QLabel("ROVER POWER")
        title.setAlignment(Qt.AlignCenter)

        self.battery_label = QLabel("Waiting for battery data...")
        self.battery_label.setAlignment(Qt.AlignCenter)

        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.battery_label)
        layout.addWidget(self.battery_bar)
        self.setLayout(layout)

        self.subscription = self.ros_node.create_subscription(
            Float32,
            "/rover/battery_percentage",
            self.update_battery,
            10,
        )

        # Process incoming ROS messages without freezing PyQt.
        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.process_ros_events)
        self.ros_timer.start(50)

    def process_ros_events(self):
        rclpy.spin_once(self.ros_node, timeout_sec=0)

    def update_battery(self, message):
        battery = max(0.0, min(100.0, message.data))

        self.battery_label.setText(f"Battery: {battery:.1f}%")
        self.battery_bar.setValue(round(battery))


def main(args=None):
    rclpy.init(args=args)

    ros_node = Node("battery_gui")
    application = QApplication(sys.argv)
    window = BatteryGui(ros_node)
    window.show()

    try:
        exit_code = application.exec_()
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
