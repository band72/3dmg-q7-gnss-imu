import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
import yaml


def launch_setup(context, *args, **kwargs):
    # Retrieve configuration paths
    config_pkg_dir = get_package_share_directory('microstrain_rtk_config')
    driver_pkg_dir = get_package_share_directory('microstrain_inertial_driver')

    # Default driver parameters file path
    default_driver_params_path = os.path.join(
        driver_pkg_dir,
        'microstrain_inertial_driver_common',
        'config',
        'params.yml'
    )

    # Custom driver parameters override path
    custom_driver_params_path = os.path.join(
        config_pkg_dir,
        'config',
        'microstrain.yml'
    )

    # NTRIP client parameters path
    ntrip_params_path = os.path.join(
        config_pkg_dir,
        'config',
        'ntrip_client.yml'
    )

    # Load driver parameters from YAML
    with open(default_driver_params_path, 'r') as f:
        driver_params = yaml.safe_load(f)
    with open(custom_driver_params_path, 'r') as f:
        driver_overrides = yaml.safe_load(f)

    # Merge overrides into default parameters
    driver_params_dict = {}
    if 'microstrain_inertial_driver' in driver_params:
        driver_params_dict.update(
            driver_params['microstrain_inertial_driver']['ros__parameters']
        )
    if 'microstrain_inertial_driver' in driver_overrides:
        driver_params_dict.update(
            driver_overrides['microstrain_inertial_driver']['ros__parameters']
        )

    # Nodes definition
    driver_node = Node(
        package='microstrain_inertial_driver',
        executable='microstrain_inertial_driver_node',
        name='gq7_driver',
        output='screen',
        parameters=[driver_params_dict]
    )

    # Decide whether to launch the NTRIP client node based on configuration
    nodes_to_launch = [driver_node]
    if driver_params_dict.get('ntrip_interface_enable', False):
        ntrip_node = Node(
            package='ntrip_client',
            executable='ntrip_ros.py',
            name='ntrip_client',
            output='screen',
            parameters=[ntrip_params_path]
        )
        nodes_to_launch.append(ntrip_node)

    return nodes_to_launch


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])
