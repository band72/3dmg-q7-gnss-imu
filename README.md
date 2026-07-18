# 3DM-GQ7-GNSS/INS RTK ROS 2 Configuration

This repository contains the custom ROS 2 configuration package (`microstrain_rtk_config`) designed to orchestrate centimeter-level RTK updates for the **MicroStrain 3DM-GQ7-GNSS/INS** IMU.

It runs the official `microstrain_inertial_driver` and `ntrip_client` nodes in harmony, handling:
* Auxiliary port RTCM corrections input.
* NMEA GGA sentence feedback back to the NTRIP caster for Virtual Reference Station (VRS) support.

---

## Repository Structure

* **`config/microstrain.yml`**: Driver parameters tailored for GQ7 serial ports, RTK interface, and NMEA outputs.
* **`config/ntrip_client.yml`**: Connection parameters template for your NTRIP correction service.
* **`launch/rtk_launch.py`**: Unified ROS 2 Python launch description starting both nodes.
* **`scripts/start_rtk.sh`**: Bash script wrapper configuring dependencies and launching the nodes.

---

## Workspace Setup & Installation

To use this configuration, you need a ROS 2 workspace with the official MicroStrain driver and NTRIP client packages built alongside it.

### Step 1: Create a ROS 2 Workspace (if you don't have one)
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

### Step 2: Clone the Required Driver Repositories
Clone the official packages to your workspace:
```bash
# Clone official microstrain driver (must be recursive for submodules!)
git clone --recursive -b ros2 https://github.com/LORD-MicroStrain/microstrain_inertial.git

# Clone official ntrip client
git clone -b ros2 https://github.com/LORD-MicroStrain/ntrip_client.git

# Clone this configuration repository
git clone https://github.com/band72/3dmg-q7-gnss-imu.git microstrain_rtk_config
```

### Step 3: Install Dependencies
Ensure you have the required geodetic package installed on your system:
```bash
sudo apt-get update
sudo apt-get install -y libgeographiclib-dev
```
*(If you do not have root/sudo privileges, download and extract `libgeographiclib-dev` and `libgeographiclib26` deb packages locally to `~/local` as mapped in `scripts/start_rtk.sh`).*

### Step 4: Build the Workspace
```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

---

## Getting Started

### Step 1: Configure your NTRIP Caster Details
For security, `config/ntrip_client.yml` contains local credentials and is **ignored by Git** (via `.gitignore`). 

If you are cloning this repository on a new machine, first copy the template file:
```bash
cp config/ntrip_client.template.yml config/ntrip_client.yml
```
Then open `config/ntrip_client.yml` and fill in your actual RTK correction network details:
* `host`: The IP/Domain of your NTRIP service (e.g. `rtk2go.com` or a local/state network).
* `port`: The port (typically `2101`).
* `mountpoint`: The name of the RTK mountpoint.
* `username` and `password`.

---

## Running the Driver & RTK Client

You can start and configure the nodes using a **Graphical GUI**, a **Bash Script**, or native **ROS 2 CLI commands**.

### Option A: Graphical User Interface (GUI) (Recommended)
We provide an interactive Tkinter-based desktop interface to read, edit, and write the NTRIP caster parameters directly into your configuration. It also features buttons to start and stop the ROS 2 launch process and displays execution logs in real-time.

To run the GUI:
```bash
# Execute the GUI configurator from your workspace root
./configure_ntrip.py
```

### Option B: Script Interface
We provide a bash wrapper script that configures the workspace sourcing, path mappings for custom dependencies (such as local `GeographicLib` builds), and launches the system cleanly:

```bash
# Execute the start script directly from the package
./src/microstrain_rtk_config/scripts/start_rtk.sh
```

### Option C: Native ROS 2 Launch Interface
If you want to run it natively via `ros2 launch`, make sure to export any local dependency paths first, then run the launch file:

```bash
# Export the local GeographicLib paths (if not installed globally)
export CMAKE_PREFIX_PATH="/home/artwalk/local/usr/share/cmake/geographiclib:/home/artwalk/local/usr:${CMAKE_PREFIX_PATH}"
export LD_LIBRARY_PATH="/home/artwalk/local/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"

# Source the environments
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Run the python launch description
ros2 launch microstrain_rtk_config rtk_launch.py
```

---

## Verification

### 1. Verify RTK Correction Stream Status
You can verify if the RTK correction is active and successfully receiving data by echoing the correction status topic:
```bash
ros2 topic echo /mip/gnss_corrections/rtk_corrections_status
```
Look for positive connection indicator flags, low correction age (typically `< 2s`), and RTCM message reception.

### 2. Verify GPS Fix Quality
To check if the navigation filter has achieved centimeter-level accuracy ("RTK Fixed"):
```bash
ros2 topic echo /mip/gnss1/fix
```
Verify that the status indicates an RTK fix state (typically status value `4` or `5` depending on your message definition).
