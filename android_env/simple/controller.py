import subprocess
import os
import time

def execute_command(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print(f"Error executing {cmd}.")
    return None

def list_devices():
    ret = execute_command("adb devices")
    return list(map(lambda z: z.split()[0], ret.split("\n")[1:]))

class AndroidController:
    def __init__(self, device):
        self.device = device
        self.width, self.height = self.get_device_size()
        self.init_log_process()

    def execute_adb_command(self, cmd):
        return execute_command(f"adb -s {self.device} {cmd}")

    def init_log_process(self):
        self.execute_adb_command("logcat -c") # Clear out old logs
        self.log_process = subprocess.Popen(["adb", "-s", self.device, "logcat"], stdout=subprocess.PIPE)
        os.set_blocking(self.log_process.stdout.fileno(), False) # To make readline from log process non-blocking

    def get_device_size(self):
        ret = self.execute_adb_command("shell wm size")
        return tuple(map(int, ret.split(": ")[1].split("x")))

    def get_log(self):
        for line in iter(lambda: self.log_process.stdout.readline(), b''):
            yield line.decode().strip()

    def get_screenshot(self, path):
        return self.execute_adb_command(f"exec-out screencap -p > {path}")

    def open_app(self, app):
        return self.execute_adb_command(f"shell monkey -p {app} 1")

    def home(self):
        return self.execute_adb_command("shell input keyevent KEYCODE_HOME")

    def back(self):
        return self.execute_adb_command("shell input keyevent KEYCODE_BACK")

    def tap(self, pos):
        return self.execute_adb_command(f"shell input tap {pos[0]} {pos[1]}")
