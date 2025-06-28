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
        self.setWindowTitle('Robot Launcher')
        self.setFixedSize(900, 600)

        central = QWidget()
        central.setStyleSheet('background-color: #f0f0f0;')
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # -- Real Robot Section --
        real_group = QGroupBox('Real Robot')
        real_group.setFont(QFont('Arial', 16, QFont.Bold))
        real_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        real_group.setStyleSheet(
            "QGroupBox { background-color:#ffffff; border:1px solid #cccccc; border-radius:5px; margin-top:20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 5px; color:#000000; }"
        )
        real_layout = QVBoxLayout()
        real_layout.setContentsMargins(15, 30, 15, 15)
        real_layout.setSpacing(10)

        # Real parameters
        combo_style = """
            QComboBox { background-color: #ffffff; color: #000000; padding: 4px; border: 1px solid #cccccc; border-radius: 4px; }
            QComboBox:hover { border: 1px solid #007ACC; }
            QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #007ACC;
                selection-color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #E0F0FF;
            }
        """
        for label, items, attr in [
            ('Use SLAM', ['true','false'], 'real_slam'),
            ('Serial Port', ['/dev/ttyUSB0','/dev/ttyUSB1'], 'real_serial'),
            ('Map Name', ['Room1','Room2','Hall'], 'real_map')
        ]:
            lbl = QLabel(label)
            lbl.setFont(QFont('Arial', 14, QFont.Bold))
            real_layout.addWidget(lbl)
            combo = QComboBox()
            combo.addItems(items)
            combo.setFont(QFont('Arial', 14, QFont.Bold))
            combo.setFixedHeight(28)
            combo.setCursor(QCursor(Qt.PointingHandCursor))
            combo.setStyleSheet(combo_style)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            real_layout.addWidget(combo)
            setattr(self, attr, combo)

        # Real control buttons
        self.real_start = QPushButton('Start Real')
        self.real_stop  = QPushButton('Stop Real')
        self.real_save  = QPushButton('Save Real Map')
        for btn in (self.real_start, self.real_stop, self.real_save):
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFont(QFont('Arial', 14, QFont.Bold))
            btn.setFixedHeight(38)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(
                'QPushButton { background-color:#ffffff; border:2px solid #007ACC; border-radius:5px; }'
                'QPushButton:hover { background-color:#E0F0FF; }'
                'QPushButton:pressed { background-color:#007ACC; color:white; }'
            )
            real_layout.addWidget(btn)
        real_group.setLayout(real_layout)

        # -- Simulated Robot Section --
        sim_group = QGroupBox('Simulated Robot')
        sim_group.setFont(QFont('Arial', 16, QFont.Bold))
        sim_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sim_group.setStyleSheet(
            "QGroupBox { background-color:#ffffff; border:1px solid #cccccc; border-radius:5px; margin-top:20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 5px; color:#000000; }"
        )
        sim_layout = QVBoxLayout()
        sim_layout.setContentsMargins(15, 30, 15, 15)
        sim_layout.setSpacing(10)

        # Sim parameters
        for label, items, attr in [
            ('Use SLAM', ['true','false'], 'sim_slam'),
            ('World Name', ['empty','small_house','small_warehouse'], 'sim_world'),
            ('Map Name', ['small_house','small_warehouse'], 'sim_map')
        ]:
            lbl = QLabel(label)
            lbl.setFont(QFont('Arial', 14, QFont.Bold))
            sim_layout.addWidget(lbl)
            combo = QComboBox()
            combo.addItems(items)
            combo.setFont(QFont('Arial', 14, QFont.Bold))
            combo.setFixedHeight(28)
            combo.setCursor(QCursor(Qt.PointingHandCursor))
            combo.setStyleSheet(combo_style)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            sim_layout.addWidget(combo)
            setattr(self, attr, combo)

        # Sim control buttons
        self.sim_start = QPushButton('Start Sim')
        self.sim_stop  = QPushButton('Stop Sim')
        self.sim_save  = QPushButton('Save Sim Map')
        for btn in (self.sim_start, self.sim_stop, self.sim_save):
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFont(QFont('Arial', 14, QFont.Bold))
            btn.setFixedHeight(38)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(
                'QPushButton { background-color:#ffffff; border:2px solid #007ACC; border-radius:5px; }'
                'QPushButton:hover { background-color:#E0F0FF; }'
                'QPushButton:pressed { background-color:#007ACC; color:white; }'
            )
            sim_layout.addWidget(btn)
        sim_group.setLayout(sim_layout)

        # Add sections to main layout
        main_layout.addWidget(real_group)
        main_layout.addWidget(sim_group)

        # Connect signals
        self.real_start.clicked.connect(self.start_real)
        self.real_stop.clicked.connect(self.stop_real)
        self.real_save.clicked.connect(self.save_real_map)
        self.sim_start.clicked.connect(self.start_sim)
        self.sim_stop.clicked.connect(self.stop_sim)
        self.sim_save.clicked.connect(self.save_sim_map)

        # Process handles
        self.real_proc = None
        self.sim_proc  = None

    def _next_map_folder(self, base_dir):
        os.makedirs(base_dir, exist_ok=True)
        nums = [int(d.split('_')[-1]) for d in os.listdir(base_dir)
                if d.startswith('test_map_') and d.split('_')[-1].isdigit()]
        next_num = max(nums) + 1 if nums else 1
        new_folder = f'test_map_{next_num}'
        full_path = os.path.join(base_dir, new_folder)
        os.makedirs(full_path)
        return full_path

    def save_real_map(self):
        base = '/home/piro/mobi_ws/src/mobi_mapping/maps'
        folder = self._next_map_folder(base)
        cmd = ['ros2', 'run', 'nav2_map_server', 'map_saver_cli', '-f', os.path.join(folder, 'map')]
        subprocess.Popen(cmd, env=os.environ, preexec_fn=os.setsid)

    def save_sim_map(self):
        base = '/home/utk/mobi_ws/src/mobi_mapping/maps'
        folder = self._next_map_folder(base)
        cmd = ['ros2', 'run', 'nav2_map_server', 'map_saver_cli', '-f', os.path.join(folder, 'map')]
        subprocess.Popen(cmd, env=os.environ, preexec_fn=os.setsid)

    def start_real(self):
        if self.real_proc and self.real_proc.poll() is None:
            return
        args = [
            f'use_slam:={self.real_slam.currentText()}',
            f'serial_port:={self.real_serial.currentText()}',
            f'map_name:={self.real_map.currentText()}']
        self.real_proc = subprocess.Popen(
            ['ros2', 'launch', 'mobi_bringup', 'real_robot.launch.py'] + args,
            env=os.environ, preexec_fn=os.setsid)

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
        args = [
            f'use_slam:={self.sim_slam.currentText()}',
            f'world_name:={self.sim_world.currentText()}',
            f'map_name:={self.sim_map.currentText()}']
        self.sim_proc = subprocess.Popen(
            ['ros2', 'launch', 'mobi_bringup', 'simulated_robot.launch.py'] + args,
            env=os.environ, preexec_fn=os.setsid)

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
