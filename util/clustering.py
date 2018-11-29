import math
import csv
import os, sys
import datetime

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

def real_distance(cp1, cp2):
    """
    >>> 995.0 <= real_distance([-118.121438, 34.179766], [-118.118132, 34.179786]) <= 1000.0
    True

    Computes the distance in feet between two points using the Haversine Formula.
    :param cp1: A list in the form [lon1, lat1].
    :param cp2: A list in the form [lon2, lat2].
    :return: The distance in feet between two coordinates.
    """
    earth_radius = 6378.1
    KM_TO_FEET_CONST = 3280.84

    cp1 = list(map(math.radians, cp1))
    cp2 = list(map(math.radians, cp2))

    delta_lon = cp2[0] - cp1[0]
    delta_lat = cp2[1] - cp1[1]

    a = math.sin(delta_lat / 2) ** 2 + math.cos(cp1[1]) * math.cos(cp2[1]) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c * KM_TO_FEET_CONST


def cluster_compare(prev, cur, dist_thres=200, time_thres=45):
    """
    Units: max_dist in feet and max_time in seconds
    """
    cur_time = datetime.datetime.strptime(cur[1],  "%Y-%m-%d %H:%M:%S")
    prev_time = datetime.datetime.strptime(prev[1],  "%Y-%m-%d %H:%M:%S")
    time_delta = (cur_time - prev_time).seconds
    dist_delta = real_distance((float(prev[3]), float(prev[2])), (float(cur[3]), float(cur[2])))
    if (time_delta >= time_thres) or (dist_delta >= dist_thres):
        # we should include cur
        return True
    else:
        # we can cluster these together
        return False


def cluster_file(subdir, file):
    """
    Units: max_dist in feet and max_time in seconds
    """

    f = open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + subdir + separator() + file)
    contents = f.read().splitlines()
    header = contents[0]
    clustered_contents = []
    clustered_contents.append(header + '\n')
    
    prev_line = contents[1]
    prev = prev_line.split(',')
    for line in contents[2:]:
        cur = line.split(',')
        if prev[-1] == cur[-1]:
            print("OLD TRIP Prev:", prev[-1], "OLD TRIP Cur:", cur[-1])
            if cluster_compare(prev, cur):
                clustered_contents.append(line + '\n')
                prev = cur
        else:
            # new trip
            print("NEW TRIP Prev:", prev[-1], "NEW TRIP Cur:", cur[-1])
            clustered_contents.append(line + '\n')
            prev = cur
    clustered_file = os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + subdir + separator() + "clustered_" + file
    with open (clustered_file, 'w') as text_file:
        # print("clustered contents: ", clustered_contents)
        text_file.write("".join(clustered_contents))
        # write must take in a string
    return clustered_file


def get_files(path, absolute=False, system_type=SYSTEM_TYPE):
    # Returns a list of paths to uncorrected files in a directory.
    # path: the path to the directory
    # absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    # system_type: 'windows' or 'unix'
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
        print('\tWrote corrected dataset to ' + clustered_file)

read_all('data')
