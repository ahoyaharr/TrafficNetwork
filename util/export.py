import csv

import util.parser as p


def export(header, data, filename):
    """
    Write a CSV as defined by the header, and the dictionaries holding data to the ~/exports/ directory.
    :param header: A sequence of strings of length k, where each item is a column name
    :param data: A sequence of dictionaries each of length k, where each item in a row in the relation.
    :return: True if successful, otherwise False
    """
    assert type(data) is list and len(data) > 0  # Data must be a list containing data.
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
