import gymnasium as gym
from gymnasium import spaces
import numpy as np
import networkx as nx
from random import choice

class NetworkEnvOptic(gym.Env):

    def __init__(self) -> None:
        # define state space
        self.observation_space = spaces.Dict(
            {
                "links": spaces.Box(0, 1, shape=(878,), dtype=int), #878 possible routes total, 0 or 1 for if they are available or not
                "req_s": spaces.Discrete(13), #13 nodes (0-12)
                "req_d": spaces.Discrete(13),

            }
        )

        # define action space
        self.action_space = spaces.Discrete(879) #878 routes + block

        self.round = 0

    def _generate_req(self):
        # a request (indicating the capacity required to host this request)
        keys = list(self._nodes.keys())
        s = choice(keys)
        d = choice(keys)
        while s == d:
            d = choice(keys)
        
        min_ht = 10
        max_ht = 20
        ht = np.random.randint(min_ht, max_ht)
        return s,d,ht
    
    def _get_obs(self):
        return {
            "links": self._linkstates,
            "req_s": self._nodes[self._req_s],
            "req_d": self._nodes[self._req_d],
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self._G = nx.read_gml('nsfnet.gml')

        #get all paths
        self._edge_paths = []
        for node1 in self._G.nodes:
            for node2 in self._G.nodes:
                if node1 != node2:
                    for path in sorted(nx.all_simple_edge_paths(self._G,source=node1,target=node2)):
                        self._edge_paths.append(path)
        
        #get nodes as dictionary
        self._nodes = {}
        for i, node in enumerate(self._G.nodes):
            self._nodes[node] = i
        
        #initialize edge stats
        self._num_colors = 5
        self._edge_stats = {}
        for edge in self._G.edges:
            self._edge_stats[edge] = np.array([0] * self._num_colors)
        #print(f'\n\n\nedge stats: {self._edge_stats}\n\n\n')

        # to recover the original state 
        self._linkstates = np.array([1] * 878) #1 means open, 0 means closed

        # to generate a request 
        s,d,ht = self._generate_req()
        self._req_s = s
        self._req_d = d
        self._req_ht = ht

        self._num_good_choices = 0

        observation = self._get_obs()
        info = {
            "num_good_choices": self._num_good_choices,
        }

        self.round = 0

        return observation, info
    
    def update_edge_stats(self, path_index):
        #check which color to use
        chosen_color = -1
        for color in range(self._num_colors):
            color_available = True
            for edge in self._edge_paths[path_index]:
                edge_name = edge
                if edge_name not in self._edge_stats: #switch edges if they are flip flopped
                    edge_name = (edge_name[1], edge_name[0])
                if self._edge_stats[edge_name][color] != 0: #this color is not available
                    color_available = False
                    break #skip to next color
            
            if color_available: #the color is available, set it and move on
                chosen_color = color
                break


        #update holding times and get list of closed off edges after holding time updates
        closed_edges = []
        for edge,stats in self._edge_stats.items(): #go trhough each item in edge stats dictionary
            number_closed = 0 #tracks how many colors are closed for this edge
            for color,ht in enumerate(stats): #go through every color's stats in the edge
                if color == chosen_color and edge in self._edge_paths[path_index]: #this is one of the edges and colors on our route
                    self._edge_stats[edge][color] = self._req_ht #put holding time in it
                    number_closed += 1 #this color is now closed
                elif ht != 0: #if the current edge and color has a ht, decrement by 1
                    self._edge_stats[edge][color] -= 1
                    if self._edge_stats[edge][color] != 0: #color still closed after decrementing, add to number closed
                        number_closed += 1
            
            if number_closed == self._num_colors: #this edge is totally closed, add it to list
                closed_edges.append(edge)

        #look over all paths and update which ones are closed or open
        for i, path in  enumerate(self._edge_paths): #all paths in edge paths
            path_open = 1 #track state of path, 1 is open, 0 is closed
            for closed_edge in closed_edges: #each edge in current path
                if closed_edge in path: #there is a closed edge in this path, mark it and go to next path
                    path_open = 0
                    break
            self._linkstates[i] = path_open

        return
    
    def path_on_line(self, path_index, s, d): #need s and d as string, not ints
        text_path = self._edge_paths[path_index]
        if text_path[0][0] == s and text_path[-1][1] == d: #check if the first node in first edge in path and second node in last edge in path match s and d
            return True #it was correct, return true
        return False
    
    def step(self, action):
        
        # action = 0-877 (which path to choose), 878 (blocking)
        blocking_action = 878
        blocking_reward = -1
        auto_blocking_reward = -3 #we had to block it after it made a bad decision
        wrong_route_but_open_reward = -1
        wrong_route_and_closed_reward = -1
        good_path_reward = 5

        self.round += 1
        terminated = (self.round == 100) # True if it experienced 100 rounds

        reward = 0
        if action == blocking_action:
            # we need to block
            reward += blocking_reward
        else: # routing
            
            if self._linkstates[action] == 1: # the path it chose can map
                if (self.path_on_line(action, self._req_s, self._req_d)): #if the choice was even on current source and dest
                    #update the edge stats
                    self.update_edge_stats(action)
                    reward += good_path_reward
                    self._num_good_choices += 1
                else:
                    reward += wrong_route_but_open_reward
            else: # we need to block
                if (self.path_on_line(action, self._req_s, self._req_d) == False): #if the choice wasn't even on current source and dest
                    reward +=  wrong_route_and_closed_reward
                reward += auto_blocking_reward  
       
        # generate new request 
        s,d,ht = self._generate_req()
        self._req_s = s
        self._req_d = d
        self._req_ht = ht
        observation = self._get_obs()
        info = {
            "num_good_choices": self._num_good_choices,
        }

        return observation, reward, terminated, terminated, info 

