#running on python 3.10 with ray version 2.20

# RL algorithm
from ray.rllib.algorithms.ppo import PPOConfig
import ray
# to use a custom env
from ray.tune.registry import register_env

# my custom env
from net_env import NetworkEnv
import numpy as np

# Just to suppress
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

ray.init()

# registering my custom env with a name "netenv-v0" 
def env_creator(env_config):
    return NetworkEnv()

register_env('netenv-v0', env_creator)


# Set up RL 
config = (PPOConfig()
          .training(gamma=0.999, lr=0.001)
          .environment(env='netenv-v0')
          .resources(num_gpus=0)
        )

algo = config.build()


blconfig = (PPOConfig()
          .training(gamma=0.999, lr=0.0)
          .environment(env='netenv-v0')
          .resources(num_gpus=0)
        )

baseline = blconfig.build()

for i in range(10):
    results = algo.train()
    baseline.train()
    print(f'iteration: {i}')
    print(f'episode reward mean: {results["episode_reward_mean"]}')