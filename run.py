import collections

from graph_tool.all import *

import utils
from constructNetwork import TrafficNetwork

junction_map, section_map = utils.decodeJSON()
print(junction_map)
network = TrafficNetwork(junction_map, section_map)

nodes, edge = graph_tool.topology.shortest_path(network.graph, network.get_entrance_junction('1941'),
                                                network.get_exit_junction('24237'),
                                                weights=network.edge_weights)

nodes = list(collections.OrderedDict.fromkeys(map(lambda node: network.node_locations[node], nodes)))

print(nodes)
