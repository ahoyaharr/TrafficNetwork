import mapMatch
import map_match.evaluation_fns
import map_match.scoring_fns
import util.Shapes
import util.m_tree.tree
import util.utils
import util.export
from constructNetwork import TrafficNetwork

junction_map, section_map = util.utils.decode_json()
network = TrafficNetwork(junction_map, section_map)
data = util.Shapes.DataPoint.convert_dataset(filename='i210_2017_10_22_id960801st_ordered.csv', subdirectory='data')
print('network constructed. number of nodes:', network.equalize_node_density(200, 15, greedy=True))

mm = mapMatch.MapMatch(network,
                       util.m_tree.tree.MTree,
                       map_match.scoring_fns.exp_distance_heading,
                       map_match.evaluation_fns.viterbi,
                       data)

#mm = mapMatch.MapMatch.without_evaluation(network, util.m_tree.tree.MTree)

path_header, path_result = mm.export_path()
path_header.append('number')
for i in range(len(path_result)):
    path_result[i]['number'] = i

print('size of path:', len(path_result))

match_header, match_result = mm.export_matches()
