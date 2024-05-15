import copy
import numpy as np
import gym
from gym import spaces

class DiscreteWrapper(gym.Env):
    def __init__(self, env, m, n):
        self._env = env
        self.m = m # Num of rows (i.e. height)
        self.n = n # Num of columns (i.e. width)

        self.action_space = spaces.Dict(
            {
                # Note that we are swapping the dimensions compared to the og env
                "pos": spaces.Box(low=np.array([0, 0]), high=np.array([m - 1, n - 1]), dtype=np.uint8),
            }
        )

    def reset(self):
        return self._env.reset()

    def _conv_pos(self, i, j):
        w, h = self._env._get_device_size()

        u = (i / self.m) * h
        d = ((i + 1) / self.m) * h
        cy = (u + d) // 2

        l = (j / self.n) * w
        r = ((j + 1) / self.n) * w
        cx = (l + r) // 2
        return (cx, cy)

    def step(self, action):
        action = copy.deepcopy(action)
        action["pos"] = self._conv_pos(*action["pos"])
        return self._env.step(action)

    def render(self):
        return self._env.render()
