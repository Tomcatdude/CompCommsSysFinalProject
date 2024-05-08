#by tom odem, from code template given by Dr. Genya
#on 17 april 2024

"""
problems with code given to us:
EdgeStats __str__ has no reqs, yet uses it ; line 42 in original
no need for slots in EdgeStats ; line 37 in original
don't need g: nx.Graph in generate requests ; line 69 in original
"""

import networkx as nx
import numpy as np
import random
import matplotlib.pyplot as plt

class Request:
    """This class represents a request. Each request is characterized by source and destination nodes and holding time (represented by an integer).

    The holding time of a request is the number of time slots for this request in the network. You should remove a request that exhausted its holding time.
    """

    def __init__(self, s, t, ht):
        self.s = s
        self.t = t
        self.ht = ht

    def __str__(self) -> str:
        return f'req({self.s}, {self.t}, {self.ht})'
    
    def __repr__(self) -> str:
        return self.__str__()
        
    def __hash__(self) -> int:
        # used by set()
        return self.id


class EdgeStats:
    """This class saves all state information of the system. In particular, the remaining capacity after request mapping and a list of mapped requests should be stored.
    """
    def __init__(self, u, v, cap) -> None:
        self.id = (u,v)
        self.u = u
        self.v = v 
        # remaining capacity
        self.cap = cap 

        # spectrum state (a list of requests, showing color <-> request mapping). Each index of this list represents a color
        self.__slots = [None] * cap
        # a list of the remaining holding times corresponding to the mapped requests
        self.__hts = [0] * cap

    def __str__(self) -> str:
        return f'{self.id}, cap = {self.cap}'
    
    def add_request(self, req: Request, color:int):
        """update self.__slots by adding a request to the specific color slot

        Args:
            req (Request): a request
            color (int): a color to be used for the request
        """

        self.__hts[color] = req.ht
       
        return

    def remove_requests(self):
        """update self.__slots by removing the leaving requests based on self.__hts; Also, self.__hts should be updated in this function.
        """
        self.__hts = [(holding_time-1) if holding_time > 0 else 0 for holding_time in self.__hts] #decrement each holding time, unless it is already free (0)

        return

    def get_available_colors(self) -> list[int]:
        """return a list of integers available to accept requests
        """
        return list(np.where(np.array(self.__hts) == 0)[0]) #find indexes of where the holding time is 0 (free), then turn back into list from numpy array
    
    def show_spectrum_state(self):
        """Come up with a representation to show the utilization state of a link (by colors)
        """
        return (5-len(self.get_available_colors()))/5
    

def generate_requests(num_reqs: int) -> list[Request]:
    """Generate a set of requests, given the number of requests and an optical network (topology)

    Args:
        num_reqs (int): the number of requests
        g (nx.Graph): network topology

    Returns:
        list[Request]: a list of request instances
    """

    min_ht = 4
    max_ht = 10
    #requests = [Request(0,4,random.randint(min_ht,max_ht)) for _ in range(num_reqs)] #for setting destination to 4
    #requests = [Request(0,np.random.randint(1,5),random.randint(min_ht,max_ht)) for _ in range(num_req)] #for finding random destination
    
    #a4 assignment review
    requests = [
        Request(0,4,4), #1
        Request(0,4,4), #2
        Request(0,4,4), #3
        Request(0,4,10), #4
        Request(0,4,10), #5
        Request(0,4,10), #6
        Request(0,4,10), #7
        Request(0,4,10), #8
        Request(0,4,10), #9
        Request(0,4,10), #10
        Request(0,4,10), #11
        Request(0,4,10), #12
        Request(0,4,10), #13
    ]

    return requests


def generate_graph() -> nx.Graph:
    """Generate a networkx graph instance importing a GML file. Set the capacity attribute to all links based on a random distribution.

    Returns:
        nx.Graph: a weighted graph
    """

    G = nx.Graph()
    G.add_edge(0,1)
    G.add_edge(1,2)
    G.add_edge(2,3)
    G.add_edge(3,4)

    return G

def get_edge_stat_index(u: int, v: int, estats: list[EdgeStats]) -> EdgeStats:
    """get the index of the edge statistics that runs from u to v 

    Args:
        u (int): node 1
        v (int): node 2
        estats (list[EdgeStats]): the edge statistics arrauy

    Returns:
        int: the index of the edge that connects given nodes
    """
    for i, estat in enumerate(estats):
        if estat.u == u and estat.v == v:
            return i
    return -1 #didn't find edge in edge stats
        
def route(g: nx.Graph, estats: list[EdgeStats], req:Request) -> list[EdgeStats]:
    """Use a routing algorithm to decide a mapping of requests onto a network topology. The results of mapping should be reflected. Consider available colors on links on a path. 

    Args:
        g (nx.Graph): a network topology
        req (Request): a request to map

    Returns:
        list[EdgeStats]: updated EdgeStats
    """
    not_found = 1 #defaults to 1 because it would be true if we don't find it


    shortest_path = nx.dijkstra_path(g, req.s,req.t)[1:] #get shortest path to end
    for color in range(estats[0].cap): #check every color, starting with 0
        for node in shortest_path: #check every node in path
            if (color not in estats[get_edge_stat_index(node-1, node, estats)].get_available_colors()): #check if the current color is available in the edge we are travelling accross
                break #if the color isn't available, break and start checking next color
            if node == req.t: #check if we have arrived at destination node yet
                for node in shortest_path: #add the request to all nodes in shortest path
                    estats[get_edge_stat_index(node-1, node, estats)].add_request(req, color)
                    not_found = 0 #set to 0 because we did find it (won't add anything to blocked requests)
                print(f'{req.__str__()}: {color}\n')
                return estats, not_found

    print('no color found, blocked request\n')
    return estats, not_found #if we reach here then we did not find a color

        
if __name__ == "__main__":
    # 1. generate a network
    G = generate_graph()

    # 2. generate a list of requests (num_reqs)
    # we simulate the sequential arrivals of the pre-generated requests using a for loop in this simulation
    requests = generate_requests(40)

    # 3. prepare an EdgeStats instance for each edge.
    edge_cap = 5
    edge_stats = [EdgeStats(edge[0],edge[1],edge_cap) for edge in G.edges]

    utilization = []
    blocked_requests = 0
    blocked_requests_arr = []

    # 4. this simulation follows the discrete event simulation concept. Each time slot is defined by an arrival of a request
    for req in requests:
        #add the current utilization stats to the utilization array
        utilization.append([estat.show_spectrum_state() for estat in edge_stats])

        # 4.1 use the route function to map the request onto the topology (update EdgeStats)
        edge_stats, not_found = route(g=G, estats=edge_stats, req=req)
        blocked_requests += not_found #if we didn't find a color, this will add 1 to blocked requests
        blocked_requests_arr.append(blocked_requests)
        # 4.2 remove all requests that exhausted their holding times (use remove_requests)
        for edge_stat in edge_stats:
            edge_stat.remove_requests()

    
    '''
    #plot blocked requests
    x = range(0,40)
    plt.plot(x, blocked_requests_arr)

    plt.xlabel("time round")
    plt.ylabel("blocked requests")

    plt.show()

    #plot utilization between node 0 and 1
    plt.xlabel("time round")
    plt.ylabel("utilization between node 0 and 1")

    plt.plot(x, np.array(utilization).T[0])

    plt.show()
    '''

    #plot utilization between node 3 and 4
    '''
    plt.xlabel("time round")
    plt.ylabel("utilization between node 3 and 4")

    plt.plot(x, np.array(utilization).T[3])

    plt.show()
    '''
        