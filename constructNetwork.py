import json
import graph_tool.all as gt

from parser import get_JSON_strings
from graph_tool.all import *
from itertools import chain

class TrafficNetwork:
	"""
	A TrafficNetwork consists of a...
		- g, graph-tools network
		- sections, a set of sequences of nodes and edges in the network representing links
		- junctions, a set of nodes representing the meeting point between sections
	"""

	def __init__(self, junction_map, section_map):
		self.graph = Graph(directed=False)
		self.sections = dict()
		self.junctions = set()

		""" a junction is stored as a dictionary with the following mappings:
		  "junctionID": unique integer identifier 
		  "name": string of the name of the current junction
		  "signalized": whether or not there is a traffic signal at this junction
	      "geolocation": a dictionary mapping 'lat' and 'lon to a double value
	      "numEntrances": the number of sections which enter this junction
	      "entrances": list of all sectionIDs entering this junction
	      "numExits": the number of sections which leave this junction
	      "exits": list of all sectionIDs exiting this junction
	      "numTurns": the number ways there are to exit this junction
	      "turns": a list of dictionaries representing turns 
	    """
		for junction in junction_map['junctions']:
			for section in chain(junction['exits'], junction['entrances']):
				if section not in sections:
					### TODO: CHANGE SECTION JSON TO ASSOCIATE SECTIONID WITH SECTION
					self.sections[section] = buildSection(section_map['sections'][section])
				### Need to add the junction node and edge to the section, even if it exists
				
			for turn in junction['turns']
				### Connect relevant sections

	def buildSection(section):
	"""
	Converts a mapping of section data into a sequence of 
	connected nodes and edges, with no junction nodes.
	"""
	return 



def decodeJSON():
	"""
	Returns a mapping of sections and junctions from a 
	JSON string.
	"""
	json_strings = get_JSON_strings()
	return json.loads(json_strings['junction']), json.loads(json_strings['section'])



def addEntranceNode(section, coordinate_pair):
	"""
	Adds a edge and node to the end of a section, representing
	the the departure from a section into a node. 
	"""
	return 

def addExitNode(section, coordinate_pair):
	"""
	Adds an edge and node to the beginning of a section, representing
	the departure from a junction into a section.
	"""
	return 

def constructGraph(junction_map, section_map):
	"""
	Converts mappings of junctions and sections to a 
	graph-tools network. 
	"""
	graph = Graph(directed=False)

	graph = Graph(graph, graph)
	return 