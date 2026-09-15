import sys
import time

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
        self.last_telemetry_time = None
        self.stale_timeout = 2.5

        self.setWindowTitle("URC Rover Console - Communication Test")
        self.setMinimumSize(500, 380)

        title = QLabel("ROVER OPERATIONS TEST")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 8px;"
        )

        self.connection_label = QLabel("ROS link: WAITING FOR DATA")
        self.connection_label.setAlignment(Qt.AlignCenter)
        self.connection_label.setStyleSheet(
            "background-color: #d1d5db; "
            "padding: 8px; "
            "font-weight: bold;"
        )

        self.battery_label = QLabel("Waiting for battery data...")
        self.battery_label.setAlignment(Qt.AlignCenter)

        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)

        self.state_label = QLabel(
            "Navigation state: Waiting for data..."
        )
        self.state_label.setAlignment(Qt.AlignCenter)

        self.command_status = QLabel("No operator command sent")
        self.command_status.setAlignment(Qt.AlignCenter)
        self.command_status.setWordWrap(True)

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

            QPushButton:pressed {
                background-color: #7f1d1d;
            }
            """
        )

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.connection_label)
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

        # This timer lets Qt process ROS messages without freezing the GUI.
        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.process_ros_events)
        self.ros_timer.start(50)

        # This timer checks whether telemetry has stopped arriving.
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(
            self.check_connection_health
        )
        self.connection_timer.start(250)

    def process_ros_events(self):
        rclpy.spin_once(self.ros_node, timeout_sec=0)

    def update_battery(self, message):
        self.last_telemetry_time = time.monotonic()

        battery = max(0.0, min(100.0, message.data))

        self.battery_label.setText(
            f"Battery: {battery:.1f}%"
        )
        self.battery_bar.setValue(round(battery))

    def update_navigation_state(self, message):
        self.last_telemetry_time = time.monotonic()

        self.state_label.setText(
            f"Navigation state: {message.data}"
        )

        if message.data == "RETURNING":
            self.command_status.setText(
                "Rover acknowledged command and is returning"
            )

    def send_abort_command(self):
        message = String()
        message.data = "ABORT_AND_RETURN"
        self.command_publisher.publish(message)

        self.command_status.setText(
            "Abort command sent - waiting for rover response"
        )

    def check_connection_health(self):
        if self.last_telemetry_time is None:
            self.connection_label.setText(
                "ROS link: WAITING FOR DATA"
            )
            self.connection_label.setStyleSheet(
                "background-color: #d1d5db; "
                "padding: 8px; "
                "font-weight: bold;"
            )
            return

        message_age = (
            time.monotonic() - self.last_telemetry_time
        )

        if message_age <= self.stale_timeout:
            self.connection_label.setText(
                f"ROS link: ACTIVE - "
                f"last update {message_age:.1f}s ago"
            )
            self.connection_label.setStyleSheet(
                "background-color: #15803d; "
                "color: white; "
                "padding: 8px; "
                "font-weight: bold;"
            )
        else:
            self.connection_label.setText(
                f"WARNING: TELEMETRY STALE - "
                f"no update for {message_age:.1f}s"
            )
            self.connection_label.setStyleSheet(
                "background-color: #b91c1c; "
                "color: white; "
                "padding: 8px; "
                "font-weight: bold;"
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
