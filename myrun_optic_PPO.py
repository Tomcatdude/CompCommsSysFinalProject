#running on python 3.8.10 with ray version 2.20

# RL algorithm
from ray.rllib.algorithms.ppo import PPOConfig
import ray
# to use a custom env
from ray.tune.registry import register_env

# my custom env
from net_env_optic_2_random_route import NetworkEnvOptic #choose for random routes
#from net_env_optic_2_single_route import NetworkEnvOptic #choose for single route
import numpy as np

# Just to suppress
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

ray.init()

# registering my custom env with a name "netenv-v0" 
def env_creator(env_config):
    return NetworkEnvOptic()

register_env('netenv-v0', env_creator)
#ray.rllib.utils.check_env(NetworkEnvOptic()) #check enviornment before running


# Set up RL 
config = (PPOConfig()
          .training(gamma=0.0, lr=0.003)
          .environment(env='netenv-v0')
          .resources(num_gpus=1)
        )

algo = config.build()

for i in range(15):
    print(f'iteration: {i}')
    results = algo.train()
    #baseline.train()
    print(f'episode reward mean: {results["episode_reward_mean"]}')
    print(f'episode rewards: {results["hist_stats"]["episode_reward"]}')
    