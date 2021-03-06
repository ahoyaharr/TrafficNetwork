import math
import os, sys
import datetime
from util.utils import real_distance

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'linux'


def cluster_compare(prev, cur, dist_thres=200, time_thres=45):
    """
    Units: dist_thres in feet and time_thres in seconds
    A helper function to determine whether or not the current point can be clustered, given the previous.
    Returns True if we should keep both points, otherwise False.
    """
    cur_time = datetime.datetime.strptime(cur[1], "%Y-%m-%d %H:%M:%S")
    prev_time = datetime.datetime.strptime(prev[1], "%Y-%m-%d %H:%M:%S")
    time_delta = (cur_time - prev_time).seconds
    dist_delta = real_distance((float(prev[3]), float(prev[2])), (float(cur[3]), float(cur[2])))
    if (time_delta >= time_thres) or (dist_delta >= dist_thres):
        # we should include cur
        return True
    else:
        # we can cluster these together
        return False
    # return time_delta >= time_thres or dist_delta >= dist_thres


def cluster_file(subdir, file):
    """
    Units: max_dist in feet and max_time in seconds
    """

    f = open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + subdir + separator() + file)
    contents = f.read().splitlines()
    header = contents[0]
    clustered_contents = list()
    clustered_contents.append(header + '\n')
    
    prev_line = contents[1]
    prev = prev_line.split(',')
    for line in contents[2:]:
        cur = line.split(',')
        if prev[-1] == cur[-1]:
            # print("OLD TRIP Prev:", prev[-1], "OLD TRIP Cur:", cur[-1])
            if cluster_compare(prev, cur):
                clustered_contents.append(line + '\n')
                prev = cur
        else:
            # new trip
            # print("NEW TRIP Prev:", prev[-1], "NEW TRIP Cur:", cur[-1])
            clustered_contents.append(line + '\n')
            prev = cur

    if len(clustered_contents) > 3:
        clustered_file = os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + subdir + separator() + "clustered_" + file
        with open (clustered_file, 'w') as text_file:
            text_file.write("".join(clustered_contents))
        return clustered_file
    return None


def get_files(path, absolute=False):
    """
    Returns a list of paths to uncorrected files in a directory.
    :param path: the path to the directory
    :param absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    :param system_type: 'windows' or 'unix'
    :return:
    """
    def get_script_path(p):
        return os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + p

    files = [file for file in os.listdir(get_script_path(path)) if 'clustered_' not in file]
    print(files)
    return [get_script_path(path) + separator() + file for file in files] if absolute else files


def separator():
    return WINDOWS_ENCODING if SYSTEM_TYPE == 'windows' else UNIX_ENCODING


def read_all(subdirectory):
    for file in get_files(subdirectory):
        print('\tClustering ' + file)
        clustered_file = cluster_file(subdirectory, file)
        if clustered_file:
            print('\tWrote corrected dataset to ' + clustered_file)
        else:
            print('\tTrip too short. Not written.')

read_all('to_cluster')
