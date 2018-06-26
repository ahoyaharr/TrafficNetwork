import math
import copy

from util.utils import real_distance


def first_score(point, candidates, network):
    def normalize(l):
        total = sum(l)
        if (total == 0):
            print('warning: sum of a list was 0 during normalization')
            total = .01
        return list(map(lambda value: value / total, l))

    bearing_scores = []
    speed_scores = []
    distance_scores = []

    max_distance = 0
    # Iterate over each candidate, which is a vertex id.
    for candidate in candidates:
        print('iterating over candidates in first_score:', candidate)
        # Update the bearing score.
        delta_theta = abs(math.radians(point.bearing - network.node_heading[candidate]))
        bearing_scores.append((1 + math.cos(delta_theta)) / 2)

        # Update the speed score. If point.speed is 0, then discard speed as a factor by setting every score to 1.
        speed_scores.append(point.speed / network.node_speed_limit[candidate] if point.speed > 0 else 1)

        # Discover the distance between point and the candidate, and keep track of the maximum distance.
        distance_scores.append(real_distance(point.as_list(), network.node_locations[candidate]))
        if distance_scores[-1] > max_distance:
            max_distance = distance_scores[-1]

    print('finished initial score calculations. \nbearing = ',  bearing_scores, '\nspeed = ', speed_scores, '\ndistance = ', distance_scores)

    # Update the distance scores as -1 * log(distance(point, candidate) / maximum(distance(point, candidate))).
    # Increasing the base of the log reduces the importance of the distance in the total evaluation.
    BASE = 10
    distance_scores = list(map(lambda d: -math.log(d / max_distance, BASE), distance_scores))

    # Component scores are combined into a composite score by taking the product then normalized.
    scores = normalize([b * s * d for b, s, d in zip(bearing_scores, speed_scores, distance_scores)])

    # Each component score is exponentiated and renormalized. This is to increase the confidence of scores
    # that are highest, and to decrease the scores that are lowest, relative to each other.
    EXPONENT = 2
    scores = normalize(list(map(lambda score: score ** EXPONENT, scores)))
    print({candidate: score for candidate, score in zip(candidates, scores)})
    return {candidate: score for candidate, score in zip(candidates, scores)}

def first_evaluation(network, scores):
    print(scores)
    DISCOUNT = 0.5
    THRESHOLD = .125

    modified_scores = copy.deepcopy(scores)

    if modified_scores is None or scores is None:
        print('scores', scores)
        print('deep copy', modified_scores)
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


# self.tree = MTree(lambda v1, v2: utils.real_distance(self.node_locations[v1], self.node_locations[v2]), 100)
# self.tree.add_all(list(self.graph.get_vertices()))

class MapMatch:
    def __init__(self, network, tree, score, evaluation, data):
        """
        :param network: A logical network of nodes which has a function defining the distance between two vertices called vertex_distance.
        :param tree: A data structure which can be constructed using only a list of vertices.
        :param score: A function which accepts a network, a point, and a sequence of candidate points.
        :param evaluation: A function which accepts a network and the sequence of the output of a score function on each data point
                           and returns the map matching result.
        :param data: Sequence of DataPoints.
        """
        self.network = network
        self.tree = tree(network.vertex_distance)
        self.tree.add_all(network.graph.get_vertices())
        self.score = score
        self.evaluation = evaluation
        self.data = data

    def match(self):
        scores = [self.score(p, self.find_knn(p.as_list()), self.network) for p in self.data]
        return self.evaluation(self.network, scores)

    def find_knn(self, point, num_results=20):
        """
        Given a point p, search for the k points nearest to p.
        :param point: A list in the form, [lon, lat]
        :param num_results: The number of neighbors to be found
        :return: A list of node IDs
        """
        v = self.network.graph.add_vertex()
        self.network.node_locations[v] = point
        result = [item for item in self.tree.search(v, num_results) if item is not None]
        self.network.graph.remove_vertex(v, fast=True)
        print(result)
        return result
