import math

from util.utils import real_distance


def first_score(point, candidates, network):
    """
    First attempt at scoring. Each node is scored based on the similarity of it's speed, bearing, and position to
    a candidate node. Scores are then normalized, then exponentiated, then re-normalized to push scores with high
    confidence higher and scores with low confidence lower. Used to construct a MapMatch object.
    a MapMatch object.
    """
    def normalize(l):
        """
        Normalizes the values in a list, such that the sum(l) = 1.
        :param l: A list containing numeric values.
        :return: A list containing the normalized values.
        """
        total = sum(l)
        if total == 0:  # Cannot divide by zero!
            print('warning: sum of a list was 0 during normalization')
            return [0 for _ in l]
        return list(map(lambda value: value / total, l))

    bearing_scores = []
    speed_scores = []
    distance_scores = []

    max_distance = 0
    # Iterate over each candidate, which is a vertex id.
    for candidate in candidates:
        # Update the bearing score.
        delta_theta = abs(math.radians(point.bearing - network.node_heading[candidate]))
        bearing_scores.append((1 + math.cos(delta_theta)) / 2)

        # Update the speed score. If point.speed is 0, then discard speed as a factor by setting every score to 1.
        speed_scores.append(point.speed / network.node_speed_limit[candidate] if point.speed > 0 else 1)

        # Discover the distance between point and the candidate, and keep track of the maximum distance.
        distance_scores.append(real_distance(point.as_list(), network.node_locations[candidate]))
        if distance_scores[-1] > max_distance:
            max_distance = distance_scores[-1]

    # Update the distance scores as -1 * log(distance(point, candidate) / maximum(distance(point, candidate))).
    # Increasing the base of the log reduces the importance of the distance in the total evaluation.
    BASE = 10
    distance_scores = list(map(lambda d: -math.log(d / max_distance, BASE), distance_scores))

    # Component scores are combined into a composite score by taking the product then normalized.
    scores = normalize([b * s * d for b, s, d in zip(bearing_scores, speed_scores, distance_scores)])

    # Each component score is exponentiated and re-normalized. This is to increase the confidence of scores
    # that are highest, and to decrease the scores that are lowest, relative to each other.
    EXPONENT = 2
    scores = normalize(list(map(lambda score: score ** EXPONENT, scores)))
    return {candidate: score for candidate, score in zip(candidates, scores)}