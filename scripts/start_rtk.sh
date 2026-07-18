#!/usr/bin/env bash

# Resolve the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../../.." &>/dev/null && pwd)"

echo "========================================="
echo " Starting MicroStrain GQ7 RTK ROS 2 Node "
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

# 3. Source local colcon workspace
if [ -f "${WORKSPACE_DIR}/install/setup.bash" ]; then
    echo "Sourcing local workspace..."
    source "${WORKSPACE_DIR}/install/setup.bash"
else
    echo "ERROR: Workspace build files not found at ${WORKSPACE_DIR}/install/setup.bash. Run 'colcon build' first." >&2
    exit 1
fi

# 4. Launch the unified RTK system
echo "Running launch file..."
ros2 launch microstrain_rtk_config rtk_launch.py
