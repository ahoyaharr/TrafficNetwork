## Installation Instructions

### Dependencies:
##### Graph Tools
[Homepage](https://graph-tool.skewed.de/)

###### Installation Instructions (Ubuntu):
1. Open `/etc/apt/sources.list` and add the following lines
    1. `deb http://downloads.skewed.de/apt/xenial xenial universe`
    2. `deb-src http://downloads.skewed.de/apt/xenial xenial universe`
2. Update the package manager by running 
    * `sudo apt-get update`
3. Validate the updated package manager by running
    * `sudo apt-key adv --keyserver pgp.skewed.de --recv-key 612DEFB798507F25`
4. Finally, install graph-tools by running
    * `sudo apt-get install python3-graph-tool`

##### Shapely
[Homepage](www.lfd.uci.edu/~gohlke/pythonlibs/#shapely)
1. Download the .whl file that corresponds to your version of Python and your machine.
    1. `pip3 install wheel`
    2. `pip3 install 'your_package_full_name'.whl`

##### Python 3

## Flow Chart
![Alt text](https://github.com/ahoyaharr/TrafficNetwork/blob/master/util/images/TrafficNetwork.png "Title")

## Usage Instructions
Extract junction and section information from an Aimsun model by running `~/data/aimsun_feature_extraction.py`. 

Import the data by calling `utils.decode_JSON`.

Construct a `TrafficNetwork` by calling `constructNetwork.TrafficNetwork(junction_data, section_data)`.

##### Map Matching, Path Inference
Example usage: import a data set located at  `~/data/probe_data.csv` and return the inferred path.
```python
junction_map, section_map = util.utils.decode_json()  # decode the .json files containing network information
network = TrafficNetwork(junction_map, section_map)  # construct the logical network
data = util.Shapes.DataPoint.convert_dataset(filename='probe_data.csv', subdirectory='data')  # import the data set
print('network constructed. number of nodes:', network.equalize_node_density(300, 30, greedy=True))

# construct the map matching object. matching happens on construction.
mm = mapMatch.MapMatch(network,
                       util.m_tree.tree.MTree,
                       map_match.scoring_fns.exp_distance_heading,
                       map_match.evaluation_fns.viterbi,
                       data)

```

##### Export

A network can export itself as a set of nodes, or as a set of edges.

```python
header, data = network.export_nodes()
util.export.export(header, data, 'nodes')
``` 

```python
header, data = network.export_edges()
util.export.export(header, data, 'edges')
```

A map matching object can export the candidates with their scores, and the inferred path.

```python
# convert the result into an exportable format
path_header, path_result = mm.export_path()

# convert the matches into an exportable format
match_header, match_result = mm.export_matches()

util.export.export(path_header, path_result, 'path')
util.export.export(match_header, match_result, 'candidates')
```

##### Visualising Candidates/Paths

To visualise exported candidates and paths, import the exported file into a PostGIS enabled database.

Create a new database connection in QGIS, and import the line geometry column as a vector layer.