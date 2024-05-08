import gymnasium as gym
from gymnasium import spaces
import numpy as np
import networkx as nx
from random import choice
from csv import writer

class NetworkEnvOptic(gym.Env):

    def __init__(self) -> None:
        # define state space
        self.observation_space = spaces.Dict(
            {
                "long_available": spaces.Discrete(2), #(long paths availble), 0 for no paths, 1 for one or more paths
                "short_available": spaces.Discrete(2),  #(short paths available), 0 for no paths, 1 for one or more paths
                "no_path_available": spaces.Discrete(2), #(no paths available), 0 for are paths, 1 for no paths

            }
        )

        # define action space
        self.action_space = spaces.Discrete(3) #short, long, blocking

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
            "long_available": self._current_short,
            "short_available": self._current_long,
            "no_path_available": self._current_no_path,
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        #max number of requests
        self._max_T = 100

        #set up file to write to csv
        self._file_name = 'results.csv'

        #initialize total reward
        self._total_reward = 0

        self._G = nx.read_gml('nsfnet.gml')

        #get all paths
        self._edge_paths = []
        for node1 in self._G.nodes:
            for node2 in self._G.nodes:
                if node1 != node2:
                    for path in sorted(nx.all_simple_edge_paths(self._G,source=node1,target=node2)):
                        self._edge_paths.append(path)
        
        #initialize utilization
        self._utilization = 0

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
        self._pathstates = np.array([1] * 878) #1 means open, 0 means closed

        # to generate a request 
        s,d,ht = self._generate_req()
        self._req_s = s
        self._req_d = d
        self._req_ht = ht

        self._short_threshold = 2
        self._short_paths, self._long_paths = self._get_short_and_long_paths(s,d)

        self._current_short = int(len(self._short_paths) > 0) #true if we have one or more
        self._current_long = int(len(self._long_paths) > 0) #true if we have one or more
        self._current_no_path = int((self._current_short+self._current_long) == 0) #true if both are 0
        
        self._num_good_choices = 0

        observation = self._get_obs()
        info = {
            "num_good_choices": self._num_good_choices,
        }

        self.round = 0

        return observation, info
    
    def _update_edge_stats(self, action):
        if action != "update": #if we are adding a new request, rather than just updating holding times
            if action == "short":
                path_index = self._short_paths[0] #just set it to the first short path
            elif action == "long":
                path_index = self._long_paths[0] #just set it to the first long path
            else:
                print("ERROR: bad action")
                return
            #check which color to use
            chosen_color = -1
            for color in range(self._num_colors):
                color_available = True
                for edge in self._edge_paths[path_index]: #check each edge in the path specified by path_index
                    edge_name = edge
                    if edge_name not in self._edge_stats: #switch edges if they are flip flopped
                        edge_name = (edge_name[1], edge_name[0])
                    if self._edge_stats[edge_name][color] != 0: #this color is not available
                        color_available = False
                        break #skip to next color
                
                if color_available: #the color is available, set it and move on
                    chosen_color = color
                    break
        else:
            chosen_color = -1 #set chosen_color to -1, so we will never run the if color == chosen_color line in update holding times

        
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
            self._pathstates[i] = path_open

        return
    
    def _get_short_and_long_paths(self, s, d):
        short_paths = []
        long_paths = []
        for i, state in enumerate(self._pathstates): #for every path
            if state == 1 and self._path_on_line(i, s, d): #if this path is open and goes from s to d
                if len(self._edge_paths[i]) <= self._short_threshold: #it's a short path
                    short_paths.append(i)
                else: #it's a long path
                    long_paths.append(i)
        return short_paths, long_paths


    #returns true if the path given by path_index starts at s and ends at d
    def _path_on_line(self, path_index, s, d): #need s and d as string, not ints
        text_path = self._edge_paths[path_index]
        if text_path[0][0] == s and text_path[-1][1] == d: #check if the first node in first edge in path and second node in last edge in path match s and d
            return True #it was correct, return true
        return False
    
    #adds the amount of currently utilized edges to the utilization score (we will use divide by 5, 100, and 15 later to get network-wide utilization)
    def _update_utilization(self):
        for edge,stats in self._edge_stats.items(): #go trhough each item in edge stats dictionary
            for color,ht in enumerate(stats): #go through every color's stats in the edge
                if ht > 0:
                    self._utilization += 1

    
    def step(self, action):
        
        # action = 0(short path), 1(long path), 2(blocking)
        blocking_action = 2
        #rewards
        blocking_reward = -1
        no_path_reward = -2 #we had to block it after it made a bad decision
        short_reward = 3
        long_reward = 2

        self.round += 1
        terminated = (self.round == self._max_T) # True if it experienced 100 rounds

        reward = 0
        if action == blocking_action:
            # we need to block
            reward += blocking_reward
            self._update_edge_stats("update")
        else: # routing
            if action == 0: #action is short path
                if self._current_short == 1: #we do have short paths
                    reward += short_reward
                    self._update_edge_stats("short")
                else: #we don't have short paths
                    reward += no_path_reward
                    self._update_edge_stats("update")
            else: #action is long path
                if self._current_long == 1: #we do have long paths
                    reward += long_reward
                    self._update_edge_stats("long")
                else: #we don't have long paths
                    reward += no_path_reward
                    self._update_edge_stats("update")

        self._total_reward += reward
       
        # generate new request 
        s,d,ht = self._generate_req()
        self._req_s = s
        self._req_d = d
        self._req_ht = ht

        self._update_utilization()

        #get paths
        self._short_paths, self._long_paths = self._get_short_and_long_paths(s,d)

        #set observations
        self._current_short = int(len(self._short_paths) > 0) #true if we have one or more
        self._current_long = int(len(self._long_paths) > 0) #true if we have one or more
        self._current_no_path = int((self._current_short+self._current_long) == 0) #true if both are 0

        observation = self._get_obs()
        info = {
            "num_good_choices": self._num_good_choices,
        }

        if terminated:
            #divide by whatever, sum, add to csv
            total_utilization = self._utilization
            total_utilization /= (self._num_colors*self._max_T*len(self._edge_stats))

            average_reward = self._total_reward/self._max_T

            row = [total_utilization, average_reward]

            print(f'\n\ntotal utilization: {total_utilization} avg reward: {average_reward}\n\n')
            with open(self._file_name, 'a+', newline='') as write_obj:
                csv_writer = writer(write_obj)
                csv_writer.writerow(row)

        return observation, reward, terminated, terminated, info 

