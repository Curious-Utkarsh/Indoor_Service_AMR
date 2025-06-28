#!/usr/bin/env python3
import os
import sys
import signal
import time
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QComboBox, QGroupBox, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Window title and size tailored for a 7" RPi display (800×480)
        self.setWindowTitle('Robot Launcher')
        self.setFixedSize(800, 480)

        central = QWidget()
        central.setStyleSheet('background-color: #f0f0f0;')
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # -- Real Robot Section --
        real_group = QGroupBox('Real Robot')
        real_group.setFont(QFont('Arial', 14, QFont.Bold))
        real_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        real_group.setStyleSheet(
            "QGroupBox { background-color:#ffffff; border:1px solid #cccccc; border-radius:5px; margin-top:20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 5px; color:#000000; }"
        )
        real_layout = QVBoxLayout()
        real_layout.setContentsMargins(10, 25, 10, 10)
        real_layout.setSpacing(8)

        combo_style = """
            QComboBox { background-color: #ffffff; color: #000000; padding: 3px; border: 1px solid #cccccc; border-radius: 4px; }
            QComboBox:hover { border: 1px solid #007ACC; }
            QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; }
            QComboBox QAbstractItemView { background-color: #ffffff; color: #000000; selection-background-color: #007ACC; selection-color: white; }
            QComboBox QAbstractItemView::item:hover { background-color: #E0F0FF; }
        """
        # Real parameters
        for label, items, attr in [
            ('Use SLAM', ['true','false'], 'real_slam'),
            ('Serial Port', ['/dev/ttyUSB0','/dev/ttyUSB1'], 'real_serial'),
            ('Map Name', ['Room1','Room2','Hall'], 'real_map')
        ]:
            lbl = QLabel(label)
            lbl.setFont(QFont('Arial', 12, QFont.Bold))
            real_layout.addWidget(lbl)
            combo = QComboBox()
            combo.addItems(items)
            combo.setFont(QFont('Arial', 12, QFont.Bold))
            combo.setFixedHeight(26)
            combo.setCursor(QCursor(Qt.PointingHandCursor))
            combo.setStyleSheet(combo_style)
            real_layout.addWidget(combo)
            setattr(self, attr, combo)

        # Real control buttons
        for name, handler in [('Start Real', self.start_real), ('Stop Real', self.stop_real), ('Save Real Map', self.save_real_map)]:
            btn = QPushButton(name)
            btn.setFont(QFont('Arial', 12, QFont.Bold))
            btn.setFixedHeight(30)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(
                'QPushButton { background-color:#ffffff; border:2px solid #007ACC; border-radius:5px; }'
                'QPushButton:hover { background-color:#E0F0FF; }'
                'QPushButton:pressed { background-color:#007ACC; color:white; }'
            )
            btn.clicked.connect(handler)
            real_layout.addWidget(btn)
        real_group.setLayout(real_layout)

        # -- Simulated Robot Section --
        sim_group = QGroupBox('Simulated Robot')
        sim_group.setFont(QFont('Arial', 14, QFont.Bold))
        sim_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sim_group.setStyleSheet(
            "QGroupBox { background-color:#ffffff; border:1px solid #cccccc; border-radius:5px; margin-top:20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 5px; color:#000000; }"
        )
        sim_layout = QVBoxLayout()
        sim_layout.setContentsMargins(10, 25, 10, 10)
        sim_layout.setSpacing(8)

        # Sim parameters
        for label, items, attr in [
            ('Use SLAM', ['true','false'], 'sim_slam'),
            ('World Name', ['empty','small_house','small_warehouse'], 'sim_world'),
            ('Map Name', ['small_house','small_warehouse'], 'sim_map')
        ]:
            lbl = QLabel(label)
            lbl.setFont(QFont('Arial', 12, QFont.Bold))
            sim_layout.addWidget(lbl)
            combo = QComboBox()
            combo.addItems(items)
            combo.setFont(QFont('Arial', 12, QFont.Bold))
            combo.setFixedHeight(26)
            combo.setCursor(QCursor(Qt.PointingHandCursor))
            combo.setStyleSheet(combo_style)
            sim_layout.addWidget(combo)
            setattr(self, attr, combo)

        # Sim control buttons
        for name, handler in [('Start Sim', self.start_sim), ('Stop Sim', self.stop_sim), ('Save Sim Map', self.save_sim_map)]:
            btn = QPushButton(name)
            btn.setFont(QFont('Arial', 12, QFont.Bold))
            btn.setFixedHeight(30)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(
                'QPushButton { background-color:#ffffff; border:2px solid #007ACC; border-radius:5px; }'
                'QPushButton:hover { background-color:#E0F0FF; }'
                'QPushButton:pressed { background-color:#007ACC; color:white; }'
            )
            btn.clicked.connect(handler)
            sim_layout.addWidget(btn)
        sim_group.setLayout(sim_layout)

        # Add sections
        main_layout.addWidget(real_group)
        main_layout.addWidget(sim_group)

        # Process handles
        self.real_proc = None
        self.sim_proc  = None

    def _next_map_folder(self, base_dir):
        os.makedirs(base_dir, exist_ok=True)
        nums = [int(d.split('_')[-1]) for d in os.listdir(base_dir)
                if d.startswith('test_map_') and d.split('_')[-1].isdigit()]
        next_num = max(nums) + 1 if nums else 1
        full_path = os.path.join(base_dir, f'test_map_{next_num}')
        os.makedirs(full_path)
        return full_path

    def save_real_map(self):
        folder = self._next_map_folder('/home/piro/mobi_ws/src/mobi_mapping/maps')
        subprocess.Popen(['ros2','run','nav2_map_server','map_saver_cli','-f',os.path.join(folder,'map')], env=os.environ, preexec_fn=os.setsid)

    def save_sim_map(self):
        folder = self._next_map_folder('/home/utk/mobi_ws/src/mobi_mapping/maps')
        subprocess.Popen(['ros2','run','nav2_map_server','map_saver_cli','-f',os.path.join(folder,'map')], env=os.environ, preexec_fn=os.setsid)

    def start_real(self):
        if self.real_proc and self.real_proc.poll() is None:
            return
        args = f"use_slam:={self.real_slam.currentText()} serial_port:={self.real_serial.currentText()} map_name:={self.real_map.currentText()}"
        cmd = ['bash','-lc',f"ros2 launch mobi_bringup real_robot.launch.py {args}"]
        self.real_proc = subprocess.Popen(cmd, env=os.environ, preexec_fn=os.setsid)

    def stop_real(self):
        if self.real_proc and self.real_proc.poll() is None:
            os.killpg(os.getpgid(self.real_proc.pid), signal.SIGINT)
            time.sleep(1)
            if self.real_proc.poll() is None:
                os.killpg(os.getpgid(self.real_proc.pid), signal.SIGTERM)
        self.real_proc = None

    def start_sim(self):
        if self.sim_proc and self.sim_proc.poll() is None:
            return
        args = f"use_slam:={self.sim_slam.currentText()} world_name:={self.sim_world.currentText()} map_name:={self.sim_map.currentText()}"
        cmd = ['bash','-lc',f"ros2 launch mobi_bringup simulated_robot.launch.py {args}"]
        self.sim_proc = subprocess.Popen(cmd, env=os.environ, preexec_fn=os.setsid)

    def stop_sim(self):
        if self.sim_proc and self.sim_proc.poll() is None:
            os.killpg(os.getpgid(self.sim_proc.pid), signal.SIGINT)
            time.sleep(1)
            if self.sim_proc.poll() is None:
                os.killpg(os.getpgid(self.sim_proc.pid), signal.SIGTERM)
        self.sim_proc = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec_())
