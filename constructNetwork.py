import math

from itertools import groupby

from graph_tool.all import *

from util import Shapes as shapes
from util import utils
from util.export import build_linestring

SHORT_DISTANCE = 0.0000001

class TrafficNetwork:
    """
    A TrafficNetwork consists of a...
        - graph, a graph-tools network, which stores the following attributes in property maps
            - edge_weights, the distance traversed by a given edge
            - node_locations, the geolocation of a given node in the format [lon, lat]
            - node_heading, the bearing that a vehicle which has arrived at a node will have
            - node_speed_limit, the legal speed limit of a vehicle traveling to a node
            - node_id, the id of the section to which the node belongs
        - sections, a dictionary mapping an Aimsun section ID to the sequence of nodes representing that section
        - junctions, a set of nodes representing the meeting point between sections
    """

    def __init__(self, junction_map, section_map):
        print('network: constructing network...')
        self.graph = Graph(directed=True)

        self.edge_weights = self.graph.new_edge_property("double")

        self.node_width = self.graph.new_vertex_property("double")
        self.node_locations = self.graph.new_vertex_property("vector<double>")
        self.node_heading = self.graph.new_vertex_property("double")
        self.node_speed_limit = self.graph.new_vertex_property("double")
        self.node_id = self.graph.new_vertex_property("string")
        self.junctions = self.graph.new_vertex_property("bool")

        self.sections = dict()

        self.road_types = {'street': 1,
                           'freeway hov lane': 0,
                           'off ramp': 1,
                           'on ramp': 1,
                           'light rail track': 0,
                           'freeway connector': 1,
                           'freeway': 1,
                           'arterial': 1}

        """
        A junction is stored as a dictionary with the following mappings:
          junctionID: unique integer identifier 
          name: string of the name of the current junction
          signalized: boolean for whether or not there is a traffic signal at this junction
          geolocation: a dictionary mapping 'lat' and 'lon' to a double value
          numEntrances: the number of sections which enter this junction
          entrances: list of all sectionIDs entering this junction
          numExits: the number of sections which exit this junction
          exits: list of all sectionIDs exiting this junction
          numTurns: the number of ways there are to exit this junction
          turns: a list of dictionaries representing turns, further explained below.
        """
        for junction in junction_map['junctions']:
            utils.print_progress(len(junction_map['junctions']), prefix='constructing network')
            """
            For each section, create the section if it does not exist. Otherwise, perform a lookup on the section.
            Add the entrance/exit node-edge pair to each.
            Update the reference.
            """
            for exit in junction['exits']:
                if exit not in self.sections:
                    section = self.build_section(section_map['sections'][exit])
                else:
                    section = self.sections[exit]

                self.add_exit(section, junction)
                self.sections[exit] = section

            for entrance in junction['entrances']:
                if entrance not in self.sections:
                    section = self.build_section(section_map['sections'][entrance])
                else:
                    section = self.sections[entrance]

                self.add_entrance(section, junction)
                self.sections[entrance] = section

            """
            A turn is stored as a dictionary with the following mappings:
            turnID: unique integer identifier
            fromLaneRange: the inclusive range of lanes from the origin section for which the turn can be taken
            toLaneRange: the inclusive range of lanes to the destination section for which the turn will arrive at
            originSectionID: the section ID of the origin
            destinationSectionID: the section ID of the destination
            speed: the average speed at which the turn is taken in miles/hr
            angle: the angle at which a turn is taken
            """
            """
            Each turn defines a connection between two sections.
            For each turn, connect the two relevant sections. 
            """
            for turn in junction['turns']:
                self.connect(turn['originSectionID'], turn['destinationSectionID'])

    def connect(self, origin, destination):
        """
        Places an edge between two sections. The geolocation of the connecting junctions
        must be identical.
        """
        origin_section = self.sections[origin]
        destination_section = self.sections[destination]
        "The junction of both origin and destination must be the same."
        """A turn transitions a vehicle from the last segment of the origin to the first
        segment of the destination."""
        edge = self.graph.add_edge(origin_section[-1], destination_section[0])
        self.edge_weights[edge] = 0  # The distance between the same location is 0.
        return

    def build_section(self, section_map):
        """
        Constructs the nodes and edges of a section using a mapping of section data, and returns a
        reference to those nodes and edges in a sequence. Does not construct junction nodes/edges.
        
        A section is stored as a dictionary with the following mappings:
        lanes: a list of dictionaries containing mappings to information about each lane
        name: a string containing the name of the section
        numPoints: the number of points that defines the shape of a segment
        shape: a list of dictionaries containing information about the lat/lon/bearing of each point
        numLanes: the number of lanes in the section
        speed: the average speed of the section in miles/hr
        """
        section = []
        for coordinate_map in section_map['shape']:
            vertex = self.graph.add_vertex()

            # Build a property map containing the geolocation, speed, ID, and bearing.
            self.node_locations[vertex] = [coordinate_map['lon'], coordinate_map['lat']]
            self.node_id[vertex] = section_map['sectionID']
            self.node_speed_limit[vertex] = section_map['speed']
            self.node_width[vertex] = self.road_types[section_map['type']] * section_map['numLanes']

            if section:
                # The first node does not get a heading until the junction node has been added.
                self.node_heading[vertex] = coordinate_map['heading']
                previous_node = section[-1]
                edge = self.graph.add_edge(previous_node, vertex)
                previous_location = self.node_locations[previous_node]
                current_location = self.node_locations[vertex]
                self.edge_weights[edge] = utils.real_distance(previous_location, current_location)

            section.append(vertex)
        return section

    def add_entrance(self, section, junction):
        """
        Adds an edge and node to the end of a section, representing
        the departure from a section into a junction.
        """
        assert section  # The section may not be an empty sequence.

        previous_node = section[-1]
        junction_node = self.graph.add_vertex()

        # Update property map with the node's geolocation, speed, ID, and bearing.
        self.node_locations[junction_node] = [junction['geolocation']['lon'], junction['geolocation']['lat']]
        self.node_id[junction_node] = junction['junctionID']
        self.node_speed_limit[junction_node] = self.node_speed_limit[previous_node]
        self.node_width[junction_node] = self.node_width[previous_node]
        self.junctions[junction_node] = True

        # Look up geolocation of previous node, then compute heading to junction.
        previous_node_geolocation = self.node_locations[previous_node]
        previous_node_geolocation_mapping = {'lon': previous_node_geolocation[0], 'lat': previous_node_geolocation[1]}
        self.node_heading[junction_node] = utils.get_heading(previous_node_geolocation_mapping, junction['geolocation'])

        # Connect the section and junction node with an edge, weighted by the distance between them.
        edge = self.graph.add_edge(previous_node, junction_node)
        previous_node_location = self.node_locations[previous_node]
        junction_node_location = self.node_locations[junction_node]
        self.edge_weights[edge] = utils.real_distance(previous_node_location, junction_node_location)

        section.append(junction_node)
        return

    def add_exit(self, section, junction):
        """
        Adds an edge and node to the beginning of a section, representing
        the departure from a junction into a section.
        """
        assert section  # The section may not be an empty sequence.

        next_node = section[0]
        junction_node = self.graph.add_vertex()

        "Build a property map containing the geolocation, speed, ID, and bearing"
        self.node_locations[junction_node] = [junction['geolocation']['lon'], junction['geolocation']['lat']]
        self.node_id[junction_node] = junction['junctionID']
        self.node_speed_limit[junction_node] = self.node_speed_limit[next_node]
        self.node_width[junction_node] = self.node_width[next_node]
        self.junctions[junction_node] = True

        # Look up geolocation of next node, then compute heading to junction.
        next_node_geolocation = self.node_locations[next_node]
        next_node_geolocation_mapping = {'lon': next_node_geolocation[0], 'lat': next_node_geolocation[1]}
        self.node_heading[next_node] = utils.get_heading(junction['geolocation'], next_node_geolocation_mapping)

        # Connect the junction and section node with an edge, weighted by the distance between them.
        edge = self.graph.add_edge(junction_node, next_node)
        next_node_location = self.node_locations[next_node]
        junction_node_location = self.node_locations[junction_node]
        self.edge_weights[edge] = utils.real_distance(junction_node_location, next_node_location)

        section.insert(0, junction_node)
        return

    def split_edges(self, maximum_distance):
        """
        Increases the number of nodes in the graph by adding new nodes between each edge which carries a weight
        greater than maximum_distance. The new nodes inherit the attributes of the destination node, unless
        it is a junction in which case they inherit from the source node.
        :param maximum_distance: The maximum allowable length of an edge, in feet.
        """
        """ Iterate through the vertices of each section. For each vertex v, evaluate edges for which v is a source.
        If an edge of weight greater than maximum_distance, then split it. """
        for section_id in self.sections:
            utils.print_progress(len(self.sections), prefix='splitting edges')
            current_section = []  # Need to update the section data after splitting the edges.
            for source in self.sections[section_id]:
                current_section.append(source)
                edges_to_remove = []  # If an edge is split, it will need to be removed.
                for edge in self.graph.get_out_edges(source):
                    if self.edge_weights[edge] > maximum_distance:
                        target = edge[1]  # edge is a numpy array of [source, target, edge]. Select target.
                        edges_to_remove.append(self.graph.edge(edge[0], edge[
                            1]))  # If an edge is split, the original edge should be removed.

                        new_edge_count = int(math.ceil(self.edge_weights[edge] / maximum_distance))
                        new_edge_distance = self.edge_weights[edge] / new_edge_count
                        current_point = shapes.Point.from_list(
                            list(self.node_locations[source]) + [self.node_heading[target]])
                        previous_vertex = source
                        for _ in range(new_edge_count):
                            current_point = utils.offset_point(current_point, new_edge_distance, current_point.bearing)
                            current_vertex = self.graph.add_vertex()
                            current_section.append(current_vertex)  # The new vertex becomes a part of the section.
                            """ Populate the property map for the new vertex. Inherit values from the target node,
                            unless the target node is a junction node. Then inherit values from the source. """
                            self.node_locations[current_vertex] = current_point.as_list()
                            self.node_heading[current_vertex] = current_point.bearing
                            property_vertex = source if not self.junctions[target] else target
                            self.node_speed_limit[current_vertex] = self.node_speed_limit[property_vertex]
                            self.node_width[current_vertex] = self.node_width[property_vertex]
                            self.node_id[current_vertex] = self.node_id[property_vertex]

                            """ Create an edge between the previous vertex and the newly created vertex, 
                            and update the edge weight property map. """
                            current_edge = self.graph.add_edge(previous_vertex, current_vertex)
                            self.edge_weights[current_edge] = new_edge_distance

                            # The current vertex becomes the previous vertex in the next step.
                            previous_vertex = current_vertex

                        """ Create an edge between the last new vertex that was created and the target of the
                        original edge which is being split, and update the property map. """
                        self.edge_weights[self.graph.add_edge(previous_vertex, target)] = new_edge_distance
                list(map(self.graph.remove_edge, edges_to_remove))  # Remove all relevant edges
            self.sections[section_id] = current_section  # Update the section with the new vertices

    def merge_edges(self, section, maximum_distance, maximum_angle_delta, greedy=True):
        """
        Decreases the number of nodes in the graph by recursively evaluating a section, merging sets of
        nodes and edges which do not span a minimum_distance and have an angular change less than
        maximum_angle_delta.
        :param section: a list of vertices representing a section
        :param maximum_distance:
        :param maximum_angle_delta:
        :param greedy: the strategy used for selecting the partition
        :return: a tuple containing a list of edges to add, and a list of edges to remove.

        """

        def total_edge_angle(e1, e2):
            """
            Computes the total change in angle is given by calculating the sum of the difference in angle
            between each vertex pair.
            :param e1:
            :param e2:
            :return:
            """
            e1_source = section.index(e1[0])
            e2_target = section.index(e2[1])

            """ Given a pair of vertices, call angle_delta between them. """
            f = lambda pair: utils.angle_delta(self.node_heading[pair[0]], self.node_heading[pair[1]])

            """ Map f onto each pair of adjacent vertices, and return the abs of the summed result. """
            return abs(sum(map(f, zip(section[e1_source + 1:e2_target], section[e1_source + 2:e2_target + 1]))))

        def cumulative_edge_length(edge):
            """
            Returns the length of an edge, possibly a compound edge, by summing the weights of the edges
            between each pair of adjacent vertices.
            :param edge: An edge represented as a list.
            :return: The total length.
            """
            source = section.index(edge[0])
            target = section.index(edge[1])

            return sum(map(lambda pair: self.edge_weights[self.graph.edge(pair[0], pair[1])],
                           zip(section[source:target], section[int(source + 1):int(target + 1)])))

        def total_edge_length(e1, e2):
            """
            Compute the total distance traversed by two adjacent edges, either of which might be compound edges.
            :param e1: An edge represented as a list.
            :param e2: An adjacent edge, represented as a list.
            :return:
            """
            return cumulative_edge_length(e1) + cumulative_edge_length(e2)

        def permissible(e1, e2):
            """
            Determines if a merge is allowable. A merge is allowable if...
                - the target of the first edge is the source of the second edge (they are adjacent)
                - length(e1) + length(e2) < minimum_distance
                - delta(bearing_1, bearing_2) + delta(bearing_2, bearing_3) < maximum_angle_delta
            :param e1:
            :param e2:
            :return: True if permissible, else false.
            """
            return e1[1] == e2[0] and \
                   total_edge_length(e1, e2) < maximum_distance and \
                   total_edge_angle(e1, e2) < maximum_angle_delta

        def merge(e1, e2):
            """
            Merges edges e1 and e2 together.
            An edge is a sequence where the first two elements are [source, target]. An edge may have additional
            elements.
            :return: A three-element sequence representing an edge: [source, target, edgeID].
            """
            assert permissible(e1, e2)
            return [e1[0], e2[1], None]  # A merged edge has not been added, so it has no ID.

        def dp_partition(edges, to_add=[], to_remove=[]):
            """
            Recursively searches for the optimal partition of edges.
            :param edges:
            :return: A list of edges represented as lists to be added, and a list of edge ids to be removed.
            """
            if not edges:
                return to_add, [edge_id for edge_id in to_remove if edge_id is not None]

            """ Take the minimum of two results:
                - merge the first two edges, and consider all remaining edges
                - do not merge the first edge, and consider all remaining edges. """

            """ Possibility 1: Do not merge the first two edges. 
                Result: Partition on all of the remaining edges. Add the current edge to to_add, 
                        and the current edge to to_remove. """
            skip_edge = dp_partition(edges[1:], to_add + [edges[0]], to_remove + [edges[0][2]])

            """ Possibility 2: Merge the first two edges. 
                Result: Partition the newly merged edge with all of the remaining edges, we add 
                        nothing to to_add because the merged edge may be merged again, 
                        and we remove the two edges which were merged. """
            try:
                merge_edge = dp_partition([merge(edges[0], edges[1])] + edges[2:], to_add,
                                          to_remove + [edges[0][2]] + [edges[1][2]])
            except (AssertionError, IndexError) as exception:
                """ Either the first two edges in the pool cannot be merged, or there is only one edge remaining
                in the pool. In both cases, partition without merging. """
                merge_edge = skip_edge

            """ Return the result which adds the fewest edges. """
            return min(merge_edge, skip_edge, key=lambda pair: len(pair[0]))

        def greedy_partition(edges):
            current_subsection = edges[0]  # A list of edges forming the current subsection
            to_add = []  # A list of edges
            to_remove = []  # A list of vertices

            """ Determine if the current subsection and the next edge can be merged. If they can, then the
            target needs to be removed. Otherwise, the current subsection should be saved, and the next subsection
            begins with the current edge. """
            for edge in edges[1:]:
                if permissible(current_subsection, edge):
                    to_remove.append(edge[0])
                    current_subsection = merge(current_subsection, edge)
                else:
                    to_add.append(current_subsection)
                    current_subsection = edge

            to_add.append(current_subsection)

            return [(e, cumulative_edge_length(e)) for e in to_add], to_remove

        """ Construct the edges of a section, and then call a partitioning algorithm on the edges of a section. """
        l = len(section)
        section_edges = [[list(edge) for edge in self.graph.get_out_edges(source) if edge[1] == target][0]
                         for source, target in zip(section[0:l], section[1:l + 1])]

        return greedy_partition(section_edges) if greedy else dp_partition(section_edges)

    def equalize_node_density(self, maximum_distance, maximum_angle_delta, greedy=True):
        """
        Reduces the clustering of nodes in the network by splitting and merging edges.
        :param maximum_distance: The maximum distance that should exist between any two adjacent nodes.
        :param maximum_angle_delta: The maximum amount of angular change that can exist within a single section.
        :param greedy: Whether or not the greedy algorithm should be used. (Default: True. DP Takes too long.)
        :return: The number of nodes in the graph.
        """
        print('network: splitting long edges...')
        """ Split edges which are very long. """
        self.split_edges(maximum_distance)

        print('network: merging short edges...')
        vertices_to_remove = []
        edges_to_add = []
        """ Merge edges which are close together, and collect vertices/edges which should be removed/added. """
        for section_id in self.sections:
            utils.print_progress(len(self.sections), prefix='merging edges')
            new_edges, redundant_vertices = self.merge_edges(self.sections[section_id], maximum_distance,
                                                             maximum_angle_delta, greedy)
            vertices_to_remove.extend(redundant_vertices)
            edges_to_add.extend(new_edges)
            # Maintain the section list
            self.sections[section_id] = list(filter(lambda v: v not in redundant_vertices, self.sections[section_id]))

        """ Add the new edges and edge weights into the graph. """
        for edge, weight in edges_to_add:
            utils.print_progress(len(edges_to_add), prefix='adding edges')
            new_edge = self.graph.add_edge(edge[0], edge[1], add_missing=False)
            self.edge_weights[new_edge] = weight

        """ Removing vertices reindexes the vertices and edges of the graph. Need to maintain external data 
        structures to prevent data corruption. """
        original_indices = self.graph.vertex_index.copy()  # Property map will correct for reindexing
        self.graph.remove_vertex(vertices_to_remove, fast=True)
        #  Vertices have now been reindexed. Update each section with the new vertex IDs.
        for section_id in self.sections:
            utils.print_progress(len(self.sections), prefix='reindexing vertices')
            self.sections[section_id] = [find_vertex(self.graph, original_indices, v)[0] for v in
                                         self.sections[section_id]]

        return self.graph.num_vertices()

    def find_section_path(self, section_id1, section_id2):
        """
        Find a path between two sections.
        :param section_id1:
        :param section_id2:
        :return:
        """
        result = graph_tool.topology.shortest_path(
            self.graph, self.sections[str(section_id1)][0],
            self.sections[str(section_id2)][-1],
            weights=self.edge_weights)

        edges = result[1]

        for edge in edges:
            if self.edge_weights[edge] > 0:
                print(tuple([round(value, 6) for value in self.node_locations[edge.source()]]),
                      '@', self.node_id[edge.source()], '>', int(self.edge_weights[edge]), 'ft >',
                      tuple([round(value, 6) for value in self.node_locations[edge.target()]]),
                      '@', self.node_id[edge.target()])
            else:
                print('crossing junction', self.node_id[edge.source()], '@', tuple(self.node_locations[edge.source()]))

        return result

    def find_vertex_path(self, vertex_id1, vertex_id2, as_network_object):
        """
        Find the vertices and edges in a path between two vertices.
        :param vertex_id1:
        :param vertex_id2:
        :param as_network_object: whether or not the returned values should be integers or vertex/edge objects
        :return:
        """
        v1 = self.graph.vertex(vertex_id1)
        v2 = self.graph.vertex(vertex_id2)
        vertices, edges = graph_tool.topology.shortest_path(self.graph, v1, v2, weights=self.edge_weights)
        if v1 == v2:
            vertices = [v1, v1]
        if not as_network_object:
            vertices = [self.graph.vertex_index[vertex] for vertex in vertices]
            edges = [self.graph.edge_index[edge] for edge in edges]

        return vertices, edges

    def shortest_distance_between_vertices(self, v1, v2):
        if v1 == v2:
            return SHORT_DISTANCE
        return graph_tool.topology.shortest_distance(self.graph, v1, v2, weights=self.edge_weights)

    def get_exit_junction(self, id):
        """
        Given a section ID, returns the exit junction. 
        :param id: A section ID.
        """
        return self.sections[id][-1]

    def get_entrance_junction(self, id):
        """
        Given a section ID, returns the exit junction. 
        :param id: A section ID.
        """
        return self.sections[id][0]

    def get_junctions(self, section_id):
        """
        Given a section ID, returns the entrance and exit junctions. 
        :param section_id: The ID of the section to get the junctions for.
        """
        return self.get_entrance_junction(section_id), self.get_exit_junction(section_id)

    def vertex_distance(self, v1, v2):
        """
        Computes the real distance between two vertices, given their vertex IDs.
        """
        return utils.real_distance(self.node_locations[v1], self.node_locations[v2])

    def export_nodes(self):
        """
        Returns a list of dictionaries containing the attributes of each vertex.
        """
        return ['lon', 'lat', 'speed', 'heading'], \
               [{'speed': self.node_speed_limit[v],
                 'lon': self.node_locations[v][0],
                 'lat': self.node_locations[v][1],
                 'heading': self.node_heading[v]} for v in self.graph.vertices()]

    def export_edges(self):
        return ['lon1', 'lat1', 'lon2', 'lat2', 'weight', 'line_geom'], \
               [{'lon1': self.node_locations[e.source()][0],
                 'lat1': self.node_locations[e.source()][1],
                 'lon2': self.node_locations[e.target()][0],
                 'lat2': self.node_locations[e.target()][1],
                 'weight': self.edge_weights[e],
                 'line_geom': build_linestring(
                     shapes.Point.from_list(self.node_locations[e.source()]).as_geometry(),
                     shapes.Point.from_list(self.node_locations[e.target()]).as_geometry())
                 } for e in self.graph.edges()]

    def to_sections(self, path):
        """
        Converts a list of vertices to a list of sections
        :param path: a list of vertex ids
        :return:
        """
        return list(map(lambda tup: tup[0], groupby(path, key=lambda v_id: self.node_id[v_id])))