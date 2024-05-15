import cv2
import gym
import numpy as np
import tempfile
import time
import re
from android_env.simple.controller import AndroidController
from gym import spaces

class AndroidGymEnvironment(gym.Env):
    def __init__(self, device, reward_terminate_fn, reset_cmds, app=None):
        self.device = device
        self.reward_terminate_fn = reward_terminate_fn # Takes as input an iterator of the log. Returns reward and whether to terminate based on log.
        self.reset_cmds = reset_cmds # List of functions that take the android controller as input, ran when reset is called on environment.
        self.app = app
        self.android_controller = AndroidController(self.device)

        self.reset()

        self.observation_space = spaces.Dict(
            {
                "image": spaces.Box(low=0, high=255, shape=(self.android_controller.height, self.android_controller.width, 3)),
            }
        )

        self.action_space = spaces.Dict(
            {
                "pos": spaces.Box(low=np.array([0, 0]), high=np.array([self.android_controller.width, self.android_controller.height]), dtype=np.int32),
            }
        )

    def _get_device_size(self):
        return self.android_controller.get_device_size()

    def _get_obs(self):
        ret = {}

        # Sleep to wait for action effect
        time.sleep(1)

        # First get image
        f = tempfile.NamedTemporaryFile()
        path = f.name
        self.android_controller.get_screenshot(path)
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        ret["image"] = img

        return ret

    def _get_reward_terminate(self):
        return self.reward_terminate_fn(self.android_controller.get_log())

    def reset(self):
        self.android_controller.home()
        self.android_controller.execute_adb_command("logcat -c") # Clear out logs
        for reset_cmd in self.reset_cmds:
            self.android_controller.execute_adb_command(reset_cmd)
        if self.app:
            self.android_controller.open_app(self.app)
        return self._get_obs()

    def step(self, action):
        # Penalize and terminate if we are not in the right app
        if self.app:
            window_dump_lines = self.android_controller.execute_adb_command("shell dumpsys window windows").split('\n')
            good = False
            for line in window_dump_lines:
                if re.search(re.escape(self.app), line, re.IGNORECASE) and "mObscuringWindow" in line:
                    good = True
            if not good:
                return self._get_obs(), -1000, True, {}

        pos = tuple(action["pos"])
        self.android_controller.tap(pos)

        observation = self._get_obs()
        reward, terminated = self._get_reward_terminate()
        info = {}

        return observation, reward, terminated, info

    def render(self):
        return self._get_obs()["image"]
