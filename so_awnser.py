import networkx as nx

edge = [(1,2,1), (1,2,2), (1,2,3), (2,3,1), (2,3,2)]
g = nx.MultiGraph()
g.add_edges_from(edge)
for path in nx.all_simple_edge_paths(g,1,3):
    print(path)
    


