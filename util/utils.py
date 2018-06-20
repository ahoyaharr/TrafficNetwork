import json
import math

from util.parser import get_JSON_strings


def real_distance(cp1, cp2):
    """
    Computes the distance in feet between two points.
    :param cp1: A list in the form [lon1, lat1]
    :param cp2: A list in the form [lon2, lat2]
    :return: the distance in meters between two coordinates.
    """

    earth_radius = 6373
    KM_TO_FEET_CONST = 3280.84

    cp1 = list(map(math.radians, cp1))
    cp2 = list(map(math.radians, cp2))

    delta_lon = cp2[0] - cp1[0]
    delta_lat = cp2[1] - cp1[1]

    a = math.sin(delta_lat / 2) ** 2 + math.cos(cp1[1]) * math.cos(cp2[1]) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c * KM_TO_FEET_CONST


def getHeading(origin, destination):
    """
    Computes the heading of a section in degrees relative to the x axis
    given the geolocation endpoints of the section as dictionaries of lat and lon.
    """
    dy = destination['lat'] - origin['lat']
    dx = destination['lon'] - origin['lon']
    return math.atan2(dy, dx) * 180 / math.pi


def decodeJSON():
    """
    Returns a mapping of sections and junctions from a
    JSON string.
    """
    json_strings = get_JSON_strings()
    return json.loads(json_strings['junction']), json.loads(json_strings['section'])