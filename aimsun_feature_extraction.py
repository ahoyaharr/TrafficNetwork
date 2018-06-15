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

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

def buildGeolocation(translator, coordinate_pair):
    """
    Converts an untranslated coordinate pair into a dictionary
    mapping 'lat'/'lon' -> coordinate value.
    """
    coordinate = translator.toDegrees(coordinate_pair)
    return {'lat': coordinate.x, 'lon': coordinate.y}

def buildJunctions(model):
    """
    Builds a dictionary containing information about the junctions
    in a model.
    """
    def buildTurn(turn_object):
        """
        Builds a dictionary containing information about a turn object.
        Inherits model from parent function buildJunctions.
        """
        turn_map = {}
        turn_map['turnID'] = turn_object.getId()

        origin = turn_object.getOrigin()
        turn_map['originSectionID'] = origin.getId()
        origin_object = model.getCatalog().find(origin.getId())
        num_origin_lanes = len(origin_object.getLanes())
        turn_map['fromLaneRange'] = num_origin_lanes - turn_object.getOriginToLane(), num_origin_lanes - turn_object.getOriginFromLane()

        destination = turn_object.getDestination()
        turn_map['destinationSectionID'] = destination.getId()
        destination_object = model.getCatalog().find(destination.getId())
        num_destination_lanes = len(destination_object.getLanes())
        turn_map['toLaneRange'] = num_destination_lanes - turn_object.getDestinationToLane(), num_destination_lanes - turn_object.getDestinationFromLane()

        TURN_SPEED_CONSTANT = 0.621371
        turn_map['speed'] = turn_object.getSpeed() * TURN_SPEED_CONSTANT
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
            junction['junctionID'] = JO.getId()
            junction['name'] = JO.getName()
            junction['externalID'] = JO.getExternalId()
            junction['geolocation'] = buildGeolocation(GKCoordinateTranslator(model), JO.getPosition())
            junction['signalized'] = bool(JO.getSignals())
            junction['numEntrances'] = JO.getNumEntranceSections()
            junction['entrances'] = [o.getId() for o in JO.getEntranceSections()]
            junction['numExits'] = JO.getNumExitSections()
            junction['exits'] = [o.getId() for o in JO.getExitSections()]
            turns = JO.getTurnings()
            junction['numTurns'] = len(turns)
            junction['turns'] = [buildTurn(turn_object) for turn_object in turns]
            junctions.append(junction)
    print 'Finished building junction map'
    return {'numJunctions': numJunctions, 'junctions': junctions}


def buildSections(model):
    def buildLane(lane_index):
        """
        Returns a dictionary mapping keys to the values in a lane object.
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
    sections = []

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType("GKSection")):
        numSections += len(types)
        for section_object in types.itervalues():
            section = {}
            section['sectionID'] = section_object.getId()
            section['name'] = section_object.getName()
            section['externalID'] = section_object.getExternalId()
            section['speed'] = section_object.getSpeed()

            lanes = section_object.getLanes()
            section['numLanes'] = len(lanes)
            section['lanes'] = [buildLane(lane_index) for lane_index in range(len(lanes))]
            shape = section_object.calculatePolyline()
            section['numPoints'] = len(shape)

            translator = GKCoordinateTranslator(model)
            section['shape'] = [buildGeolocation(translator, point) for point in shape]

            sections.append(section)
    print 'Finished building section map'
    return {'numSections': numSections, 'sections': sections}



def buildJSON(model, path):
    junction_map = buildJunctions(model)
    section_map = buildSections(model)

    junction_json = json.dumps(junction_map, indent=2, sort_keys=False)
    section_json = json.dumps(section_map, indent=2, sort_keys=False)

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

path='L:/arterial_detector_analysis_files'

buildJSON(model, path)