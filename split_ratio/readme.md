Place path files in this directory. (A path file is a file with the naming structure *path*.csv)

Run reader.py and all paths will be evaluated between the entrance and exit nodes.

The entrance and exit nodes need to be manually adjusted in the Python script:

```
	name = 'example_name' # The name of the directory that the results should be written to.
	entrance_node = '1234' # Aimsun ID
	exit_node = '5678' # Aimsun ID
```