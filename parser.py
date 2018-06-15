import os
import sys

def separator():
    UNIX_ENCODING = '/'
    return UNIX_ENCODING

def get_files(path='data', absolute=False):
    # Returns a list of paths to uncorrected files in a directory.
    # path: the path to the directory
    # absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    # system_type: 'windows' or 'unix'
    def get_script_path(p):
        return os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + p

    files = [file for file in os.listdir(get_script_path(path)) if '.json' in file]
    return [get_script_path(path) + separator() + file for file in files] if absolute else files

def read_file(s):
    file = open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + 'data' + separator() + s)
    return file.read()


def get_JSON_strings():
	""" 
	Maps the file name without the extension to the associated JSON string.
	"""
	return {file.rsplit(".", 1)[0]: read_file(file) for file in get_files()} 
