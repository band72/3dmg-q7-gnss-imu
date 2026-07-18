# 3DM-GQ7-GNSS/INS RTK ROS 2 Configuration

This repository contains the custom ROS 2 configuration package (`microstrain_rtk_config`) to orchestrate centimeter-level RTK updates for the **MicroStrain 3DM-GQ7-GNSS/INS** IMU.

It launchs the official `microstrain_inertial_driver` and `ntrip_client` nodes in harmony, handling:
* Auxiliary port RTCM corrections input.
* NMEA GGA sentence feedback back to the NTRIP caster for Virtual Reference Station (VRS) support.

## Package Structure

* `config/microstrain.yml`: Driver parameters tailored for GQ7 serial ports, RTK interface, and NMEA outputs.
* `config/ntrip_client.yml`: Connection parameters template for your NTRIP correction service.
* `launch/rtk_launch.py`: Unified launch description starting both nodes.

## Instructions for Use

### Step 1: Configure your NTRIP Caster Details
Open `config/ntrip_client.yml` and fill in your RTK base station/correction network details:
* `host`: The IP/Domain of your NTRIP service (e.g. `rtk2go.com` or a local/state network).
* `port`: The port (typically `2101`).
* `mountpoint`: The name of the RTK mountpoint.
* `username` and `password`.

### Step 2: Source and Launch
Source your ROS 2 workspace and run the unified launch file:
```bash
source /opt/ros/jazzy/setup.bash
source <path_to_your_workspace>/install/setup.bash
ros2 launch microstrain_rtk_config rtk_launch.py
```

### Step 3: Verify RTK Correction Status
You can verify if the RTK correction is active and receiving updates by echoing the correction status topic:
```bash
ros2 topic echo /mip/gnss_corrections/rtk_corrections_status
```
You should see fields indicating the connection status, correction age, and correction type.
Additionally, you can monitor the GPS fix quality (which should go to "RTK Fixed" or status `4`/`5` depending on format) on:
```bash
ros2 topic echo /mip/gnss1/fix
```
