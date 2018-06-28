from PyANGBasic import *
from PyANGKernel import *
from PyANGGui import *
from PyANGAimsun import *
#from AAPI import *

import datetime
import pickle
import sys
import csv
import os
import json
import math

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

MPH_CONSTANT = 0.62137119 #multiply km/hr to convert to mph


def build_geolocation(translator, coordinate_pair):
    """
    Converts an untranslated coordinate pair into a dictionary
    mapping 'lon'/'lat' -> coordinate value.
    """
    coordinate = translator.toDegrees(coordinate_pair)
    return {'lon': coordinate.x, 'lat': coordinate.y}

def get_heading(origin, destination):
    """
    Computes the heading between the origin and destination in degrees given the geolocation endpoints
    of the section as dictionaries of lat and lon.
    Zero degrees is true north, increments clockwise.
    """
    dlon = math.radians(destination['lon'])
    dlat = math.radians(destination['lat'])
    olon = math.radians(origin['lon'])
    olat = math.radians(origin['lat'])

    y = math.sin(dlon - olon) * math.cos(dlat)
    x = math.cos(olat) * math.sin(dlat) - \
        math.sin(olat) * math.cos(dlat) * math.cos(dlon - olon)
    prenormalized = math.atan2(y, x) * 180 / math.pi

    return (prenormalized + 360) % 360 # map result to [0, 360) degrees

def build_junctions(model):
    """
    Builds a dictionary containing information about the junctions
    in a model.
    """
    def build_turn(turn_object):
        """
        Builds a dictionary containing information about a turn object.
        Inherits model from parent function build_junctions.
        Units for turn speed is mph.
        """
        turn_map = {}
        turn_map['turnID'] = str(turn_object.getId())

        origin = turn_object.getOrigin()
        turn_map['originSectionID'] = str(origin.getId())
        origin_object = model.getCatalog().find(origin.getId())
        num_origin_lanes = len(origin_object.getLanes())
        turn_map['fromLaneRange'] = num_origin_lanes - turn_object.getOriginToLane(), num_origin_lanes - turn_object.getOriginFromLane()

        destination = turn_object.getDestination()
        turn_map['destinationSectionID'] = str(destination.getId())
        destination_object = model.getCatalog().find(destination.getId())
        num_destination_lanes = len(destination_object.getLanes())
        turn_map['toLaneRange'] = num_destination_lanes - turn_object.getDestinationToLane(), num_destination_lanes - turn_object.getDestinationFromLane()

        turn_map['speed'] = turn_object.getSpeed() * MPH_CONSTANT
        turn_map['angle'] = turn_object.calcAngleBridge()
        turn_map['type'] = turn_object.getDescription()

        return turn_map

    print 'Building junction map'
    numJunctions = 0
    junctions = []

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKNode")):
        numJunctions += len(types)
        for JO in types.itervalues(): 
            junction = {}
            junction['junctionID'] = str(JO.getId())
            junction['name'] = JO.getName()
            junction['externalID'] = JO.getExternalId()
            junction['geolocation'] = build_geolocation(GKCoordinateTranslator(model), JO.getPosition())
            junction['signalized'] = bool(JO.getSignals())
            junction['numEntrances'] = JO.getNumEntranceSections()
            junction['entrances'] = [str(o.getId()) for o in JO.getEntranceSections()]
            junction['numExits'] = JO.getNumExitSections()
            junction['exits'] = [str(o.getId()) for o in JO.getExitSections()]
            turns = JO.getTurnings()
            junction['numTurns'] = len(turns)
            junction['turns'] = [build_turn(turn_object) for turn_object in turns]
            junctions.append(junction)
    print 'Finished building junction map'
    return {'numJunctions': numJunctions, 'junctions': junctions}


def build_sections(model):
    def build_lane(lane_index):
        """
        Returns a dictionary mapping keys to the values in a lane object.
        Units for length and width are feet and speed is mph.
        """
        LANE_CONST = 3.28084
        lane = {}
        lane['length'] = section_object.getLaneLength(lane_index) * LANE_CONST
        lane['width'] = section_object.getLaneWidth(lane_index) * LANE_CONST
        lane_object = section_object.getLane(lane_index)
        lane['isFullLane'] = lane_object.isFullLane()
        lane['offset'] = lane_object.getInitialOffset() * LANE_CONST
        return lane

    print 'Building section map'
    numSections = 0
    sections = {}

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKSection")):
        numSections += len(types)
        for section_object in types.itervalues():
            section = {}
            sectionID = str(section_object.getId())
            section['sectionID'] = sectionID
            section['name'] = section_object.getName()
            section['externalID'] = section_object.getExternalId()
            section['speed'] = section_object.getSpeed() * MPH_CONSTANT

            lanes = section_object.getLanes()
            section['numLanes'] = len(lanes)
            section['lanes'] = [build_lane(lane_index) for lane_index in range(len(lanes))]
            shape = section_object.calculatePolyline()
            section['numPoints'] = len(shape)

            translator = GKCoordinateTranslator(model)
            section['shape'] = [build_geolocation(translator, point) for point in shape]

            previous = section['shape'][0]
            previous['heading'] = None

            for i in range (1, len(shape)):
                curr = section['shape'][i]
                curr['heading'] = get_heading(previous, curr)
                previous = curr

            sections[sectionID] = section
    print 'Finished building section map'
    return {'numSections': numSections, 'sections': sections}



def build_json(model, path):
    junction_map = build_junctions(model)
    section_map = build_sections(model)

    junction_json = json.dumps(junction_map, indent=2)
    section_json = json.dumps(section_map, indent=2)

    junction_path = path + separator() + 'junction.json'
    print 'Writing', junction_path
    with open (junction_path, 'w') as text_file:
        text_file.write(junction_json)

    section_path = path + separator() + 'section.json'
    print 'Writing', section_path
    with open (section_path, 'w') as text_file:
        text_file.write(section_json)
        

def separator():
    return WINDOWS_ENCODING if SYSTEM_TYPE == 'windows' else UNIX_ENCODING


gui=GKGUISystem.getGUISystem().getActiveGui()
model = gui.getActiveModel()

path='C:\Users\Serena\connected_corridors\TrafficNetwork\data'

build_json(model, path)