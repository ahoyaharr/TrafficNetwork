from math import radians
from util.parser import read_file

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
        assert self.validate_point()

    def __repr__(self):
        return str(self.lon) + ',' + str(self.lat) + ' @ ' + str(self.bearing) + '\n'

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


class DataPoint(Point):
    def __init__(self, timestamp, speed, lon, lat, bearing):
        Point.__init__(self, lon, lat, bearing)
        self.speed = float(speed)
        self.timestamp = timestamp

    @staticmethod
    def convert_dataset(subdirectory, filename):
        points = []
        for line in read_file(s=filename, dir=subdirectory).splitlines():
            line = line.split(',')
            points.append(DataPoint(timestamp=line[1],
                                    speed=line[5],
                                    lon=line[3],
                                    lat=line[2],
                                    bearing=line[4]))
        return points
