from util.Shapes import Point
from util.export import export as file_export, build_linestring
import datetime

class MapMatch:
    def __init__(self, network, tree, score, evaluation, data):
        """
        :param network: An object containing a logical network of nodes and a distance function, vertex_distance.
        :param tree: A data structure which can be constructed network.vertex_distance and populated by add_all.
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

    @classmethod
    def without_evaluation(cls, network, tree):
        dummy_score = lambda a, b, c, d: None
        dummy_eval = lambda a, b: None
        return cls(network, tree, dummy_score, dummy_eval, [])

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
        return self.matches, self.result

    def find_knn(self, point, num_results=20):
        """
        Given a point p, search for the k points nearest to p.
        :param point: A list in the form, [lon, lat]
        :param num_results: The number of neighbors to be found
        :return: A list of node IDs
        """
        """ Add point to the logical network, perform the k-nn search in the tree, and then remove the
        point from the logical network. """
        #print('')

        #start=datetime.datetime.now()
        v = self.network.graph.add_vertex()
        self.network.node_locations[v] = point
        #print('cost of adding: {0}'.format(datetime.datetime.now() - start))

        #start=datetime.datetime.now()
        search_result = self.tree.search(v, limit=num_results)
        #print('cost of searching: {0}'.format(datetime.datetime.now() - start))


        #start=datetime.datetime.now()
        result = [item for item in search_result] #[item for item in search_result] #
        #print('cost of materializing: {0}'.format(datetime.datetime.now() - start))

        #start=datetime.datetime.now()
        self.network.graph.remove_vertex(v, fast=True)
        #print('cost of removing: {0}'.format(datetime.datetime.now() - start))
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

    def update_data(self, data):
        """
        Updates the map match object with a new data set, and finds the result.
        :param data:
        :return:
        """
        self.data = data
        return self.match()

    def batch_process(self, data_items, date="", score=None, evaluation=None):
        """
        :param data_items: a list of data
        :param date: optionally, a date string which will be prepended to the filename
        :return:
        """
        cache_data = self.data, self.matches, self.result, self.score, self.evaluation  # Save current information
        if score:
            self.score = score
        if evaluation:
            self.evaluation = evaluation

        print('beginning batch process on {0} data sets...'.format(len(data_items)))
        for data in data_items:
            self.update_data(data)
            filename = date + "_" + self.network.node_id[self.result[0]] + "_to_" + self.network.node_id[self.result[-1]]
            file_export(*self.export_matches(), filename + "_matches")
            file_export(*self.export_path(), filename + "_path")
            print('\tfinished {0}...'.format(filename))
        self.data, self.matches, self.result, self.score, self.evaluation = cache_data  # Restore at end

    def export_matches(self):
        """
        Export the GPS point, and the geoposition and ID of the node which it was matched to a format suitable for
        util.export.export.
        :return: (list of string, list of dictionaries)
        """
        assert self.matches is not None
        header = ['gps_lon', 'gps_lat', 'match_lon', 'match_lat', 'score', 'gps_point', 'match_point', 'line_geom']
        result = []
        for probe_data, candidate in zip(self.data, self.matches):
            result.extend({'gps_lon': probe_data.as_list()[0],
                           'gps_lat': probe_data.as_list()[1],
                           'match_lon': self.network.node_locations[v_id][0],
                           'match_lat': self.network.node_locations[v_id][1],
                           'score': score,
                           'gps_point': probe_data.as_geometry(),
                           'match_point': Point.from_list(self.network.node_locations[v_id]).as_geometry(),
                           'line_geom': build_linestring(
                               probe_data.as_geometry(),
                               Point.from_list(self.network.node_locations[v_id]).as_geometry())
                           } for v_id, score in candidate.items())

        return header, result

    def export_path(self):
        """
        Temporary.
        :return:
        """
        assert self.result is not None
        header = ['lon1', 'lat1', 'lon2', 'lat2', 'line_geom']
        path = [{'lon1': first[0],
                 'lat1': first[1],
                 'lon2': second[0],
                 'lat2': second[1],
                 'line_geom': build_linestring(Point.from_list(first).as_geometry(),
                                               Point.from_list(second).as_geometry())
                 } for first, second in zip((self.network.node_locations[v_id] for v_id in self.result[:-1]),
                                            (self.network.node_locations[v_id] for v_id in self.result[1:]))]
        return header, path
