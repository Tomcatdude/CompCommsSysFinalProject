import gymnasium as gym
from gymnasium import spaces
import numpy as np

class NetworkEnv(gym.Env):

    def __init__(self) -> None:
        # define state space
        self.observation_space = spaces.Dict(
            {
                "links": spaces.Box(0, 5, shape=(3,), dtype=int),
                "req": spaces.Box(1, 3, shape=(1,), dtype=int)    
            }
        )

        # define action space
        self.action_space = spaces.Discrete(4)

        self.round = 0

    def _generate_req(self):
        # a request (indicating the capacity required to host this request)
        return np.array([np.random.randint(1, 3+1),])
    
    def _get_obs(self):
        return {
            "links": self._linkstates,
            "req": self._req,
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # to recover the original state (empty)
        self._linkstates = np.array([0] * 3)

        # to generate a request 
        self._req = self._generate_req()

        observation = self._get_obs()
        info = {}

        self.round = 0

        return observation, info

    def step(self, action):
        # action = 0 (P0), 1 (P1), 2 (P2), 3 (blocking)
        # if we have enough capacity to host the req on the selected path
        # self._req[0]: requested capacity         
        blocking_action = 3
        blocking_reward = -1

        self.round += 1
        terminated = (self.round == 8) # True if it experienced 8 rounds

        if action == blocking_action:
            #print("blocked")
            # we need to block
            reward = blocking_reward
        else: # routing
            num_occupied_slots = self._linkstates[action] + self._req[0]
            if num_occupied_slots <= 5: # we can map
                #print("mapped")
                self._linkstates[action] = num_occupied_slots
                reward = +1 * self._req[0]   
            else: # we need to block
                #print("blocked after choice")
                reward = blocking_reward  
       
        self._req = self._generate_req()
        observation = self._get_obs()
        info = {}

        return observation, reward, terminated, terminated, info 

