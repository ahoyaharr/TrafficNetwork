class MapMatch:
    def __init__(self, network, tree, score, evaluation, data):
        """
        :param network: An object containing a logical network of nodes and a distance function, vertex_distance.
        :param tree: A data structure which can be constructed vertex_distance and populated by add_all.
        :param score: A function which accepts a network, a point, and a sequence of candidate points.
        :param evaluation: A function which accepts a network and the result of calling score on each data point.
        :param data: Sequence of DataPoints.
        """
        self.network = network
        self.tree = tree(network.vertex_distance)
        self.tree.add_all(network.graph.get_vertices())
        self.score = score
        self.evaluation = evaluation
        self.data = data

    def match(self):
        """
        Matches each point in data to a position in network using a map matching algorithm
        defined by the score and evaluation functions.
        :return: The result, in the form of the return of evaluation.
        """
        scores = [self.score(p, self.find_knn(p.as_list()), self.network) for p in self.data]
        return self.evaluation(self.network, scores)

    def find_knn(self, point, num_results=20):
        """
        Given a point p, search for the k points nearest to p.
        :param point: A list in the form, [lon, lat]
        :param num_results: The number of neighbors to be found
        :return: A list of node IDs
        """
        """ Add point to the logical network, perform the k-nn search in the tree, and then remove the
        point from the logical network. """
        v = self.network.graph.add_vertex()
        self.network.node_locations[v] = point
        result = [item for item in self.tree.search(v, num_results) if item is not None]
        self.network.graph.remove_vertex(v, fast=True)
        return result
