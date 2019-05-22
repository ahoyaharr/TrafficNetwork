import mapMatch
import map_match.evaluation_fns
import map_match.scoring_fns
import util.Shapes
import util.m_tree.tree
import util.utils
import util.export
from constructNetwork import TrafficNetwork
import sys, os

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'linux'

def run(f):

    # Decode the JSON of junction and section information to construct the network.
    junction_map, section_map = util.utils.decode_json()
    network = TrafficNetwork(junction_map, section_map)

    # Use this to convert a dataset into points that our Map Matcher can use. Place the file of data into the data
    # subdirectory and change filename to be a string of the name of the file you would like to run.
    # Example usage:
    #  data = util.Shapes.DataPoint.convert_dataset(filename='i210_2017_10_22_id960801st_ordered.csv', subdirectory='data')

    data = util.Shapes.DataPoint.convert_dataset(f)
    print('network constructed. number of nodes:', network.equalize_node_density(200, 15, greedy=True))

    # Call the map matching algorithm on your data. The second argument to batch_process will be the prefix of the
    # outputted filenames - we recommend changing this to match the filename you passed in above.

    mm = mapMatch.MapMatch.without_evaluation(network, util.m_tree.tree.MTree)
    mm.batch_process(data,
                     f[:-12],
                     score=map_match.scoring_fns.exp_distance_heading,
                     evaluation=map_match.evaluation_fns.viterbi,
                     min_path=2)

    #mm.batch_process(data,'clipped_clustered_45sec_20171001CONSUMER',score=map_match.scoring_fns.exp_distance_heading,evaluation=map_match.evaluation_fns.viterbi)


def get_files(path, absolute=False, system_type=SYSTEM_TYPE):
    # Returns a list of paths to uncorrected files in a directory.
    # path: the path to the directory
    # absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    # system_type: 'windows' or 'unix'
    def get_script_path(p):
        return os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + p

    files = [file for file in os.listdir(get_script_path(path)) if 'clustered_' in file]
    print(files)
    return [get_script_path(path) + separator() + file for file in files] if absolute else files


def separator():
    return WINDOWS_ENCODING if SYSTEM_TYPE == 'windows' else UNIX_ENCODING


def read_all(subdirectory):
    for file in get_files(subdirectory):
        print('\tRunning ' + file)
        run(file)
        print('\tFinished ' + file)

read_all('data')

# run(sys.argv[1])