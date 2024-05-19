import networkx as nx
import numpy as np
import random
from random import choice
import matplotlib.pyplot as plt
#blocked_route = 0
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
        return f'{self.id}, cap = {self.cap}: {self.reqs}'

    def add_request(self, req: Request, color:int):
        """update self.__slots by adding a request to the specific color slot

        Args:
            req (Request): a request
            color (int): a color to be used for the request
        """
        self.__slots[color]=req
        self.__hts[color]=req.ht
        pass

    def remove_requests(self):
        """update self.__slots by removing the leaving requests based on self.__hts; Also, self.__hts should be updated in this function.
        """
        for i in range(10):
          if self.__hts[i] == 1:
            self.__slots[i] = None
            self.__hts[i] -=1
          elif self.__hts[i] == 0:
            pass
          else:
            self.__hts[i] -=1


    def get_available_colors(self) -> list[int]:
        """return a list of integers available to accept requests
        """
        returnV = []
        for i in range(len(self.__hts)):
          if self.__slots[i] is None :
            returnV.append(i)
        return returnV

    def show_spectrum_state(self) -> float:
        """Come up with a representation to show the utilization state of a link (by colors)
        """
        n=0
        for i in self.__slots:
          if i == None:
            n+=1
        return (10-n)/10


def generate_requests(num_reqs: int, g: nx.Graph) -> list[Request]:
    """Generate a set of requests, given the number of requests and an optical network (topology)

    Args:
        num_reqs (int): the number of requests
        g (nx.Graph): network topology

    Returns:
        list[Request]: a list of request instances
    """
    returnV = []
    for i in range(num_reqs):
      returnV.append(Request('San Diego Supercomputer Center','Jon Von Neumann Center, Princeton, NJ',np.random.randint(10, 20)))
    return returnV


def generate_graph() -> nx.Graph:
    """Generate a networkx graph instance importing a GML file. Set the capacity attribute to all links based on a random distribution.

    Returns:
        nx.Graph: a weighted graph
    """
    pass


def route(g: nx.Graph, estats: list[EdgeStats], req:Request) -> list[EdgeStats]:
    """Use a routing algorithm to decide a mapping of requests onto a network topology. The results of mapping should be reflected. Consider available colors on links on a path.

    Args:
        g (nx.Graph): a network topology
        req (Request): a request to map

    Returns:
        list[EdgeStats]: updated EdgeStats
    """
    #global blocked_route
    path = nx.shortest_path(g, source=req.s, target=req.t)
    edge_pairs = list(zip(path[:-1], path[1:]))

    commoncolor = set([0,1,2,3,4,5,6,7,8,9])

    for i in range(len(estats)):
      e = estats[i].id
      if e in edge_pairs:
        avail_color = estats[i].get_available_colors()
        if (len(avail_color)) ==0:
          #blocked_route += 1
          return estats
        else:
          commoncolor = commoncolor & set(avail_color)
    if len(commoncolor) == 0:
      #blocked_route +=1
      return estats
    color = min(commoncolor)
    #update
    for i in range(len(estats)):
      e = estats[i].id
      if e in edge_pairs:
        temp = estats[i]
        temp.add_request(req,color)
        estats[i]=temp

    return estats

if __name__ == "__main__":
    # 1. generate a network
    G = nx.read_gml('nsfnet.gml')

    # 2. generate a list of requests (num_reqs)
    # we simulate the sequential arrivals of the pre-generated requests using a for loop in this simulation
    requests = generate_requests(100,G)

    # 3. prepare an EdgeStats instance for each edge.
    EdgeStatsL = []
    for i,j in G.edges():
      EdgeStatsL.append(EdgeStats(i,j,10))
    link_state_x = []
    obj = 0
    # 4. this simulation follows the discrete event simulation concept. Each time slot is defined by an arrival of a request
    for req in requests:
        # 4.1 use the route function to map the request onto the topology (update EdgeStats)
      EdgeStatsL = route(G,EdgeStatsL,req)
      #blocked_x.append(blocked_route)
      # 4.2 remove all requests that exhausted their holding times (use remove_requests)
      objt = 0
      for i in range(len(EdgeStatsL)):
        objt+=temp.show_spectrum_state()
        temp = EdgeStatsL[i]
        temp.remove_requests()
        EdgeStatsL[i] = temp
      objt = objt/len(EdgeStatsL)
      obj += objt

    print(obj/100)
    