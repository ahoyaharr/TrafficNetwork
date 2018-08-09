import copy
import math
import util.utils as utils
from collections import namedtuple
from heapq import heapify, heappop as pop, heappush as push
from functools import reduce


def viterbi_optimized(network, scores):
    """
    An optimized version of Viterbi. Instead of evaluating the K*O matrix column by column, the single most likely
    path is evaluated. In the worst case, the full matrix is evaluated which yields the same runtime as the
    basic Viterbi algorithm, O(K^2 * O). In the best case, only a single path is evaluated, which has a time complexity
    of Ω(K*O).
    :param network:
    :param scores:
    :return:
    """
    def normalize_subpath_scores(subpaths):
        """
        normalizes the scores of all paths in a subpath
        :param subpaths:
        :return:
        """
        sum_of_scores = reduce(lambda total, t: total + t.score, subpaths, 0)
        return [subpath_factory(-(path.score / sum_of_scores), path.length, path.path) for path in subpaths]

    def update(active_subpath):
        """
        Given a single active path, find the most probable next candidate and add it to the path.
        :param active_subpath: a named tuple with fields score, length, path
        :return: an active subpath with the most probable candidate appended to it
        """

        def update_pr(candidate):
            """
            Finds the probability of an active path if the candidate is added to it.
            Score = Probability of active path * Probability of candidate / Distance(old path -> candidate)
            :param candidate: tuple of (id of candidate vertex, score)
            :return: score
            """
            candidate_probability = candidate[1]
            distance = 1 + network.shortest_distance_between_vertices(active_subpath.path[-1], candidate[0])
            #print('[candidate: {0}], [active_subpath: {1}], [distance: {2}]'.format(candidate, active_subpath, distance))
            return active_subpath.score * candidate_probability / distance ** 1.5

        def update_path(candidate):
            """
            Given an active path, finds the most probable path with the candidate added to it.
            :param candidate: tuple of (id of candidate vertex, score)
            :return: A list of vertex IDs
            """
            return active_subpath.path[:-1] + network.find_vertex_path(active_subpath.path[-1], candidate[0], False)[0]

        active_candidates = list(scores[active_subpath.length].items())
        best_candidate = min(active_candidates, key=update_pr)
        # print('best candidate for {0} is {1} with score {2}'.format(active_subpath, best_candidate, update_path(best_candidate)))
        return subpath_factory(update_pr(best_candidate), active_subpath.length + 1, update_path(best_candidate))

    subpath_factory = namedtuple('Subpath', ['score', 'length', 'path'])

    """ At the first observation, the possible paths are the candidates, and their emission probabilities. 
    Score is multiplied by -1 because heapq is a min heap. """
    active_subpaths = [subpath_factory(-score, 1, [candidate]) for candidate, score in scores[0].items()]
    heapify(active_subpaths)

    """ Add the most probable candidate to the most probable path, until a complete path is found. """
    best_subpath = pop(active_subpaths)
    while best_subpath.length < len(scores):
        print('active_subpaths: {0}, best_subpath: {1}, {2}'.format(len(active_subpaths)+1, best_subpath.score, best_subpath.length))
        best_subpath = update(best_subpath)
        if best_subpath.score == 0:
            print('warning: best_subpath_score is {0}'.format(best_subpath.score))
        push(active_subpaths, best_subpath)
        active_subpaths = normalize_subpath_scores(active_subpaths)
        best_subpath = pop(active_subpaths)

    """ Return the most probable complete path. """
    return best_subpath.path


def viterbi(network, scores):
    """
    Uses the Viterbi algorithm to find the most probable path. The Viterbi algorithm is a dynamic programming algorithm
    which finds the shortest path through a probability lattice (HMM).
    :param network: a network which can query paths
    :param scores: a set of candidates and scores for each data point
    :return: a path
    """

    def find_next_step(observation_candidate, active_paths):
        """
        Find the best active path leading to the candidate of an observation, and find the probability of the path
        passing through the candidate, and the path that would pass through the candidate.
        :param observation_candidate: a tuple of (candidate, score)
        :param active_paths: a list of [ ([path], score) ]
        :return: a tuple of ([path], score)
        """

        def update_pr(active_path):
            """
            Finds the probability of an active path if the candidate is added to it.
            Score = Probability of active path * Probability of candidate / Distance(old path -> candidate)
            :param active_path: tuple of ([path], score)
            :return: score
            """
            if not active_path[0]:  # If there was a path that led to a dead end, the probability is zero.
                #print('WARNING: found path of length {}'.format(len(active_path)))
                return 0
            pr_active_path = active_path[1]
            pr_candidate = observation_candidate[1]
            distance = 1 + network.shortest_distance_between_vertices(active_path[0][-1], observation_candidate[0])
            return (pr_active_path * pr_candidate) / (distance ** 1.5)

        def update_path(path):
            """
            Given an active path, finds the most probable path with the candidate added to it.
            :param path: A list of vertex IDs
            :return: A list of vertex IDs
            """
            if not path:  # If there was a path that led to a dead end, return a path with no items.
                return list()
            return path[:-1] + network.find_vertex_path(path[-1], observation_candidate[0], False)[0]

        best = max(((active_path[0], update_pr(active_path)) for active_path in active_paths), key=lambda t: t[1])
        return update_path(best[0]), best[1]

    """ At the first observation, the possible paths are the candidates, and their emission probabilities. """
    possible_paths = [([candidate], score) for candidate, score in scores[0].items()]
    utils.print_progress(len(scores), prefix='searching for most probable route')
    """ For each observation, update the paths and probabilities. """
    for candidate_map in scores[1:]:
        utils.print_progress(len(scores), prefix='searching for most probable route')
        possible_paths = [find_next_step((candidate, score), possible_paths)
                          for candidate, score in candidate_map.items()]
        sum_of_scores = sum(path[1] for path in possible_paths)
        possible_paths = [(path[0], path[1] / sum_of_scores) for path in possible_paths]

    """ Return the most probable path. """
    return max(possible_paths, key=lambda t: t[1])[0]


def simple_evaluation(network, scores):
    best_match = [max(score.keys(), key=(lambda key: score[key])) for score in scores]
    matches = [(network.node_id[node], network.node_locations[node]) for node in best_match]
    return matches


def first_evaluation(network, scores):
    """
    First attempt at evaluation. Attempts to match a point to a node by selecting the candidate with the largest
    score for a given point after weighting that point using the results of other nearby points. Used to construct
    a MapMatch object.
    """
    DISCOUNT = 0.5  # A node j positions away from the currently evaluated node is weighted at DISCOUNT ^ j.
    THRESHOLD = .125  # Stop considering values once DISCOUNT ^ j < THRESHOLD.

    modified_scores = copy.deepcopy(scores)

    if modified_scores is None or scores is None:
        return

    for index, score in enumerate(scores):
        for i in range(int(math.log(THRESHOLD) / math.log(DISCOUNT)) + 1):
            for candidate in score.keys():
                try:
                    previous = scores[index - i]
                    if candidate in previous:
                        modified_scores[index][candidate] += previous[candidate] * DISCOUNT ** i
                except IndexError:
                    pass

                try:
                    next = scores[index + i]
                    if candidate in next:
                        modified_scores[index][candidate] += next[candidate] * DISCOUNT ** i
                except IndexError:
                    pass

    best_match = [max(score.keys(), key=(lambda key: score[key])) for score in modified_scores]
    matches = [(network.node_id[node], network.node_locations[node]) for node in best_match]
    return matches
