#!/usr/bin/env python3
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

import yaml


def load_ntrip_settings(config_path):
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    return data['ntrip_client']['ros__parameters']


def save_ntrip_settings(config_path, settings):
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    params = data['ntrip_client']['ros__parameters']
    for key, val in settings.items():
        if key == 'port':
            try:
                params[key] = int(val)
            except ValueError:
                raise ValueError('Port must be a valid integer.')
        elif key == 'authenticate':
            params[key] = str(val).lower() == 'true'
        else:
            params[key] = val
    with open(config_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)


def load_driver_settings(config_path):
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    return data['microstrain_inertial_driver']['ros__parameters']


def save_driver_settings(config_path, settings):
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    params = data['microstrain_inertial_driver']['ros__parameters']
    for key, val in settings.items():
        if key == 'imu_data_rate':
            try:
                params[key] = int(val)
            except ValueError:
                raise ValueError('IMU Data Rate must be a valid integer.')
        else:
            params[key] = val
    with open(config_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)


class NTRIPConfigurator(tk.Tk):

    def __init__(self, ntrip_config_path, gq7_config_path, gx5_config_path, start_script_path):
        super().__init__()
        self.ntrip_config_path = ntrip_config_path
        self.gq7_config_path = gq7_config_path
        self.gx5_config_path = gx5_config_path
        self.start_script_path = start_script_path
        self.script_dir = os.path.dirname(start_script_path)
        self.process = None

        self.title('MicroStrain Driver Settings')
        self.geometry('700x650')
        self.minsize(600, 550)

        # Style configurations
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Color Scheme (Sleek Dark Mode theme)
        self.configure(bg='#1e1e2e')
        self.style.configure('.', background='#1e1e2e', foreground='#cdd6f4')
        self.style.configure(
            'TLabel', background='#1e1e2e', foreground='#cdd6f4',
            font=('Helvetica', 11)
        )
        self.style.configure(
            'TEntry', fieldbackground='#313244', foreground='#cdd6f4',
            font=('Helvetica', 11)
        )
        self.style.configure(
            'Header.TLabel', font=('Helvetica', 14, 'bold'),
            foreground='#89b4fa'
        )

        # Button styling
        self.style.configure(
            'Save.TButton', background='#a6e3a1', foreground='#11111b',
            font=('Helvetica', 10, 'bold')
        )
        self.style.map('Save.TButton', background=[('active', '#94e2d5')])

        self.style.configure(
            'Run.TButton', background='#89b4fa', foreground='#11111b',
            font=('Helvetica', 10, 'bold')
        )
        self.style.map('Run.TButton', background=[('active', '#b4befe')])

        self.style.configure(
            'Stop.TButton', background='#f38ba8', foreground='#11111b',
            font=('Helvetica', 10, 'bold')
        )
        self.style.map('Stop.TButton', background=[('active', '#f9e2af')])

        self._build_ui()
        self._load_settings()

        self.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self, padding='20 20 20 20')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Label(
            main_frame, text='MicroStrain Device Configurations',
            style='Header.TLabel'
        )
        header.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky='w')

        # Device Selector Dropdown
        dev_label = ttk.Label(main_frame, text='Select Device / Driver:')
        dev_label.grid(row=1, column=0, sticky='w', pady=(0, 10))

        self.device_var = tk.StringVar(value='3DM-GQ7 (RTK)')
        self.device_combo = ttk.Combobox(
            main_frame, textvariable=self.device_var,
            values=['3DM-GQ7 (RTK)', '3DM-GX5-25 (IMU)'],
            state='readonly', width=33, exportselection=False
        )
        self.device_combo.grid(row=1, column=1, sticky='ew', pady=(0, 10), padx=(10, 0))
        self.device_combo.bind('<<ComboboxSelected>>', self._on_device_changed)

        # IMU Data Rate Selector Dropdown
        rate_label = ttk.Label(main_frame, text='IMU Data Rate (Hz):')
        rate_label.grid(row=2, column=0, sticky='w', pady=(0, 15))

        self.rate_var = tk.StringVar(value='100')
        self.rate_combo = ttk.Combobox(
            main_frame, textvariable=self.rate_var,
            values=['10', '50', '100', '200', '500'],
            state='readonly', width=33, exportselection=False
        )
        self.rate_combo.grid(row=2, column=1, sticky='ew', pady=(0, 15), padx=(10, 0))
        self.rate_combo.bind('<<ComboboxSelected>>', self._on_rate_changed)

        # Connection fields
        fields = [
            ('host', 'NTRIP Caster Host:'),
            ('port', 'Caster Port:'),
            ('mountpoint', 'Mountpoint:'),
            ('username', 'Username:'),
            ('password', 'Password:')
        ]

        self.entries = {}
        for idx, (key, label_text) in enumerate(fields):
            label = ttk.Label(main_frame, text=label_text)
            label.grid(row=idx+3, column=0, sticky='w', pady=5)

            show_char = '*' if key == 'password' else ''
            entry = ttk.Entry(main_frame, show=show_char, width=35)
            entry.grid(row=idx+3, column=1, sticky='ew', pady=5, padx=(10, 0))
            self.entries[key] = entry

        # Load / Save buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(
            row=len(fields)+3, column=0, columnspan=2, pady=20, sticky='ew'
        )

        self.save_btn = ttk.Button(
            btn_frame, text='Save Settings', style='Save.TButton',
            command=self._save_settings
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # ROS Launch control frame
        launch_frame = ttk.Frame(main_frame)
        launch_frame.grid(
            row=len(fields)+4, column=0, columnspan=2, pady=(0, 10), sticky='ew'
        )

        self.run_btn = ttk.Button(
            launch_frame, text='Start ROS 2 Launch', style='Run.TButton',
            command=self._start_launch
        )
        self.run_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(
            launch_frame, text='Stop Launch', style='Stop.TButton',
            command=self._stop_launch, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)

        # Scrolled Text for logs output
        log_label = ttk.Label(main_frame, text='ROS 2 Process Logs:')
        log_label.grid(
            row=len(fields)+5, column=0, columnspan=2, sticky='w',
            pady=(10, 5)
        )

        self.log_text = scrolledtext.ScrolledText(
            main_frame, height=12, bg='#11111b', fg='#a6e3a1',
            font=('Courier New', 10)
        )
        self.log_text.grid(
            row=len(fields)+6, column=0, columnspan=2, sticky='nsew',
            pady=(0, 10)
        )

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(len(fields)+6, weight=1)

    def _on_device_changed(self, event=None):
        selected = self.device_var.get()
        if selected == '3DM-GQ7 (RTK)':
            for entry in self.entries.values():
                entry.config(state=tk.NORMAL)
            self.start_script_path = os.path.join(self.script_dir, 'start_gq7.sh')
            # Load GQ7 data rate
            try:
                params = load_driver_settings(self.gq7_config_path)
                rate = params.get('imu_data_rate', 100)
                self.rate_var.set(str(rate))
            except Exception:
                self.rate_var.set('100')
        else:
            for entry in self.entries.values():
                entry.config(state=tk.DISABLED)
            self.start_script_path = os.path.join(self.script_dir, 'start_gx5.sh')
            # Load GX5 data rate
            try:
                params = load_driver_settings(self.gx5_config_path)
                rate = params.get('imu_data_rate', 100)
                self.rate_var.set(str(rate))
            except Exception:
                self.rate_var.set('100')

    def _on_rate_changed(self, event=None):
        selected = self.device_var.get()
        rate_val = self.rate_var.get().strip()

        # Automatically save settings
        try:
            if selected == '3DM-GQ7 (RTK)':
                save_driver_settings(self.gq7_config_path, {'imu_data_rate': rate_val})
            else:
                save_driver_settings(self.gx5_config_path, {'imu_data_rate': rate_val})
            self.log_text.insert(tk.END, f'Saved new IMU rate: {rate_val} Hz\n')
            self.log_text.see(tk.END)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save rate: {e}')
            return

        # If driver is running, restart/reset it
        if self.process:
            self.log_text.insert(tk.END, '\nIMU data rate changed. Resetting driver...\n')
            self.log_text.see(tk.END)
            self._stop_launch()
            # Give a brief delay for clean termination, then start launch again
            self.after(800, self._start_launch)

    def _load_settings(self):
        try:
            # 1. Load NTRIP settings
            params = load_ntrip_settings(self.ntrip_config_path)
            for key, entry in self.entries.items():
                val = params.get(key, '')
                entry.delete(0, tk.END)
                entry.insert(0, str(val))

            # 2. Load driver settings for the default device (GQ7)
            selected = self.device_var.get()
            config_path = self.gq7_config_path if selected == '3DM-GQ7 (RTK)' \
                else self.gx5_config_path
            d_params = load_driver_settings(config_path)
            rate = d_params.get('imu_data_rate', 100)
            self.rate_var.set(str(rate))
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load settings file:\n{e}')

    def _save_settings(self):
        try:
            selected = self.device_var.get()
            rate_val = self.rate_var.get().strip()

            if selected == '3DM-GQ7 (RTK)':
                # Save NTRIP settings
                ntrip_settings = {}
                for key, entry in self.entries.items():
                    ntrip_settings[key] = entry.get().strip()
                save_ntrip_settings(self.ntrip_config_path, ntrip_settings)

                # Save GQ7 driver settings (imu_data_rate)
                save_driver_settings(self.gq7_config_path, {'imu_data_rate': rate_val})
            else:
                # Save GX5 driver settings (imu_data_rate)
                save_driver_settings(self.gx5_config_path, {'imu_data_rate': rate_val})

            messagebox.showinfo('Saved', 'Settings successfully written to config!')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save settings:\n{e}')

    def _start_launch(self):
        if self.process:
            return

        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, 'Starting ROS 2 environment & launch file...\n')

        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # Run process in a separate background thread to prevent UI freezing
        self.thread = threading.Thread(target=self._run_process_loop, daemon=True)
        self.thread.start()

    def _run_process_loop(self):
        try:
            self.process = subprocess.Popen(
                [self.start_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create process group to allow full termination
            )

            # Keep reading stdout lines as they are produced
            for line in iter(self.process.stdout.readline, ''):
                self.log_text.insert(tk.END, line)
                self.log_text.see(tk.END)

            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.log_text.insert(tk.END, f'\nProcess startup failed: {e}\n')
        finally:
            self.process = None
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def _stop_launch(self):
        if self.process:
            self.log_text.insert(tk.END, '\nStopping launch process...\n')
            try:
                # Terminate the entire process group
                os.killpg(os.getpgid(self.process.pid), 9)
            except Exception as e:
                self.log_text.insert(tk.END, f'Failed to kill process: {e}\n')
            self.process = None
            # Allow a tiny pause for standard termination cleanup
            time.sleep(0.2)

    def _on_close(self):
        self._stop_launch()
        self.destroy()


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Resolve absolute paths
    config_dir = os.path.join(script_dir, '..', 'config')
    ntrip_config = os.path.join(config_dir, 'ntrip_client.yml')
    gq7_config = os.path.join(config_dir, 'microstrain.yml')
    gx5_config = os.path.join(config_dir, 'gx5.yml')
    start_script = os.path.join(script_dir, 'start_gq7.sh')

    if not os.path.exists(ntrip_config):
        print(f'Error: configuration file not found at {ntrip_config}')
        sys.exit(1)

    app = NTRIPConfigurator(ntrip_config, gq7_config, gx5_config, start_script)
    app.mainloop()
