import math
import datetime

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


def exp_distance_heading(index, points, find_candidates, network, exponent=2, score_multiplier=100):
    print_progress(len(points), prefix='scoring candidates of {0}th data point'.format(index))
    point = points[index]
    scores = {}
    for candidate in find_candidates(point.as_list()):
        width = network.node_width[candidate]
        if width == 0:  # Exclude all lanes with zero weight
            continue
        heading_multiplier = 1 + math.cos(math.radians(point.bearing - network.node_heading[candidate]))
        distance = 1 / (1 + real_distance(point.as_list(), network.node_locations[candidate]))
        scores[candidate] = (distance * heading_multiplier * width) ** exponent
    sum_of_scores = sum(scores.values())
    return {candidate: (score / sum_of_scores) * score_multiplier for candidate, score in scores.items()}

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

# def first_score(point, candidates, network):
#     """
#     First attempt at scoring. Each node is scored based on the similarity of it's speed, bearing, and position to
#     a candidate node. Scores are then normalized, then exponentiated, then re-normalized to push scores with high
#     confidence higher and scores with low confidence lower. Used to construct a MapMatch object.
#     a MapMatch object.
#     """
#     def normalize(l):
#         """
#         Normalizes the values in a list, such that the sum(l) = 1.
#         :param l: A list containing numeric values.
#         :return: A list containing the normalized values.
#         """
#         total = sum(l)
#         if total == 0:  # Cannot divide by zero!
#             print('warning: sum of a list was 0 during normalization')
#             return [0 for _ in l]
#         return list(map(lambda value: value / total, l))
#
#     bearing_scores = []
#     speed_scores = []
#     distance_scores = []
#
#     max_distance = 0
#     # Iterate over each candidate, which is a vertex id.
#     for candidate in candidates:
#         # Update the bearing score.
#         delta_theta = abs(math.radians(point.bearing - network.node_heading[candidate]))
#         bearing_scores.append((1 + math.cos(delta_theta)) / 2)
#
#         # Update the speed score. If point.speed is 0, then discard speed as a factor by setting every score to 1.
#         speed_scores.append(point.speed / network.node_speed_limit[candidate] if point.speed > 0 else 1)
#
#         # Discover the distance between point and the candidate, and keep track of the maximum distance.
#         distance_scores.append(real_distance(point.as_list(), network.node_locations[candidate]))
#         if distance_scores[-1] > max_distance:
#             max_distance = distance_scores[-1]
#
#     # Update the distance scores as -1 * log(distance(point, candidate) / maximum(distance(point, candidate))).
#     # Increasing the base of the log reduces the importance of the distance in the total evaluation.
#     BASE = 10
#     distance_scores = list(map(lambda d: -math.log(d / max_distance, BASE), distance_scores))
#
#     # Component scores are combined into a composite score by taking the product then normalized.
#     scores = normalize([b * s * d for b, s, d in zip(bearing_scores, speed_scores, distance_scores)])
#
#     # Each component score is exponentiated and re-normalized. This is to increase the confidence of scores
#     # that are highest, and to decrease the scores that are lowest, relative to each other.
#     EXPONENT = 2
#     scores = normalize(list(map(lambda score: score ** EXPONENT, scores)))
#     return {candidate: score for candidate, score in zip(candidates, scores)}
