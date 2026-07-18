import os
import sys
import tempfile
import unittest

from ament_index_python.packages import get_package_share_directory
import yaml

# Resolve share directory to load the script from install space
package_share = get_package_share_directory('microstrain_rtk_config')
scripts_path = os.path.join(package_share, 'scripts')
sys.path.insert(0, scripts_path)

# noqa: E402, I100, I101
from configure_ntrip import (  # noqa: E402, I100, I101
    load_driver_settings,
    load_ntrip_settings,
    save_driver_settings,
    save_ntrip_settings
)


class TestNTRIPConfig(unittest.TestCase):

    def setUp(self):
        # Create a temporary config file for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, 'ntrip_client.yml')
        self.driver_config_path = os.path.join(self.test_dir.name, 'gx5.yml')

        self.initial_data = {
            'ntrip_client': {
                'ros__parameters': {
                    'host': 'initial.host.com',
                    'port': 2101,
                    'mountpoint': 'TEST',
                    'authenticate': True,
                    'username': 'user',
                    'password': 'password'
                }
            }
        }
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.initial_data, f)

        self.initial_driver_data = {
            'microstrain_inertial_driver': {
                'ros__parameters': {
                    'port': '/dev/microstrain_main',
                    'baudrate': 115200,
                    'imu_data_rate': 100
                }
            }
        }
        with open(self.driver_config_path, 'w') as f:
            yaml.safe_dump(self.initial_driver_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_settings(self):
        params = load_ntrip_settings(self.config_path)
        self.assertEqual(params['host'], 'initial.host.com')
        self.assertEqual(params['port'], 2101)
        self.assertEqual(params['mountpoint'], 'TEST')
        self.assertTrue(params['authenticate'])

    def test_save_settings_valid(self):
        new_settings = {
            'host': 'new.host.com',
            'port': '20000',
            'mountpoint': 'NEW_MOUNT',
            'authenticate': 'False',
            'username': 'new_user',
            'password': 'new_password'
        }
        save_ntrip_settings(self.config_path, new_settings)

        # Verify saved data
        params = load_ntrip_settings(self.config_path)
        self.assertEqual(params['host'], 'new.host.com')
        self.assertEqual(params['port'], 20000)  # Should be cast to int
        self.assertEqual(params['mountpoint'], 'NEW_MOUNT')
        self.assertFalse(params['authenticate'])  # Should be cast to bool
        self.assertEqual(params['username'], 'new_user')
        self.assertEqual(params['password'], 'new_password')

    def test_save_settings_invalid_port(self):
        invalid_settings = {
            'port': 'not_an_int'
        }
        with self.assertRaises(ValueError):
            save_ntrip_settings(self.config_path, invalid_settings)

    def test_load_driver_settings(self):
        params = load_driver_settings(self.driver_config_path)
        self.assertEqual(params['port'], '/dev/microstrain_main')
        self.assertEqual(params['baudrate'], 115200)
        self.assertEqual(params['imu_data_rate'], 100)

    def test_save_driver_settings_valid(self):
        new_driver_settings = {
            'imu_data_rate': '200'
        }
        save_driver_settings(self.driver_config_path, new_driver_settings)

        params = load_driver_settings(self.driver_config_path)
        self.assertEqual(params['imu_data_rate'], 200)  # Should be cast to int
        self.assertEqual(params['port'], '/dev/microstrain_main')  # Unchanged

    def test_save_driver_settings_invalid_rate(self):
        invalid_driver_settings = {
            'imu_data_rate': 'not_an_int'
        }
        with self.assertRaises(ValueError):
            save_driver_settings(self.driver_config_path, invalid_driver_settings)


if __name__ == '__main__':
    unittest.main()
