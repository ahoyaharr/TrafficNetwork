from util.Shapes import Point
from util.export import export as file_export, build_linestring
import datetime

class MapMatch:
    def __init__(self, network, tree, score, evaluation, data):
        """
        :param network: An object containing a logical network of nodes and a distance function, vertex_distance.
        :param tree: A data structure which can be constructed using network.vertex_distance and populated by add_all.
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
        self.score_args = None
        self.evaluation_args = None
        self.matches = None
        self.result = None

    @classmethod
    def without_evaluation(cls, network, tree):
        """
        Creates a map matching object with a complete network and spatial index, but no data or algorithms.
        :param network:
        :param tree:
        :return:
        """
        dummy_score = lambda a, b, c, d: None
        dummy_eval = lambda a, b: None
        return cls(network, tree, dummy_score, dummy_eval, [])

    def specify_configuration(self, score_args=None, evaluation_args=None):
        """
        Specifies a set of arguments for each algorithm function to use.
        :param score_args: a tuple of arguments for the score function
        :param evaluation_args: a tuple of arguments for the evaluation function
        :return:
        """
        self.score_args = score_args
        self.evaluation_args = evaluation_args

    def match(self):
        """
        Matches each point in data to a position in network using a map matching algorithm
        defined by the score and evaluation functions.
        :return: The result, in the form of the return of evaluation.
        """
        print('mm: finding/scoring candidates...')
        if self.score_args:
            self.matches = [self.score(i, self.data, self.find_knn, self.network, *self.score_args)
                            for i in range(len(self.data))]
        else:
            self.matches = [self.score(i, self.data, self.find_knn, self.network) for i in range(len(self.data))]

        print('mm: searching for correct path...')
        if self.evaluation_args:
            self.result = self.evaluation(self.network, self.matches, *self.evaluation_args)
        else:
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
        """
        self.data = data
        return self.match()

    def batch_process(self, data_items, date="", score=None, evaluation=None, min_path=15):
        """
        :param data_items: a list of data
        :param date: optionally, a date string which will be prepended to the filename
        """
        cache_data = self.data, self.matches, self.result, self.score, self.evaluation  # Save current information
        if score:
            self.score = score
        if evaluation:
            self.evaluation = evaluation

        num_trips = 0

        if self.score and self.evaluation:
            print('beginning batch process on {0} data sets...'.format(len(data_items)))
            for trip, data in enumerate(data_items):
                num_trips +=1
                if not data:
                    print("no data being passed in ")
                    print("trip: ", trip)
                    break
                if len(data) < min_path:
                    print("too few points in trip", trip)
                    continue
                try:
                    self.update_data(data)
                    filename = "trip_" + str(num_trips) + "_" + date + "_" + self.network.node_id[self.result[0]] + "_to_" + self.network.node_id[self.result[-1]]
                except:
                    print("excepted out")
                    print(self.data)
                    continue
                # if len(self.result) == 0:
                #     print(self.data)
                file_export(*self.export_matches(), filename + "_matches")
                file_export(*self.export_path(), filename + "_path")
                print('\tfinished {0}...'.format(filename))
                print('completed {0} trips'.format(num_trips))
        self.data, self.matches, self.result, self.score, self.evaluation = cache_data  # Restore at end

    def export_matches(self):
        """
        Export the GPS point, and the geoposition and ID of the node which it was matched to a format suitable for
        util.export.export.
        :return: (list of string, list of dictionaries)
        """
        assert self.matches is not None
        header = ['gps_lon', 'gps_lat', 'gps_heading', 'match_lon', 'match_lat', 'match_heading', 'timestamp', 'score',
                  'gps_point', 'match_point', 'line_geom']
        result = []
        for probe_data, candidate in zip(self.data, self.matches):
            result.extend({'gps_lon': probe_data.as_list()[0],
                           'gps_lat': probe_data.as_list()[1],
                           'gps_heading': probe_data.bearing,
                           'match_lon': self.network.node_locations[v_id][0],
                           'match_lat': self.network.node_locations[v_id][1],
                           'match_heading': self.network.node_heading[v_id],
                           'timestamp': probe_data.timestamp,
                           'score': score,
                           'gps_point': probe_data.as_geometry(),
                           'match_point': Point.from_list(self.network.node_locations[v_id]).as_geometry(),
                           'line_geom': build_linestring(
                               probe_data.as_geometry(),
                               Point.from_list(self.network.node_locations[v_id]).as_geometry())
                           } for v_id, score in candidate.items())

        return header, result

    def export_path(self):
        assert self.result is not None
        # print("result: ", [self.network.node_id[v_id] for v_id in self.result])
        header = ['lon1', 'lat1', 'id1', 'lon2', 'lat2', 'id2', 'line_geom']
        if len(self.result) == 0:
            print(self.data)
            print("no result")
            return header, [{'lon1': None,
                             'lat1': None,
                             'lon2': None,
                             'lat2': None,
                             'line_geom': None}]
        if len(self.result) == 1:
            print(self.data)
            print("result length of 1")

        path = [{'lon1': first[0][0],
                 'lat1': first[0][1],
                 'id1': self.network.node_id[first[1]],
                 'lon2': second[0][0],
                 'lat2': second[0][1],
                 'id2': self.network.node_id[second[1]],
                 'line_geom': build_linestring(Point.from_list(first[0]).as_geometry(),
                                               Point.from_list(second[0]).as_geometry())
                 } for first, second in zip(((self.network.node_locations[v_id1], v_id1) for v_id1 in self.result[:-1]),
                                            ((self.network.node_locations[v_id2], v_id2) for v_id2 in self.result[1:]))]
        return header, path
