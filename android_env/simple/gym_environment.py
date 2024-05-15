import controller
import cv2
import gym
import numpy as np
import tempfile
import time
from gym import spaces

class AndroidGymEnvironment(gym.Env):
    def __init__(self, device, reward_fn, reset_cmds, app=None):
        self.device = device
        self.reward_fn = reward_fn # Takes as input an iterator of the log. Returns reward based on log.
        self.reset_cmds = reset_cmds # List of functions that take the android controller as input, ran when reset is called on environment.
        self.app = app
        self.android_controller = controller.AndroidController(self.device)

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

    def _get_reward(self):
        return self.reward_fn(self.android_controller.get_log())

    def reset(self):
        self.android_controller.home()
        self.android_controller.execute_adb_command("logcat -c") # Clear out logs
        for reset_cmd in self.reset_cmds:
            self.android_controller.execute_adb_command(reset_cmd)
        if self.app:
            self.android_controller.open_app(self.app)
        return self._get_obs()

    def step(self, action):
        pos = tuple(action["pos"])
        self.android_controller.tap(pos)

        observation = self._get_obs()
        reward = self._get_reward()
        terminated = False
        info = {}

        return observation, reward, terminated, info

    def render(self):
        return self._get_obs()["image"]
