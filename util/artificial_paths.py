import datetime
import random
import graph_tool
import util.Shapes
import util.utils


def generate_path(network, section1=None, section2=None, min_path_length=30000, max_path_length=75000,
                  max_offset_distance=200, max_offset_heading=25, omit_factor=1):
    """
    Finds a path of DataPoints through the network from section1 to section2, or between two random sections, within
    a provided range for acceptable length. Skews the points randomly under a threshold to add noise to the data.

    :param section1: section ID of origin section. If not provided, a random section will be chosen.
    :param section2: section ID of destination section. If not provided, a random section will be chosen.
    :param min_path_length: minimum allowable length of path, in feet.
    :param max_path_length: maximum allowable length of path, in feet.
    :param max_offset_distance: the max number of feet that a point's lon/lat can be offset from the true path.
    :param max_offset_heading: the max number of degrees that a point's heading can be offset from the true heading.
    :param omit_factor: the integer x where you would like to include every xth point. If x is 1, all points included.
    :return: two lists of DataPoints, one with noise and one of the true path.
    """

    def random_vertex(exclude=-1):
        return random.sample(vertices - {exclude}, 1)[0]

    def length(vp):
        return network.shortest_distance_between_vertices(vp[0], vp[-1]) if vp != [] else 0

    def near_junction(v):
        # Return true if near a junction
        out_neighbors = [network.junctions[w] for w in [i for i in v.out_neighbors()]]
        in_neighbors = [network.junctions[x] for x in [j for j in v.in_neighbors()]]
        return any(out_neighbors) or any(in_neighbors) or network.junctions[v]

    cc = graph_tool.topology.label_largest_component(network.graph, True)
    vertices = {v for v in network.graph.vertices() if cc[v] and not near_junction(v)}

    section1 = graph_tool.util.find_vertex(network.graph, network.node_id, section1) if section1 else random_vertex()
    section2 = graph_tool.util.find_vertex(network.graph, network.node_id, section2) if section2 else random_vertex(section1)

    # Find path between two vertices that satisfies length requirements.
    vertex_path = network.find_vertex_path(section1, section2, True)[0]
    path_length = length(vertex_path)
    origin = random_vertex()
    vertex_path = network.find_vertex_path(origin, random_vertex(origin), True)[0]

    # If the path is too short, concatenate another path to it.
    while path_length < min_path_length:
        continuation = network.find_vertex_path(vertex_path[-1], random_vertex(vertex_path[-1]), True)[0]
        vertex_path.extend(continuation[1:])
        path_length += length(continuation)
    # If the path is too long, trim it to an allowable length.
    if path_length > max_path_length:
        appx_node_dist = path_length / len(vertex_path)
        # Ceiling divide by the approximate distance between two vertices to determine how many vertices to trim.
        diff = -(-(path_length - max_path_length) // appx_node_dist)
        vertex_path = vertex_path[:int(len(vertex_path) - diff)]

    vertex_path = [v for v in vertex_path if v in vertices]

    timestamp = datetime.datetime.now()

    # The true data is intended for path visualization. There is only a one-to-one relationship between true data
    # points and offset data points if omit_factor == 1 (no data is omitted from offset data).

    true_data = [util.Shapes.DataPoint(timestamp, network.node_speed_limit[v], network.node_locations[v][0],
                                       network.node_locations[v][1], network.node_heading[v]) for v in vertex_path]

    # Keep only every xth point, where x = omit_factor, to simulate sparse data.
    try:
        assert omit_factor <= len(vertex_path), 'omit_factor must be less than the length of the list'
        vertex_path = vertex_path[::omit_factor]
    except AssertionError:
        print("Omit factor too big.")
        vertex_path = vertex_path[::omit_factor//2]


    # Offset each vertex in the current path by a random amount within a given threshold.
    offset_data = [util.Shapes.DataPoint(timestamp, network.node_speed_limit[v],
                                         *util.Shapes.Point.as_tuple(
                                             util.utils.offset_point(util.Shapes.Point(network.node_locations[v][0],
                                                                                       network.node_locations[v][1],
                                                                                       network.node_heading[v]),
                                                                     random.randrange(max_offset_distance),
                                                                     random.randrange(359)))[:2],
                                         (network.node_heading[v] + random.randrange(-max_offset_heading,
                                                                                     max_offset_heading)) % 360)
                   for v in vertex_path]
    return offset_data, true_data


def export_artificial_data(offset_data, true_data, trip):
    """
    Formats the header and relevant information from offset and true data to be written to a .csv file.
    :param offset_data: a list of DataPoints
    :param true_data: a list of DataPoints. Note: not necessarily same length as offset_data.
    :param trip: an integer representing the trip number
    :return: (list of header, list of dictionaries for artificial data, list of dictionaries for true data)
    """
    data_header = ['probe_id', 'sample_date', 'lat', 'lon', 'heading', 'speed', 'probe_data_provider', 'trip_id']
    artificial_data = [{'probe_id': 0,
                        'sample_date': str(d.timestamp + datetime.timedelta(seconds=i)),
                        'lat': d.lat,
                        'lon': d.lon,
                        'heading': d.bearing,
                        'speed': d.speed,
                        'probe_data_provider': 'artificial',
                        'trip_id': trip
                        } for i, d in enumerate(offset_data)]
    true_data = [{'probe_id': 0,
                  'sample_date': str(d.timestamp + datetime.timedelta(seconds=i)),
                  'lat': d.lat,
                  'lon': d.lon,
                  'heading': d.bearing,
                  'speed': d.speed,
                  'probe_data_provider': 'artificial',
                  'trip_id': trip
                  } for i, d in enumerate(true_data)]
    return data_header, artificial_data, true_data


def multiple_artificial_paths(network, num_trips, section1=None, section2=None, min_path_length=30000,
                              max_path_length=50000, max_offset_distance=200, max_offset_heading=25, omit_factor=1):
    """
    Generate multiple artificial paths at once, ready to exported to a .csv file. Each path will have a unique
    trip_id to distinguish it.
    :param num_trips: number of trips to be generated
    :return: (list of header, list of dictionaries for artificial data, list of dictionaries for true data)
    """
    assert num_trips > 0, "Zero paths generated."

    fake_data = []
    real_data = []

    for i in range(num_trips):
        offset, true = generate_path(network, section1, section2, min_path_length, max_path_length, max_offset_distance,
                                     max_offset_heading, omit_factor)
        header, fake_trip, real_trip = export_artificial_data(offset, true, i)
        fake_data.extend(fake_trip)
        real_data.extend(real_trip)

    return header, fake_data, real_data
