#!/usr/bin/env bash

# Resolve the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

echo "========================================="
# Check if the specific device symlink exists
if [ ! -e "/dev/microstrain_main_6253.114065" ]; then
    echo "WARNING: /dev/microstrain_main_6253.114065 not found."
    echo "Will attempt to use standard fallback if available."
fi
echo " Starting MicroStrain GX5-25 Driver Node "
echo "========================================="

# 1. Source ROS 2 base environment
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    echo "Sourcing ROS 2 Jazzy..."
    source /opt/ros/jazzy/setup.bash
else
    echo "ERROR: ROS 2 Jazzy installation not found at /opt/ros/jazzy/setup.bash" >&2
    exit 1
fi

# 2. Configure environment paths for local GeographicLib dependency
export CMAKE_PREFIX_PATH="/home/artwalk/local/usr/share/cmake/geographiclib:/home/artwalk/local/usr:${CMAKE_PREFIX_PATH}"
export LD_LIBRARY_PATH="/home/artwalk/local/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"

# 3. Locate and source local colcon workspace
WS_DIR=""
if [ -f "${SCRIPT_DIR}/install/setup.bash" ]; then
    WS_DIR="${SCRIPT_DIR}"
elif [ -f "${SCRIPT_DIR}/../../../install/setup.bash" ]; then
    WS_DIR="$(cd "${SCRIPT_DIR}/../../.." &>/dev/null && pwd)"
elif [ -f "${SCRIPT_DIR}/../../../../install/setup.bash" ]; then
    WS_DIR="$(cd "${SCRIPT_DIR}/../../../.." &>/dev/null && pwd)"
fi

if [ -n "${WS_DIR}" ]; then
    echo "Sourcing local workspace from ${WS_DIR}..."
    source "${WS_DIR}/install/setup.bash"
else
    echo "ERROR: Workspace build files (install/setup.bash) not found. Run 'colcon build' first." >&2
    exit 1
fi

# 4. Configure FastDDS to disable shared memory transport (avoiding multi-user permission issues)
export FASTRTPS_DEFAULT_PROFILES_FILE="${WS_DIR}/fastdds_no_shm.xml"

# 5. Launch the GX5 system
echo "Running launch file..."
ros2 launch microstrain_rtk_config gx5_launch.py
