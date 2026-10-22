# Mobi — Indoor Service Robot (ROS 2)

[![ROS 2 Humble](https://img.shields.io/badge/ROS%202-Humble-22314E?logo=ros)](https://docs.ros.org/en/humble/)
[![Nav2](https://img.shields.io/badge/Nav2-SLAM%20%2B%20navigation-1F6FEB)](https://docs.nav2.org/)
[![Teensy 4.1](https://img.shields.io/badge/MCU-Teensy%204.1-555)](https://www.pjrc.com/store/teensy41.html)
[![Real hardware](https://img.shields.io/badge/runs%20on-real%20hardware-2EA44F)](#demo)

Mobi is a differential-drive service robot I designed and built for indoor spaces. It maps a room, localizes, navigates through tight passages, backs out of its dock on its own, and acts on spoken commands such as "undock" or "go to the kitchen". A Raspberry Pi runs the ROS 2 stack; a Teensy 4.1 runs the motor control; the same packages drive a Gazebo twin.

The torso carries a lifting rail and a pan-tilt head, built for arms that were planned but not added. Navigation, voice control and docking run on the real robot.

## Demo

<table>
<tr>
<td align="center"><a href="https://www.youtube.com/shorts/Y7EMHcqw5RQ"><img src="https://img.youtube.com/vi/Y7EMHcqw5RQ/hqdefault.jpg" width="250" alt="Mobi autonomous service robot"></a><br><sub>Voice-driven service demo</sub></td>
<td align="center"><a href="https://www.youtube.com/shorts/A8FcfQKHm_Q"><img src="https://img.youtube.com/vi/A8FcfQKHm_Q/hqdefault.jpg" width="250" alt="Mobi SLAM and navigation"></a><br><sub>SLAM and navigation</sub></td>
<td align="center"><a href="https://youtu.be/QhUhHbz_ZHU"><img src="https://img.youtube.com/vi/QhUhHbz_ZHU/hqdefault.jpg" width="250" alt="Robot Launcher GUI"></a><br><sub>Robot Launcher GUI</sub></td>
</tr>
</table>

Playlist: [ROS 2 Projects](https://www.youtube.com/playlist?list=PLVjFk3hP8Wm4)

Case study: [Mobi on my portfolio](https://curious-utkarsh.github.io/projects/mobi/)

Also: [joystick teleoperation](https://youtu.be/tbZFirvaFq8) · [face and hand tracking driving the head in Gazebo](https://youtu.be/g8SuOeqCy2A)

Build log on LinkedIn (2025): [physical structure](https://www.linkedin.com/feed/update/urn:li:activity:7308149354974875648/) · [drive base progress](https://www.linkedin.com/feed/update/urn:li:activity:7309089843953774592/) · [encoder readings at speed](https://www.linkedin.com/feed/update/urn:li:activity:7310514592126746629/) · [joystick control](https://www.linkedin.com/feed/update/urn:li:activity:7312521395224080385/) · [SLAM map distortion](https://www.linkedin.com/feed/update/urn:li:activity:7313719472240869376/) · [autonomous chassis](https://www.linkedin.com/feed/update/urn:li:activity:7315668001528127488/) · [A* vs Dijkstra](https://www.linkedin.com/feed/update/urn:li:activity:7342869348153217024/) · [Robot Launcher app](https://www.linkedin.com/feed/update/urn:li:activity:7345315157805305856/) · [adding the torso](https://www.linkedin.com/feed/update/urn:li:activity:7352925309186297858/) · [voice docking with an LLM](https://www.linkedin.com/feed/update/urn:li:activity:7355552667160530944/)

Building Mobi from CAD to simulation (4-part series): [Fusion 360 CAD](https://youtu.be/TRADhNjp63E) · [URDF part 1](https://youtu.be/uwYU_mx7p3k) · [URDF part 2](https://youtu.be/GTiLhWPwOXQ) · [spawning in Gazebo](https://youtu.be/LI0W00ytupg)

## Key features

- **Mapping and navigation** — slam_toolbox, AMCL, Nav2 (Smac Planner 2D + Regulated Pure Pursuit) with replanning and recovery behaviour trees.
- **Own motor control stack** — Teensy 4.1 firmware with per-wheel PID at 100 Hz and a C++ `ros2_control` hardware interface over 500 kbaud serial.
- **Voice → action** — Whisper transcribes, Gemini returns an intent (`dock`, `undock`, `go_to_kitchen`, `go_to_user`, `stop`), and a task handler turns it into Nav2 goals or an `Undock` action.
- **Undocking action server** — reverses until the ultrasonic sensor clears 0.35 m, then turns away using IMU yaw rate; cancellable, with timeouts.
- **Safety by arbitration** — a LiDAR safety-stop node holds a `twist_mux` lock at priority 255 above joystick, keyboard and Nav2.
- **Robot Launcher** — a PyQt5 app that starts the real robot or the simulation with map, world, SLAM mode and serial port chosen from drop-downs, and saves versioned maps.
- **Own planner and controller plugins** — A\*, Dijkstra, PD and pure-pursuit written as Nav2 plugins in C++ (available, not enabled by default).

## Hardware

| | |
|---|---|
| Compute | Raspberry Pi 4B (8 GB) + 7-inch touchscreen |
| Motion | Teensy 4.1, 2 × DC gear motors with high-resolution quadrature encoders, PWM/DIR driver |
| Sensing | RPLiDAR, MPU6050 IMU, ultrasonic sensor, camera |
| Body | Torso on dual lead-screw linear rails, pan-tilt head; 12 V 30 A supply with 5 V 20 A buck during development |

## Software stack

ROS 2 Humble · Nav2 · slam_toolbox · AMCL · ros2_control · twist_mux · Gazebo Fortress · OpenCV (ArUco) · MediaPipe · Whisper · Gemini API · ElevenLabs · PyQt5 · C++ · Python

## Packages

`mobi_description` URDF and worlds · `mobi_firmware` Teensy sketch + hardware interface · `mobi_controller` diff-drive, joystick, twist_mux · `mobi_mapping` / `mobi_localization` / `mobi_navigation` SLAM, AMCL, Nav2 · `mobi_planning` / `mobi_motion` own Nav2 plugins · `mobi_script` task handler + undock action · `mobi_speech` voice · `mobi_vision` ArUco, face and hand tracking · `mobi_utils` safety stop · `mobi_gui` Robot Launcher · `mobi_bringup` launch files

## Run

```bash
mkdir -p ~/mobi_ws/src && cd ~/mobi_ws/src
git clone https://github.com/Curious-Utkarsh/mobi-service-robot.git .
cd ~/mobi_ws && rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install && source install/setup.bash

ros2 launch mobi_bringup simulated_robot.launch.py world_name:=small_house map_name:=small_house   # simulation
ros2 launch mobi_bringup real_robot.launch.py serial_port:=/dev/ttyUSB0 map_name:=Room1          # real robot
ros2 topic pub --once /mobi/intents std_msgs/msg/String "data: 'undock'"                           # test a behaviour
```

The voice node reads its keys from the environment: `export GEMINI_API_KEY=...` and `export ELEVENLABS_API_KEY=...` before launching it.

## Engineering notes

- **Encoders the ESP32 could not keep up with.** With an ESP32 at 240 MHz, wheel counts from the high-resolution encoders were unreliable, which corrupted odometry and everything above it. I isolated the encoder layer, confirmed counts were being missed, and moved motor control to a Teensy 4.1 at 600 MHz, which reads them cleanly.
- **Tight passages.** With a 0.58 × 0.56 m costmap footprint the robot had to pass ~0.8 m openings. On the real robot it stopped mid-path even with obstacles far away; I traced it to costmaps not clearing after dynamic obstacles moved. The current workaround disables obstacle checks in the local controller — a stopgap, not a fix; a behaviour-tree recovery is next.

## Related

- [MechaBot](https://github.com/MechaMind-Labs/AMR-Mastery) — the smaller robot I built next, with QR + LiDAR docking
- [Aura](https://github.com/Curious-Utkarsh/aura-mobile-manipulator) — simulated predecessor with an arm and vision docking
- [Bumperbot](https://github.com/Curious-Utkarsh/bumperbot-diff-drive-robot) — an earlier differential-drive robot on real hardware
- [TurtleBot3 ArUco docking](https://github.com/Curious-Utkarsh/turtlebot3-aruco-docking) — where the docking work started

## Credits

Package layout and the `mobi_planning` / `mobi_motion` plugins follow Antonio Brandi's *Self-Driving and ROS 2 — Learn by Doing* course series. House and warehouse worlds use [AWS RoboMaker](https://github.com/aws-robotics/aws-robomaker-small-house-world) models.

---
[Kumar Utkarsh](https://github.com/Curious-Utkarsh) · [LinkedIn](https://www.linkedin.com/in/kumar-utkarsh-124aab227/) · [MechaMind Labs](https://www.mechamindlabs.com/)
