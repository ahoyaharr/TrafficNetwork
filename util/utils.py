import json
import math
import time
import util.Shapes

from util.parser import get_JSON_strings


def time_fn(fn, iterations, args):
    """
    Records the time it takes to run function fn on args iterations times.
    :param fn: The function to be executed.
    :param iterations: The number of times to run the function.
    :param args: The arguments to be passed into function fn.
    """
    start = time.time()
    for _ in range(iterations):
        fn(*args)
    t = (time.time() - start)
    print('time taken: %s' % t)
    return int(t)


def real_distance(cp1, cp2):
    """
    >>> 995.0 <= real_distance([-118.121438, 34.179766], [-118.118132, 34.179786]) <= 1000.0
    True

    Computes the distance in feet between two points using the Haversine Formula.
    :param cp1: A list in the form [lon1, lat1].
    :param cp2: A list in the form [lon2, lat2].
    :return: The distance in feet between two coordinates.
    """
    earth_radius = 6378.1
    KM_TO_FEET_CONST = 3280.84

    cp1 = list(map(math.radians, cp1))
    cp2 = list(map(math.radians, cp2))

    delta_lon = cp2[0] - cp1[0]
    delta_lat = cp2[1] - cp1[1]

    a = math.sin(delta_lat / 2) ** 2 + math.cos(cp1[1]) * math.cos(cp2[1]) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c * KM_TO_FEET_CONST


def get_heading(origin, destination):
    """
    Computes the heading between the origin and destination in degrees given the geolocation endpoints
    of the section as dictionaries of lat and lon.
    Zero degrees is true north, increments clockwise.
    """
    d_lon = math.radians(destination['lon'])
    d_lat = math.radians(destination['lat'])
    o_lon = math.radians(origin['lon'])
    o_lat = math.radians(origin['lat'])

    y = math.sin(d_lon - o_lon) * math.cos(d_lat)
    x = math.cos(o_lat) * math.sin(d_lat) - \
        math.sin(o_lat) * math.cos(d_lat) * math.cos(d_lon - o_lon)
    prenormalized = math.atan2(y, x) * 180 / math.pi

    return (prenormalized + 360) % 360  # map result to [0, 360) degrees


def decode_json():
    """
    Returns a mapping of sections and junctions from a JSON string.
    """
    json_strings = get_JSON_strings()
    return json.loads(json_strings['junction']), json.loads(json_strings['section'])


def offset_point(point, distance, bearing):
    """
    Given a point, find a new point which is distance away in direction of bearing.
    :param point: A point object.
    :param distance: The distance that the point should be offset, in feet.
    :param bearing: The angle of projection from the original point.
    :return: A point with the new coordinates, pointing in the direction that it was offset.
    """
    assert point.bearing is not None

    bearing = math.radians(bearing)

    R = 6378.1  # The radius of the world, in km.
    KM_TO_FEET_CONST = 3280.84  # The number of feet in a KM

    distance = distance / KM_TO_FEET_CONST

    lat2 = math.asin(math.sin(point.lat_as_rad) * math.cos(distance / R) +
                     math.cos(point.lat_as_rad) * math.sin(distance / R) * math.cos(bearing))

    lon2 = point.lon_as_rad + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(point.lat_as_rad),
                                         math.cos(distance / R) - math.sin(point.lat_as_rad) * math.sin(lat2))

    return util.Shapes.Point(math.degrees(lon2), math.degrees(lat2), math.degrees(bearing))


def angle_delta(a1, a2):
    """
    Computes the difference between two angles, accounting for overflow.
    :param a1: An angle
    :param a2: A different angle
    :return: The change between a1 and a2
    """
    # TODO: Determine if the change in angle is a positive or negative change
    return min((a1 - a2 + 360) % 360, (a2 - a1 + 360) % 360)