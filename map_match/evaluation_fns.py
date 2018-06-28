import copy
import math


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