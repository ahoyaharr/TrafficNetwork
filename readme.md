## Installation Instructions

### Dependencies:
##### Graph Tools
[Homepage](https://graph-tool.skewed.de/)

### Usage Instructions
Extract junction and section information from an Aimsun model by running `~/data/aimsun_feature_extraction.py`. 

Import the data by calling `utils.decode_JSON`.

Construct a `TrafficNetwork` by calling `constructNetwork.TrafficNetwork(junction_data, section_data)`.


##### Map Matching, Path Inference
Equalise the node density in the network by calling `TrafficNetwork.equalize_node_density`.

Construct a `MapMatch` by calling `mapMatch.MapMatch(TrafficNetwork, SpatialIndex, ScoreFn, EvaluationFn, DataPoints)`. 

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