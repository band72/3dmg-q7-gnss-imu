# MicroStrain ROS 2 Driver Configurations (`3dmg-q7-gnss-imu`)

This repository provides production-ready ROS 2 configuration templates, startup scripts, and a graphical desktop configurator to manage and launch MicroStrain sensors on **ROS 2 Jazzy**:
1. **3DM-GQ7-GNSS/INS**: Centimeter-level RTK positioning using Lord MicroStrain's `ntrip_client` integration.
2. **3DM-GX5-25**: High-frequency IMU/AHRS data streams.

---

## Hardware Setup & Serial Ports

The devices communicate over USB serial interfaces. For predictable port mappings, it is recommended to use the UDEV rules provided by the official driver:

* **3DM-GQ7**: Requires two connections:
  * **Main Port** (`/dev/microstrain_main`): For IMU, GNSS, EKF state, and configurations.
  * **Aux Port** (`/dev/microstrain_aux`): Used specifically to feed the incoming RTCM corrections to the RTK receiver and source NMEA sentences.
* **3DM-GX5-25**: Requires a single connection:
  * **Main Port** (`/dev/microstrain_main_<serial>`): For IMU and magnetometer data.

---

## Directory Structure

```
.
├── CMakeLists.txt
├── package.xml
├── README.md
├── config/
│   ├── microstrain.yml         # GQ7 driver parameters override
│   ├── gx5.yml                 # GX5-25 driver parameters override
│   ├── ntrip_client.yml        # NTRIP caster settings (ignored in git)
│   └── ntrip_client.template.yml # NTRIP caster settings template
├── launch/
│   ├── gq7_launch.py           # Launch GQ7 driver and ntrip client nodes
│   └── gx5_launch.py           # Launch GX5-25 driver node
├── scripts/
│   ├── configure_ntrip.py      # Tkinter desktop configuration GUI
│   ├── start_gq7.sh            # Dynamic launch script for GQ7
│   └── start_gx5.sh            # Dynamic launch script for GX5-25
└── test/
    └── test_configure_ntrip.py # Pytest unit testing suite
```

---

## Installation & Build Guide

### Prerequisites
Make sure you have a working ROS 2 Jazzy workspace. Install the required geodetic package:
```bash
sudo apt-get update
sudo apt-get install -y libgeographiclib-dev
```
*(If you do not have root privileges, download GeographicLib deb packages and extract them locally to `~/local`).*

### Step 1: Clone Repositories
Clone the required LORD MicroStrain packages and this configuration repo into your workspace:
```bash
cd ~/ros2_ws/src
git clone --recursive -b ros2 https://github.com/LORD-MicroStrain/microstrain_inertial.git
git clone -b ros2 https://github.com/LORD-MicroStrain/ntrip_client.git
git clone https://github.com/band72/3dmg-q7-gnss-imu.git microstrain_rtk_config
```

### Step 2: Build the Workspace
```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

---

## How to Use

For convenience, symbolic links to the GUI and startup scripts are created in the workspace root (`~/ros2_ws/`) upon package compilation.

### Option A: Desktop GUI Configurator (Recommended)
Launch the graphical interface directly from the workspace root:
```bash
./configure_ntrip.py
```
* **Device Selection Dropdown**: Switch between `3DM-GQ7 (RTK)` and `3DM-GX5-25 (IMU)`.
* **Dynamic Form Fields**: When `3DM-GX5-25` is selected, all NTRIP connection inputs are automatically disabled and grayed out.
* **IMU Rate Selector (Hz)**: Select frequency (`10`, `50`, `100`, `200`, or `500` Hz) for the IMU orientation and raw sensor data.
* **Auto-Save & Hot Reset**: Modifying the IMU frequency instantly saves the configuration to the device's parameters file. If the driver node is currently running, the GUI automatically triggers a hot reset (stops and restarts the driver) to apply the new rate.

### Option B: Script Launch (Headless)
Run the dynamic wrapper scripts from the workspace root:
* **Launch GQ7**:
  ```bash
  ./start_gq7.sh
  ```
* **Launch GX5-25**:
  ```bash
  ./start_gx5.sh
  ```

---

## ROS 2 Topics & Output Verification

Before inspecting the topic outputs, configure your environment to use the FastDDS loopback transport to bypass shared memory permissions issues:
```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=/home/artwalk/ros2_ws/fastdds_no_shm.xml
```

### 1. Verify GQ7 RTK Corrections Feed
* Echo `/rtcm` to verify the NTRIP caster binary RTCM stream:
  ```bash
  ros2 topic echo --once /rtcm
  ```
* Echo `/nmea` to verify the NMEA GGA feedback stream to the VRS caster:
  ```bash
  ros2 topic echo --once /nmea
  ```

### 2. Verify GX5-25 IMU Output
* Echo `/imu/data` to inspect raw and orientation estimations:
  ```bash
  ros2 topic echo --once /imu/data
  ```
* Echo `/imu/mag` to check active magnetometer outputs:
  ```bash
  ros2 topic echo --once /imu/mag
  ```

---

## FastDDS Shared Memory Configuration (UDP Loopback)
To avoid Shared Memory permissions warnings (e.g., `Failed init_port fastrtps_port7002`) common in multi-user or containerized setups, we force FastDDS to use UDP loopback instead.
* Profile location: `/home/artwalk/ros2_ws/fastdds_no_shm.xml`
* The startup scripts automatically export the environment variable `FASTRTPS_DEFAULT_PROFILES_FILE` pointing to this XML profile before launching the nodes.

---

## Unit Testing & Code Styling Quality
We use `pytest` for functional parameter validations, and standard ROS 2 linters for code quality verification.

### Run Tests:
```bash
source /opt/ros/jazzy/setup.bash
colcon test --packages-select microstrain_rtk_config --event-handlers console_cohesion+
```
The suite verifies **100% success** across 5 test suites:
* Pytest functional testing (`test_configure_ntrip.py`)
* Python formatting compliance (`flake8`)
* Python docstrings standard compliance (`pep257`)
* XML package format validation (`xmllint`)
* CMake build script structure validation (`lint_cmake`)

---

## Credential Security
To prevent sensitive NTRIP CORS caster credentials (hostnames, usernames, passwords) from being pushed to public git repos:
* `config/ntrip_client.yml` is added to `.gitignore`.
* A template configuration file [config/ntrip_client.template.yml](config/ntrip_client.template.yml) is tracked in Git with placeholder values.
