import csv

import shapely.geometry as geom
from shapely.wkb import loads

import util.parser as p


def export(header, data, filename):
    """
    Write a CSV as defined by the header, and the dictionaries holding data to the ~/exports/ directory.
    :param header: A sequence of strings of length k, where each item is a column name
    :param data: A sequence of dictionaries each of length k, where each item in a row in the relation.
    :return: True if successful, otherwise False
    """
    assert type(data) is list and len(data) > 0, "No path found"  # Data must be a list containing data.
    assert type(header) is list and len(header) > 0  # Header must be a list containing data.

    for row in data:
        # Each row must be a dictionary, and the keys of the dictionary must be aligned with the header.
        assert len(header) == len(row.keys()) and type(row) is dict

    filepath = p.get_script_path('exports') + p.separator() + filename + '.csv'
    with open(filepath, 'w', newline='\n') as csvfile:
        f = csv.DictWriter(csvfile, fieldnames=header, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        f.writeheader()
        for row in data:
            f.writerow(row)


def build_linestring(p1, p2):
    """
    Constructs a hex-encoded linestring given two hex-encoded points
    :param p1:
    :param p2:
    :return:
    """
    p1 = loads(p1, hex=True)
    p2 = loads(p2, hex=True)
    return geom.LineString([p1, p2]).wkb_hex
