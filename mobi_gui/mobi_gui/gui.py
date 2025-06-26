#!/usr/bin/env python3
import os
import sys
import signal
import time
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Mobi Robot Launcher')
        self.setFixedSize(600, 500)
        central_widget = QWidget(self)
        central_widget.setStyleSheet('background-color: #f5f5f5;')
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Title
        title = QLabel('Mobi Robot Launcher', self)
        title_font = QFont('Arial', 24, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('color: #333333;')
        main_layout.addWidget(title)

        # Launch buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(40)

        btn_real = self.create_button('Real Robot', '#007ACC')
        btn_real.clicked.connect(lambda: self.launch_mode('real'))

        btn_sim = self.create_button('Simulated Robot', '#007ACC')
        btn_sim.clicked.connect(lambda: self.launch_mode('sim'))

        button_layout.addWidget(btn_real)
        button_layout.addWidget(btn_sim)
        main_layout.addLayout(button_layout)

        # Stop button
        stop_layout = QHBoxLayout()
        stop_layout.setAlignment(Qt.AlignCenter)
        stop_layout.setContentsMargins(0, 20, 0, 0)

        btn_stop = QPushButton('■')
        btn_stop.setFixedSize(80, 80)
        btn_stop.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        stop_font = QFont('Arial', 32, QFont.Bold)
        btn_stop.setFont(stop_font)
        btn_stop.setStyleSheet(
            '''
            QPushButton {
                background-color: #E74C3C;
                border: 2px solid #C0392B;
                border-radius: 40px;
                color: white;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
            }
            QPushButton:pressed {
                background-color: #C0392B;
            }
            '''
        )
        stop_shadow = QGraphicsDropShadowEffect(self)
        stop_shadow.setBlurRadius(20)
        stop_shadow.setOffset(0, 4)
        stop_shadow.setColor(QColor(0, 0, 0, 100))
        btn_stop.setGraphicsEffect(stop_shadow)
        btn_stop.clicked.connect(self.stop_all)

        stop_layout.addWidget(btn_stop)
        main_layout.addLayout(stop_layout)

        # Track processes
        self.processes = []

    def create_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedSize(200, 200)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setFont(QFont('Arial', 16))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                border: 2px solid {color};
                border-radius: 15px;
                color: {color};
            }}
            QPushButton:hover {{ background-color: #E0F0FF; }}
            QPushButton:pressed {{ background-color: {color}; color: white; }}
        """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 75))
        btn.setGraphicsEffect(shadow)
        return btn

    def launch_mode(self, mode):
        # Build command
        pkg = 'mobi_bringup'
        launch_file = 'real_robot.launch.py' if mode == 'real' else 'simulated_robot.launch.py'
        cmd = ['ros2', 'launch', pkg, launch_file]
        # Start process with its own session (process group)
        try:
            p = subprocess.Popen(cmd, env=os.environ, preexec_fn=os.setsid)
            self.processes.append(p)
        except Exception as e:
            print(f"Failed to start launch: {e}")

    def stop_all(self):
        # Send SIGINT (Ctrl+C) to each group
        for p in self.processes:
            if p.poll() is None:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGINT)
                except Exception as e:
                    print(f"Error sending SIGINT: {e}")
        # Give processes time to shutdown
        time.sleep(1)
        # Force kill any remaining
        for p in self.processes:
            if p.poll() is None:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                except Exception as e:
                    print(f"Error sending SIGTERM: {e}")
        self.processes.clear()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet('QMainWindow { background-color: #f5f5f5; }')
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
