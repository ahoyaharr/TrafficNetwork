import util.utils
import util.Shapes
import util.SearchArea
import util.m_tree
import util.parser as parser
import util.export as export
import mapMatch
import map_match.evaluation_fns
import map_match.scoring_fns
from constructNetwork import TrafficNetwork
from graph_tool.all import *
import graph_tool.topology
import collections
import itertools
#
p = util.Shapes.Point(-118.141671408,34.169072391, 0)
#
#
# p_offset = util.utils.offset_point(p, .025, 0)
#
# print(p_offset)
header = ['lon', 'lat', 'speed', 'heading']

data = util.Shapes.DataPoint.convert_dataset(filename='i210_2017_10_22_id960801st.csv', subdirectory='data')
#
junction_map, section_map = util.utils.decode_json()
network = TrafficNetwork(junction_map, section_map)
print(network.equalize_node_density(100, 15, greedy=True))

# util.export.export(['lon1', 'lat1', 'lon2', 'lat2', 'weight'], network.export_edges(), 'edges_final')
# util.export.export(header, network.export_nodes(), 'nodes final')

# print('searching')
# print(network.sections['1800'], network.sections['2638'])
# result = graph_tool.topology.shortest_path(network.graph, network.sections['1800'][0], network.sections['2638'][-1], weights=network.edge_weights)
# print('finished')
# print(result)
#
# for va in result:
#     for v in va:
#         prev = None
#         try:
#             if prev != network.node_id[v]:
#                 print(network.node_locations[v], network.node_id[v])
#                 prev = network.node_id[v]
#         except:
#             print(network.edge_weights[v])

# network.find_path(1800, 2638)

#
#
print('begin populating m-tree')
# util.utils.time_fn(mapMatch.MapMatch, 1, [network, util.m_tree.MTree, map_match.scoring_fns.first_score, map_match.evaluation_fns.first_evaluation, data])
mm = mapMatch.MapMatch(network, util.m_tree.MTree, map_match.scoring_fns.simple_distance_heading, map_match.evaluation_fns.simple_evaluation, data)
print('finish populating m-tree')
#
header, result = mm.export()
util.export.export(header, result, 'match_attempt_simple')
# print([network.node_locations[v_id] for v_id in mm.find_knn([-118.017415, 34.141630])])
#
# #
#
# import time
#
# search_point = util.Shapes.Point(-118.0832555, 34.1477116, 90)
#
# time_fn(TrafficNetwork, 1, [junction_map, section_map, 5])
# time_fn(TrafficNetwork, 1, [junction_map, section_map, 25])
# time_fn(TrafficNetwork, 1, [junction_map, section_map, 125])
#
# print("finished making network")
# graph_draw(network.graph)

# nodes, edge = graph_tool.topology.shortest_path(network.graph, network.get_entrance_junction('1941'),
#                                                network.get_exit_junction('24237'),
#                                                weights=network.edge_weights)
#
#




#time_fn(network.find_knn, 10000, [search_point.get_as_list(), 20])


# for v in network.find_knn(search_point.get_as_list(), 20):
#     print(network.node_id[v], network.node_locations[v])



#
# for _ in range(100):
#     search_area = util.SearchArea.SearchArea(search_point, 0.1, .025, 60)
#
#     print(search_area.initial_point)
#
#     print(search_area.search_area)
#
#     good_points = []
#
#     count = 0
#     for v in network.graph.vertices():
#         count += 1
#         point = util.Shapes.Point.from_list(network.node_locations[v])
#         if search_area.contains(point):
#             good_points.append(point)

#nodes = list(collections.OrderedDict.fromkeys(map(lambda node: network.node_locations[node], nodes)))

#print(nodes)

#print("finished 100 searches")

#
# from pysal.cg import rtree
#
# r = rtree.RTree()


#
# def fake_distance(a, b):
#     return abs(a-b)
#
# tree = util.m_tree.MTree(real_distance, max_node_size=50)   # create an empty M-tree
# tree.add_all(range(1000))
# print("finished making tree")
#
# for _ in range(100):
#     result = tree.search(23, 20)
#     print(_)
#
# print(type(result))
# print(list(result))

