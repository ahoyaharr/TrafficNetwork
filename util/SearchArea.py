class SearchArea:
    def __init__(self, initial_point, distance, initial_width, fanout=90):
        """
        :param initial_point: A Point object from which the search originates
        :param distance: The maximum distance from the original point.
        :param initial_width: The initial width at the angle orthogonal to the initial point.
        :param fanout: The fanout angle. The default parameter gives a rectangle.
        """
        self.initial_point = initial_point
        self.distance = distance
        self.initial_width = initial_width
        self.fanout = fanout
        self.search_area = self.construct_hourglass()

    def construct_hourglass(self):
        """
        Constructs a search area by fanning out in either direction of the bearing of the point.
        :return: a list of Points, whose edges define a search area.
        """
        offset_to_fanout = 90 - self.fanout

        left_offset = self.offset_point(self.initial_point, self.initial_width, 90)
        left_positive_fanout = self.offset_point(left_offset, self.distance, -offset_to_fanout)
        left_negative_fanout = self.offset_point(left_offset, self.distance, offset_to_fanout)
        right_offset = self.offset_point(self.initial_point, self.initial_width, -90)
        right_positive_fanout = self.offset_point(right_offset, self.distance, offset_to_fanout)
        right_negative_fanout = self.offset_point(right_offset, self.distance, -offset_to_fanout)

        return [left_offset, left_positive_fanout, right_positive_fanout,
                right_offset, right_negative_fanout, left_negative_fanout]

    def contains(self, point):
        """
        Determines if the search area contains a point.
        :param point:
        :return:
        """
        last_point = self.search_area[-1]
        is_inside = False

        for p in self.search_area:
            dx = p.lon - last_point.lon

            if abs(dx) > 180:
                # Crossed Prime Meridian
                if point.lon > 0:
                    while last_point.lon < 0:
                        last_point.lon += 360
                    while p.lon < 0:
                        p.lon += 360
                else:
                    while last_point.lon > 0:
                        last_point.lon -= 360
                    while p.lon > 0:
                        p.lon -= 360

                dx = p.lon - last_point.lon

            if (last_point.lon <= point.lon < p.lon) or (p.lon < point.lon <= last_point.lon):
                gradient = (p.lat - last_point.lat) / dx
                intersection_at_lat = last_point.lat + ((point.lon - last_point.lon) * gradient)

                if intersection_at_lat > point.lat:
                    is_inside = not is_inside
            last_point = p

        return is_inside
