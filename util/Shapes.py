from math import radians
import shapely.geometry as geom

from util.parser import read_csv


class Point:
    """
    Represents a WGS-84 GPS point.
    """
    def __init__(self, lon, lat, bearing=None):
        self.lon = float(lon)
        self.lon_as_rad = radians(self.lon)
        self.lat = float(lat)
        self.lat_as_rad = radians(self.lat)
        try:
            self.bearing = float(bearing)
        except TypeError:
            pass
        assert self.validate_point(), str(self.lon) + ', ' + str(self.lat) + ', ' + str(self.bearing)

    def __repr__(self):
        repr_string = str(self.lon) + ',' + str(self.lat)
        if self.bearing:
            repr_string += ' @ ' + str(self.bearing)
        repr_string += '\n'
        return repr_string

    @classmethod
    def from_list(cls, l):
        """
        :param l: A list in the form [lon, lat], or in the form [lon, lat, bearing]
        """
        try:
            return cls(l[0], l[1], l[2])
        except IndexError:
            return cls(l[0], l[1])

    @classmethod
    def from_dict(cls, d):
        """
        :param d: A dictionary with the entries lat, lon, heading
        """
        return cls(d['lon'], d['lat'], d['heading'])

    def validate_point(self):
        """
        :return: Determines if the point is a valid point
        """
        return -90 < self.lat < 90 and -180 < self.lon < 180

    def as_list(self):
        return [self.lon, self.lat]

    def as_tuple(self):
        return self.lon, self.lat, self.bearing

    def as_dict(self):
        return {'lon': self.lon, 'lat': self.lat, 'bearing': self.bearing}

    def as_geometry(self):
        return geom.Point(self.as_list()).wkb_hex

class DataPoint(Point):
    """
    Represents a HERE Probe Data Point. Inherits from Point.
    """

    def __init__(self, timestamp, speed, lon, lat, bearing):
        Point.__init__(self, lon, lat, bearing)
        self.speed = float(speed)
        self.timestamp = timestamp

    @classmethod
    def from_dict(cls, d):
        """
        :param d: A dictionary with the entries timestamp, speed, lat, lon, heading
        """
        return cls(d['timestamp'], d['speed'], d['lon'], d['lat'], d['heading'])

    def as_dict(self):
        """
        Returns a dictionary containing the attributes of the DataPoint. Not yet used.
        :return:
        """
        return {'timestamp': self.timestamp, 'speed': self.speed, 'lon': self.lon,
                'lat': self.lat, 'bearing': self.bearing}

    @staticmethod
    def convert_dataset(subdirectory, filename):
        """
        Converts a CSV of HERE probe data into a list of DataPoints.
        :param subdirectory:
        :param filename:
        :return: a list of DataPoints representing a path if there is only a single path in the file, or a
                 list of paths if there are many paths in the file.
        """
        """ Single path case. """
        if 'TRIP_ID' not in next(read_csv(filename, subdirectory)):
            return [DataPoint(timestamp=line['SAMPLE_DATE'],
                              speed=line['SPEED'],
                              lon=line['LON'],
                              lat=line['LAT'],
                              bearing=line['HEADING']) for line in read_csv(filename, subdirectory)]

        """ Multiple path case. """
        paths = {}
        for line in read_csv(filename, subdirectory):
            next_point = DataPoint(timestamp=line['SAMPLE_DATE'],
                                   speed=line['SPEED'],
                                   lon=line['LON'],
                                   lat=line['LAT'],
                                   bearing=line['HEADING'])
            try:
                paths[line['TRIP_ID']].append(next_point)
            except KeyError:
                paths[line['TRIP_ID']] = [next_point]

        return list(paths.values())
