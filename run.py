import mapMatch
import map_match.evaluation_fns
import map_match.scoring_fns
import util.Shapes
import util.m_tree.tree
import util.utils
import util.export
from constructNetwork import TrafficNetwork

# Decode the JSON of junction and section information to construct the network.
junction_map, section_map = util.utils.decode_json()
network = TrafficNetwork(junction_map, section_map)

# Use this to convert a dataset into points that our Map Matcher can use. Place the file of data into the data
# subdirectory and change filename to be a string of the name of the file you would like to run.
# Example usage:
#  data = util.Shapes.DataPoint.convert_dataset(filename='i210_2017_10_22_id960801st_ordered.csv', subdirectory='data')

data = util.Shapes.DataPoint.convert_dataset(filename='clipped_clustered_45sec_20171001CONSUMER.csv')
print('network constructed. number of nodes:', network.equalize_node_density(200, 15, greedy=True))

# Call the map matching algorithm on your data. The second argument to batch_process will be the prefix of the
# outputted filenames - we recommend changing this to match the filename you passed in above.

mm = mapMatch.MapMatch.without_evaluation(network, util.m_tree.tree.MTree)
mm.batch_process(data,
                 'clipped_clustered_45sec_20171001CONSUMER',
                 score=map_match.scoring_fns.exp_distance_heading,
                 evaluation=map_match.evaluation_fns.viterbi)
