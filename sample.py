import networkx as nx
import matplotlib.pyplot as plt

#create own topology
'''G = nx.Graph()
G.add_edge(1,2)
G.add_edge(2,3)
G.add_edge(3,4)'''

#read in topology
G = nx.read_gml('nsfnet.gml')

edge_paths = []
for node1 in G.nodes:
    for node2 in G.nodes:
        if node1 != node2:
            for path in sorted(nx.all_simple_edge_paths(G,source=node1,target=node2)):
                edge_paths.append(path)

print(len(edge_paths))
print(len(G.nodes))


#nodes = nx.dijkstra_path(G,'Denver','New York')#shortest path
#print(nodes)

#show the graph visually
#nx.draw(G)
#plt.savefig('pic')

