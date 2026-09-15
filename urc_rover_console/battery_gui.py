import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BatteryGui(QWidget):
    def __init__(self, ros_node):
        super().__init__()

        self.ros_node = ros_node

        self.setWindowTitle("URC Rover Console - Communication Test")
        self.setMinimumSize(460, 320)

        title = QLabel("ROVER OPERATIONS TEST")
        title.setAlignment(Qt.AlignCenter)

        self.battery_label = QLabel("Waiting for battery data...")
        self.battery_label.setAlignment(Qt.AlignCenter)

        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)

        self.state_label = QLabel("Navigation state: Waiting for data...")
        self.state_label.setAlignment(Qt.AlignCenter)

        self.command_status = QLabel("No operator command sent")
        self.command_status.setAlignment(Qt.AlignCenter)

        self.abort_button = QPushButton("ABORT AND RETURN")
        self.abort_button.setMinimumHeight(50)
        self.abort_button.clicked.connect(self.send_abort_command)

        self.abort_button.setStyleSheet(
            """
            QPushButton {
                background-color: #b91c1c;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #991b1b;
            }
            """
        )

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.battery_label)
        layout.addWidget(self.battery_bar)
        layout.addWidget(self.state_label)
        layout.addWidget(self.abort_button)
        layout.addWidget(self.command_status)
        self.setLayout(layout)

        self.battery_subscription = self.ros_node.create_subscription(
            Float32,
            "/rover/battery_percentage",
            self.update_battery,
            10,
        )

        self.state_subscription = self.ros_node.create_subscription(
            String,
            "/rover/navigation_state",
            self.update_navigation_state,
            10,
        )

        self.command_publisher = self.ros_node.create_publisher(
            String,
            "/operator/command",
            10,
        )

        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.process_ros_events)
        self.ros_timer.start(50)

    def process_ros_events(self):
        rclpy.spin_once(self.ros_node, timeout_sec=0)

    def update_battery(self, message):
        battery = max(0.0, min(100.0, message.data))
        self.battery_label.setText(f"Battery: {battery:.1f}%")
        self.battery_bar.setValue(round(battery))

    def update_navigation_state(self, message):
        self.state_label.setText(f"Navigation state: {message.data}")

    def send_abort_command(self):
        message = String()
        message.data = "ABORT_AND_RETURN"
        self.command_publisher.publish(message)

        self.command_status.setText(
            "Abort command sent—waiting for rover response"
        )


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
