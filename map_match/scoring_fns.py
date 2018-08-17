import datetime
import math

from util.utils import real_distance, print_progress


def path_score(index, points, find_candidates, network):
    """
    scores candidates by searching for candidates with 'good' (close) connectivity distance relative to all
    previous candidates. poor accuracy because the accuracy of the kth point is dependent upon the accuracy
    of the k-1th point.
    :param index:
    :param points:
    :param find_candidates:
    :param network:
    :return:
    """
    try:
        '' in path_score.cache
    except AttributeError:
        path_score.cache = {}

    # print(' ' * index, '-')  # prints the depth of the recursion

    key = (index, tuple((point for point in points)))
    if key not in path_score.cache:
        """ Lower values of connectivity_factor increase the weight that the distance 
        between previously matched points has on the current match."""
        connectivity_factor = 1
        connectivity_score = lambda a, b, cf: cf + math.log(network.shortest_distance_between_vertices(a, b) + math.e)
        point = points[index]
        scores = {}

        for candidate in find_candidates(point.as_list()):
            heading_multiplier = 1 + math.cos(math.radians(point.bearing - network.node_heading[candidate]))
            distance = 1 / real_distance(point.as_list(), network.node_locations[candidate])
            width = network.node_width[candidate]
            scores[candidate] = distance * heading_multiplier * width

        if index > 0:
            previous_candidates = path_score(index - 1, points, find_candidates, network)
            previous_match = max(previous_candidates, key=lambda candidate: previous_candidates[candidate])
            scores = {candidate: score / connectivity_score(candidate, previous_match, connectivity_factor)
                      for candidate, score in scores.items()}

        path_score.cache[key] = scores

    return path_score.cache[key]


def simple_distance_heading(index, points, find_candidates, network, score_multiplier=1000):
    point = points[index]
    scores = {}
    for candidate in find_candidates(point.as_list()):
        width = network.node_width[candidate]
        if width == 0:  # Exclude all lanes with zero weight
            continue
        heading_multiplier = 1 + math.cos(math.radians(point.bearing - network.node_heading[candidate]))
        distance = 1 / (1 + real_distance(point.as_list(), network.node_locations[candidate]))
        scores[candidate] = distance * heading_multiplier * width
    sum_of_scores = sum(scores.values())
    return {candidate: (score / sum_of_scores) * score_multiplier for candidate, score in scores.items()}


def pow_distance_heading(index, points, find_candidates, network, distance_weight=.75, heading_weight=2,
                         width_weight=1, score_multiplier=100):
    point = points[index]
    scores = {}
    for candidate in find_candidates(point.as_list()):
        width = network.node_width[candidate]
        if width == 0:  # Exclude all lanes with zero weight
            continue
        heading_multiplier = 1 + math.cos(math.radians(point.bearing - network.node_heading[candidate]))
        distance = 1 / (1 + real_distance(point.as_list(), network.node_locations[candidate]))
        scores[candidate] = (distance ** distance_weight) * (heading_multiplier ** heading_weight) * (
                width ** width_weight)
    sum_of_scores = sum(scores.values())
    return {candidate: (score / sum_of_scores) * score_multiplier for candidate, score in scores.items()}


def log_distance_heading(index, points, find_candidates, network, distance_weight=math.e, score_multiplier=100):
    point = points[index]
    scores = {}
    for candidate in find_candidates(point.as_list()):
        width = network.node_width[candidate]
        if width == 0:  # Exclude all lanes with zero weight
            continue
        heading_multiplier = 1 + math.cos(math.radians(point.bearing - network.node_heading[candidate]))
        distance = 1 / math.log(distance_weight + real_distance(point.as_list(), network.node_locations[candidate]),
                                distance_weight)
        scores[candidate] = distance * heading_multiplier * width
    sum_of_scores = sum(scores.values())
    return {candidate: (score / sum_of_scores) * score_multiplier for candidate, score in scores.items()}


def exp_distance_heading(index, points, find_candidates, network, exponent=2, score_multiplier=1):
    print_progress(len(points), prefix='scoring candidates of {0}th data point'.format(index))
    point = points[index]
    scores = {}
    for candidate in find_candidates(point.as_list()):
        width = network.node_width[candidate]
        if width == 0:  # Exclude all lanes with zero weight
            continue
        heading_multiplier = 1 + math.cos(math.radians(point.bearing - network.node_heading[candidate]))
        distance = 1 / (math.log(math.e + real_distance(point.as_list(), network.node_locations[candidate])))
        scores[candidate] = (distance * heading_multiplier) ** exponent
    sum_of_scores = sum(scores.values())
    return {candidate: (score / sum_of_scores) * score_multiplier for candidate, score in scores.items()}


def general_distance_heading(index, points, find_candidates, network,
                             width_score, heading_score, distance_score, combiner):
    """
    A general score function, which accepts functions to evaluate each parameter.
    :param index:
    :param points:
    :param find_candidates:
    :param network:
    :param width_score: fn which maps the width to a real number
    :param heading_score: fn which maps the difference in bearing to a real number
    :param distance_score: fn which maps the distance in feet to a real number
    :param combiner: 3 argument fn which maps the scores for heading, distance and width to a real number
    :return: a mapping between candidates and their scores
    """
    print_progress(len(points), prefix='scoring candidates of {0}th data point'.format(index))
    point = points[index]
    scores = {}
    for candidate in find_candidates(point.as_list()):
        width = network.node_width[candidate]
        if width == 0:  # Exclude all lanes with zero weight
            continue
        try:
            width = width_score(width)
        except:
            width = 0

        try:
            hs = heading_score(point.bearing - network.node_heading[candidate])
        except:
            hs = 0

        try:
            ds = distance_score(real_distance(point.as_list(), network.node_locations[candidate]))
        except:
            ds = 0

        try:
            scores[candidate] = combiner(hs, ds, width)
        except:
            scores[candidate] = 0

    sum_of_scores = sum(scores.values())
    return {candidate: (score / sum_of_scores) for candidate, score in scores.items()}


def one_score(index, points, find_candidates, network, exponent=2, score_multiplier=100):
    """
    Test scoring function which assigns a score of 1 to every candidate
    """
    start = datetime.datetime.now()
    point = points[index]
    scores = {}

    start = datetime.datetime.now()
    candidates = find_candidates(point.as_list())
    print('found candidates', str(datetime.datetime.now() - start))

    start = datetime.datetime.now()
    for candidate in candidates:
        a = candidate.__hash__()
    print('computed hashes', str(datetime.datetime.now() - start))

    start = datetime.datetime.now()
    for candidate in candidates:
        scores[candidate] = 1
    print('assigned score', str(datetime.datetime.now() - start))

    start = datetime.datetime.now()
    print('')
    return scores
