import json

from graph_tool.all import *

from parser import get_JSON_strings


class TrafficNetwork:
    """
    A TrafficNetwork consists of a...
        - graph, a graph-tools network, which stores the following attributes in property maps
            - edge_weights, the distance traversed by a given edge
            - node_locations, the geolocation of a given node
            - node_heading, the bearing that a vehicle which has arrived at a node will have
            - node_speed_limit, the legal speed limit of a vehicle traveling to a node
        - sections, a dictionary mapping an Aimsun section ID to the sequence of nodes representing that section
        - junctions, a set of nodes representing the meeting point between sections
    """

    def __init__(self, junction_map, section_map):
        self.graph = Graph(directed=True)
        self.edge_weights = self.graph.new_edge_property("double")
        self.node_locations = self.graph.new_vertex_property("vector<double>")
        self.node_heading = self.graph.new_vertex_property("vector<double>")
        self.node_speed_limit = self.graph.new_vertex_property("double")

        self.sections = dict()
        self.junctions = set()

        """ a junction is stored as a dictionary with the following mappings:
          "junctionID": unique integer identifier 
          "name": string of the name of the current junction
          "signalized": whether or not there is a traffic signal at this junction
          "geolocation": a dictionary mapping 'lat' and 'lon to a double value
          "numEntrances": the number of sections which enter this junction
          "entrances": list of all sectionIDs entering this junction
          "numExits": the number of sections which leave this junction
          "exits": list of all sectionIDs exiting this junction
          "numTurns": the number ways there are to exit this junction
          "turns": a list of dictionaries representing turns """
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

            """ a turn is stored as a dictionary with the following mappings:
            "turnID": unique integer identifier
            "fromLaneRange": the inclusive range of lanes from the origin section for which the turn can be taken
            "toLaneRange": the inclusive range of lanes to the destination section for which the turn will arrive at
            "originSectionID": the section ID of the origin
            "destinationSectionID": the section ID of the destination
            "speed": the average speed at which the turn is taken
            "angle": the angle at which a turn is taken
            """

            """
            Each turn defined a connection between two sections.
            For each turn, connect the two relevant sections. 
            """
            for turn in junction['turns']:
                self.connect(turn['originSectionID'], turn['destinationSectionID'])

    def real_distance(self, v1, v2):
        return None

    def connect(self, origin, destination):
        """
        Places an edge between two sections. The geolocation of the connecting junctions
        must be identical.
        """
        origin_section = self.sections[origin]
        destination_section = self.sections[destination]
        "TODO: The junction of both origin and destination must be the same. Assert this."
        """A turn transitions a vehicle from the last segment of a the origin to the first
        segment of the destination"""
        self.graph.add_edge(origin_section[-1], destination_section[0])
        return

    def build_section(self, section_map):
        """
        Constructs the nodes and edges of a section using
        a mapping of section data, and returns a reference to those
        nodes and edges in a sequence. Does not construct junction nodes/edges.
        """
        """ a section is stored as a dictionary with the following mappings:
        "lanes": a list of dictionaries containing mappings to information about each lane
        "name": a string containing the name of the section
        "numPoints": the number of points that defines the shape of a segment
        "shape": a list of dictionaries containing information about the lat/lon/bearing of each point
        "numLanes": the number of lanes in the section
        "speed": the average speed of the section in miles/hr
        """
        section = []
        for coordinate_map in section_map['shape']:
            "Build a property map containing the geolocation, speed, name, and bearing"
            vertex = self.graph.add_vertex()
            if section:
                self.graph.add_edge(section[-1], vertex)
            section.append(vertex)
        return section

    def add_entrance(self, section, junction):
        """
        Adds an edge and node to the end of a section, representing
        the departure from a section into a junction.
        """
        assert section  # The section may not be an empty sequence.

        "Build a property map containing the geolocation, speed, name, and bearing"
        junction_node = self.graph.add_vertex()
        self.graph.add_edge(section[-1], junction_node)
        section.append(junction_node)
        return

    def add_exit(self, section, junction):
        """
        Adds an edge and node to the beginning of a section, representing
        the departure from a junction into a section.
        """
        assert section  # The section may not be an empty sequence.

        "Build a property map containing the geolocation, speed, name, and bearing"
        junction_node = self.graph.add_vertex()
        self.graph.add_edge(junction_node, section[0])
        section.insert(0, junction_node)
        return


def decodeJSON():
    """
    Returns a mapping of sections and junctions from a
    JSON string.
    """
    json_strings = get_JSON_strings()
    return json.loads(json_strings['junction']), json.loads(json_strings['section'])


junction_map, section_map = decodeJSON()
network = TrafficNetwork(junction_map, section_map)

graph_draw(network.graph)
