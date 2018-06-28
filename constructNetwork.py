from graph_tool.all import *
import math

from util import utils
from util import Shapes as shapes


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
        self.graph = Graph(directed=True)
        self.edge_weights = self.graph.new_edge_property("double")
        self.node_locations = self.graph.new_vertex_property("vector<double>")
        self.node_heading = self.graph.new_vertex_property("double")
        self.node_speed_limit = self.graph.new_vertex_property("double")
        self.node_id = self.graph.new_vertex_property("string")

        self.sections = dict()
        self.junctions = set()

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
            speed: the average speed at which the turn is taken in km/hr
            angle: the angle at which a turn is taken
            """
            "TODO: convert turn speed to mph"
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
        "TODO: The junction of both origin and destination must be the same. Assert this."
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
        self.junctions.add(junction_node)  # Each junction node is added to a set of junction nodes.

        # Update property map with the node's geolocation, speed, ID, and bearing.
        self.node_locations[junction_node] = [junction['geolocation']['lon'], junction['geolocation']['lat']]
        self.node_id[junction_node] = junction['junctionID']
        self.node_speed_limit[junction_node] = self.node_speed_limit[previous_node]

        # Look up geolocation of previous node, then compute heading to junction.
        previous_node_geolocation = self.node_locations[previous_node]
        previous_node_geolocation_mapping = {'lon': previous_node_geolocation[0], 'lat': previous_node_geolocation[1]}
        self.node_heading[junction_node] = utils.getHeading(previous_node_geolocation_mapping, junction['geolocation'])

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
        self.junctions.add(junction_node)  # Each junction node is added to a set of junction nodes.

        "Build a property map containing the geolocation, speed, ID, and bearing"
        self.node_locations[junction_node] = [junction['geolocation']['lon'], junction['geolocation']['lat']]
        self.node_id[junction_node] = junction['junctionID']
        self.node_speed_limit[junction_node] = self.node_speed_limit[next_node]

        # Look up geolocation of next node, then compute heading to junction.
        next_node_geolocation = self.node_locations[next_node]
        next_node_geolocation_mapping = {'lon': next_node_geolocation[0], 'lat': next_node_geolocation[1]}
        self.node_heading[next_node] = utils.getHeading(junction['geolocation'], next_node_geolocation_mapping)

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
        for vertices in self.sections.values():
            for source in vertices:
                edges_to_remove = []  # If an edge is split, it will need to be removed.
                for edge in self.graph.get_out_edges(source):
                    if self.edge_weights[edge] > maximum_distance:
                        target = edge[1]  # edge is a numpy array of [source, target, edge]. Select target.
                        edges_to_remove.append(edge)  # If an edge is split, the original edge should be removed.

                        new_edge_count = int(math.ceil(self.edge_weights[edge] / maximum_distance)) - 1
                        new_edge_distance = self.edge_weights[edge] / new_edge_count
                        current_point = shapes.Point.from_list(list(self.node_locations[source]) + [self.node_heading[target]])
                        previous_vertex = source
                        for _ in range(new_edge_count):
                            current_point = utils.offset_point(current_point, new_edge_distance, current_point.bearing)
                            current_vertex = self.graph.add_vertex()
                            """ Populate the property map for the new vertex. Inherit values from the target node,
                            unless the target node is a junction node. Then inherit values from the source. """
                            self.node_locations[current_vertex] = current_point.as_list()
                            self.node_heading[current_vertex] = current_point.bearing
                            property_vertex = source if target not in self.junctions else target
                            self.node_speed_limit[current_vertex] = self.node_speed_limit[property_vertex]
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

                map(self.graph.remove_edge, edges_to_remove)
        return

    def merge_edges(self, minimum_distance, maximum_angle_delta):
        """
        Decreases the number of nodes in the graph by recursively evaluating a section, merging sets of
        nodes and edges which do not span a minimum_distance and have an angular change less than
        maximum_angle_delta.
        :param minimum_distance:
        :param maximum_angle_delta:
        """
        return

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

    def export(self):
        """
        Returns a list of dictionaries containing the attributes of each vertex.
        """
        return [{'speed': self.node_speed_limit[v],
                 'lon': self.node_locations[v][0],
                 'lat': self.node_locations[v][1],
                 'heading': self.node_heading[v]} for v in self.graph.vertices()]