## Installation Instructions

### Dependencies:
##### Graph Tools
[Homepage](https://graph-tool.skewed.de/)

###### Installation Instructions (Ubuntu):
1. Open `/etc/apt/sources.list` and add the following lines
    * `deb http://downloads.skewed.de/apt/xenial xenial universe`
    * `deb-src http://downloads.skewed.de/apt/xenial xenial universe`
2. Update the package manager by running 
    * `sudo apt-get update`
3. Validate the updated package manager by running
    * `sudo apt-key adv --keyserver pgp.skewed.de --recv-key 612DEFB798507F25`
4. Finally, install graph-tools by running
    * `sudo apt-get install python3-graph-tool`

##### Python 3
- Install Python3 using `sudo apt-get install python3`

##### Shapely
- Install Shapely using `sudo apt-get install python3-shapely`



## Flow Chart
![alt text](util/images/flowchart.png "A flowchart demonstrating the
use of and relationships between main files in this repo.")

## Usage Instructions

##### Preparing the Data
Place data files in the folder `util/to_cluster`. Run `clustering.py`.
Clustered files will be written to this folder, with 'clustered_'
appended to the start of the file name.

Import the clustered data file as a delimited text layer in QGIS, using
 Layer -> Add Layer -> Delimited Text Layer.
Download all files found on Box at `I-210 Routing/TestShapes/taz` and
add `taz.shp` as a Vector Layer in QGIS.
To clip in QGIS, select the `Processing` menu at the top, and choose
`Toolbox` - a new menu will open. Under `Vector overlay`, select
`Clip`. Choose the clustered data layer as the input layer and the
taz as the clip layer, then run.

Once the clip has been completed, you should see a new layer called
`Clipped` appear in the Layers panel. Right click on the layer, select
`export`, then `Save features as...`, which should prompt a new window.
Select CSV to be the Format in the dropdown at the top of the menu.
Browse to select a location and file name to save the clipped data as.
This is the file that you will later run map matching and path
inference on.

##### Constructing the Network
If changes have been made to the network, extract updated junction and
section information from an Aimsun model using
`~/data/aimsun_feature_extraction.py`. Make sure you edit the 'path'
variable to reflect the path to your 'data' directory. Then, add the
file as a script and run it in Aimsun.

Import the junction and section data by calling `utils.decode_JSON`. Use
this to construct a `TrafficNetwork` by calling
`constructNetwork.TrafficNetwork()` on the junction and section data.

Notice that nodes are placed at each junction, so they are not
necessarily evenly spaced. Call `network.equalize_node_density()` to
remedy this, passing in the maximum allowed distance and angle change
as a threshold at which a new point will be added. We recommend using
300 feet and 30 degrees.

Example:
```python
junction_map, section_map = util.utils.decode_json()  # decode the .json files containing network information
network = TrafficNetwork(junction_map, section_map)  # construct the logical network
print('network constructed. number of nodes:', network.equalize_node_density(300, 30))
```

##### Map Matching and Path Inference

Place the file of data you would like to run map matching and path
inference on into the 'data' subdirectory. Call
`util.Shapes.DataPoint.convert_dataset` on a string of the filename. If
the data is stored in a different location, pass in the subdirectory
name as well.

Map match the data with the previously constructed network by calling
`mapMatch.MapMatch()` and passing in the network, a tree structure which
can be searched by nearest distance, a scoring function, an evaluation
function, and the previously imported data.

Example:
```python
data = util.Shapes.DataPoint.convert_dataset('probe_data.csv')  # import the data set

# construct the map matching object. matching happens on construction.
mm = mapMatch.MapMatch(network,
                       util.m_tree.tree.MTree,
                       map_match.scoring_fns.exp_distance_heading,
                       map_match.evaluation_fns.viterbi,
                       data)
```

To infer paths for a data set containing multiple trips, use `batch_process()`,
passing in the data, a filename for the export, a score function, and
an evaluation function.

Example:
```python
data = util.Shapes.DataPoint.convert_dataset('probe_data.csv')  # import the data set

mm.batch_process(data,
                 'matched_10_01_17',
                 score=map_match.scoring_fns.exp_distance_heading,
                 evaluation=map_match.evaluation_fns.viterbi)
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

A map matching object can export the candidates with their scores, and
the inferred path. Note that if you are using `batch_process` to match
and infer paths for a dataset with multiple trips, exports are already
handled for you. Each trip will be exported as a separate file.

```python
# convert the result into an exportable format
path_header, path_result = mm.export_path()

# convert the matches into an exportable format
match_header, match_result = mm.export_matches()

util.export.export(path_header, path_result, 'path')
util.export.export(match_header, match_result, 'candidates')
```

##### Visualizing Candidates/Paths

To visualize exported candidates and paths, we will import the exported file into a PostGIS enabled database.

In PgAdmin, right click on the database and select 'Query Tool'. Using
 the query tool, create a table using:
```SQL
CREATE TABLE path_table_name
    (
      lon1 float,
      lat1 float,
      lon2 float,
      lat2 float,
      line_geom geometry
    );
```
Refresh, then find this new table in the browser menu on the left.
Right click on it, and select Import/Export. Browse to find the file to
import, and choose 'yes' for Header.

To visualize matches, follow the same instructions as above except with
the following SQL query:
```SQL
CREATE TABLE matches_table_name
    (
      GPS_LON float,
      GPS_LAT float,
      MATCH_LON float,
      MATCH_LAT float,
      SCORE float,
      GPS geometry,
      MATCH geometry,
      LINE geometry
    )
```
Create a new database connection in QGIS if needed, and import the line
geometry column as a vector layer.