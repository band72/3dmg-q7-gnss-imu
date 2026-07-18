#!/usr/bin/env python3
import os
import sys
import yaml
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class NTRIPConfigurator(tk.Tk):
    def __init__(self, config_path, start_script_path):
        super().__init__()
        self.config_path = config_path
        self.start_script_path = start_script_path
        self.process = None

        self.title("MicroStrain GQ7 RTK Settings")
        self.geometry("700x550")
        self.minsize(600, 450)

        # Style configurations
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Color Scheme (Sleek Dark Mode theme)
        self.configure(bg="#1e1e2e")
        self.style.configure(".", background="#1e1e2e", foreground="#cdd6f4")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Helvetica", 11))
        self.style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4", font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground="#89b4fa")
        
        # Button styling
        self.style.configure("Save.TButton", background="#a6e3a1", foreground="#11111b", font=("Helvetica", 10, "bold"))
        self.style.map("Save.TButton", background=[("active", "#94e2d5")])

        self.style.configure("Run.TButton", background="#89b4fa", foreground="#11111b", font=("Helvetica", 10, "bold"))
        self.style.map("Run.TButton", background=[("active", "#b4befe")])

        self.style.configure("Stop.TButton", background="#f38ba8", foreground="#11111b", font=("Helvetica", 10, "bold"))
        self.style.map("Stop.TButton", background=[("active", "#f9e2af")])

        self._build_ui()
        self._load_settings()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Label(main_frame, text="3DM-GQ7 NTRIP Configuration", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Connection fields
        fields = [
            ("host", "NTRIP Caster Host:"),
            ("port", "Caster Port:"),
            ("mountpoint", "Mountpoint:"),
            ("username", "Username:"),
            ("password", "Password:")
        ]

        self.entries = {}
        for idx, (key, label_text) in enumerate(fields):
            label = ttk.Label(main_frame, text=label_text)
            label.grid(row=idx+1, column=0, sticky="w", pady=5)
            
            show_char = "*" if key == "password" else ""
            entry = ttk.Entry(main_frame, show=show_char, width=35)
            entry.grid(row=idx+1, column=1, sticky="ew", pady=5, padx=(10, 0))
            self.entries[key] = entry

        # Load / Save buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20, sticky="ew")

        save_btn = ttk.Button(btn_frame, text="Save Settings", style="Save.TButton", command=self._save_settings)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # ROS Launch control frame
        launch_frame = ttk.Frame(main_frame)
        launch_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=(0, 10), sticky="ew")

        self.run_btn = ttk.Button(launch_frame, text="Start ROS 2 RTK Launch", style="Run.TButton", command=self._start_launch)
        self.run_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(launch_frame, text="Stop Launch", style="Stop.TButton", command=self._stop_launch, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # Scrolled Text for logs output
        log_label = ttk.Label(main_frame, text="ROS 2 Process Logs:")
        log_label.grid(row=len(fields)+3, column=0, columnspan=2, sticky="w", pady=(10, 5))

        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, bg="#11111b", fg="#a6e3a1", font=("Courier New", 10))
        self.log_text.grid(row=len(fields)+4, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(len(fields)+4, weight=1)

    def _load_settings(self):
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            params = data['ntrip_client']['ros__parameters']
            for key, entry in self.entries.items():
                val = params.get(key, "")
                entry.delete(0, tk.END)
                entry.insert(0, str(val))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings file:\n{e}")

    def _save_settings(self):
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)

            params = data['ntrip_client']['ros__parameters']
            
            # Save parameters back, casting port to int
            for key, entry in self.entries.items():
                val = entry.get().strip()
                if key == "port":
                    try:
                        params[key] = int(val)
                    except ValueError:
                        raise ValueError("Port must be a valid integer.")
                elif key == "authenticate":
                    params[key] = val.lower() == "true"
                else:
                    params[key] = val

            with open(self.config_path, 'w') as f:
                yaml.safe_dump(data, f, default_flow_style=False)

            messagebox.showinfo("Saved", "Settings successfully written to config!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def _start_launch(self):
        if self.process:
            return

        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "Starting ROS 2 environment & launch file...\n")
        
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
                preexec_fn=os.setsid # Create process group to allow full termination
            )

            # Keep reading stdout lines as they are produced
            for line in iter(self.process.stdout.readline, ''):
                self.log_text.insert(tk.END, line)
                self.log_text.see(tk.END)
            
            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.log_text.insert(tk.END, f"\nProcess startup failed: {e}\n")
        finally:
            self.process = None
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def _stop_launch(self):
        if self.process:
            self.log_text.insert(tk.END, "\nStopping launch process...\n")
            try:
                # Terminate the entire process group (including subprocesses of start_rtk.sh)
                os.killpg(os.getpgid(self.process.pid), 9)
            except Exception as e:
                self.log_text.insert(tk.END, f"Failed to kill process: {e}\n")
            self.process = None

    def _on_close(self):
        self._stop_launch()
        self.destroy()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Resolve absolute paths
    config_file = os.path.join(script_dir, "..", "config", "ntrip_client.yml")
    start_script = os.path.join(script_dir, "start_rtk.sh")
    
    if not os.path.exists(config_file):
        print(f"Error: configuration file not found at {config_file}")
        sys.exit(1)
        
    app = NTRIPConfigurator(config_file, start_script)
    app.mainloop()
