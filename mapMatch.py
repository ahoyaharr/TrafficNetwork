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
        print('mm: constructing tree...')
        self.tree = tree(distance_function=network.vertex_distance)
        self.tree.add_all(network.graph.get_vertices())
        self.score = score
        self.evaluation = evaluation
        self.data = data
        self.matches = None
        self.result = None
        self.match()

    def match(self):
        """
        Matches each point in data to a position in network using a map matching algorithm
        defined by the score and evaluation functions.
        :return: The result, in the form of the return of evaluation.
        """
        print('mm: finding/scoring candidates...')
        self.matches = [self.score(i, self.data, self.find_knn, self.network) for i in range(len(self.data))]
        print('mm: searching for correct path...')
        self.result = self.evaluation(self.network, self.matches)
        return self.result

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
        result = [item for item in self.tree.search(v, limit=num_results) if item is not None]
        self.network.graph.remove_vertex(v, fast=True)
        return result

    def update_fn(self, score=None, evaluation=None):
        """
        Updates the functions used in the map matching algorithm and calls match again.
        :param score: a score function
        :param evaluation: an evaluation function
        """
        self.score = score if score is not None else self.score
        self.evaluation = evaluation if evaluation is not None else self.evaluation
        self.match()

    def export_matches(self):
        """
        Export the GPS point, and the geoposition and ID of the node which it was matched to a format suitable for
        util.export.export.
        :return: (list of string, list of dictionaries)
        """
        header = ['gps_lon', 'gps_lat', 'match_lon', 'match_lat', 'score']
        result = []
        for probe_data, candidate in zip(self.data, self.matches):
            result.extend({'gps_lon': probe_data.as_list()[0],
                           'gps_lat': probe_data.as_list()[1],
                           'match_lon': self.network.node_locations[v_id][0],
                           'match_lat': self.network.node_locations[v_id][1],
                           'score': score} for v_id, score in candidate.items())
        return header, result

    def export_path(self):
        """
        Temporary.
        :return:
        """
        header = ['lon1', 'lat1', 'lon2', 'lat2']
        path = [{'lon1': first[0],
                 'lat1': first[1],
                 'lon2': second[0],
                 'lat2': second[1]} for first, second in
                zip((self.network.node_locations[v_id] for v_id in self.result[:-1]), (self.network.node_locations[v_id] for v_id in self.result[1:] ))]
        return header, path

