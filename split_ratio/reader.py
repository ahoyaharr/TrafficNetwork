import csv
import os
from shutil import copyfile, rmtree
from re import search

### cli args
name = 'example_name'
entrance_node = '8009623'
exit_node = '22180'

# todo: fix cli 
# parser = argparse.ArgumentParser()
# parser.add_argument("-name", type=str,
#                     help="the output will be placed in a directory of this name")
# parser.add_argument("-in", type=str,
#                     help="the aimsun id of the entrance node")
# parser.add_argument("-out", type=str,
#                     help="the aimsun id of the exit node")
# args = parser.parse_args()

# assert args.name "-name is a required argument. example: -name i210-some_street_offramp"
# assert args.in "-in is a required argument. example: -in 1111"
# assert args.out "-out is a required argument. example: -out 5555"
#### end cli args


id1 = 'id1'
id2 = 'id2'
geom = 'line_geom'

total_cnt = 0
exit_cnt = 0
path_regex = r"(.*)path(.*).csv"



try:
    in_dir = os.getcwd()
    exit_dir = os.path.join(*[in_dir, name, 'exited']) # * operator feeds in each element of the list as an argument
    continue_dir = os.path.join(*[in_dir, name, 'continued'])
    out_dir = os.path.join(in_dir, name)
    os.makedirs(exit_dir)  
    os.makedirs(continue_dir) 
except Exception as e:
    if os.path.exists(out_dir) and not os.listdir(out_dir): # remove the directory tree if it is empty
        rmtree(out_dir)
    print('Unable to create directory:', str(e))
    exit()


# Work on all files matching the pattern *path.csv in the current working directory.
for f in (f for f in os.listdir(in_dir) if os.path.isfile(f) and search(path_regex, f)):
    with open(f, newline='') as csvfile:
        row_reader = csv.DictReader(csvfile, delimiter=',')
        
        nodes = set()
        for row in row_reader:
            nodes.add(row[id1])
            nodes.add(row[id2])

        if entrance_node in nodes:
            total_cnt += 1
            if exit_node in nodes:
                copyfile(os.path.join(in_dir, f), os.path.join(exit_dir, f))
            else:
                copyfile(os.path.join(in_dir, f), os.path.join(continue_dir, f))
                exit_cnt += 1

with open(os.path.join(out_dir, name + '_stats.txt'), "w") as textfile:
    stat = f'Statistics for {name}:\nTotal # paths: {total_cnt}\nTotal # exit: {exit_cnt}\nTotal # continue: {total_cnt - exit_cnt}\nSplit ratio: {exit_cnt / (total_cnt + .000000000000000000001)}'
    textfile.write(stat)
    print(stat)