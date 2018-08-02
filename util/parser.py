import os
import sys
import csv


def separator():
    UNIX_ENCODING = '/'
    return UNIX_ENCODING


def get_script_path(p):
    return os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + p

def get_JSON_files(path='data', absolute=False):
    # Returns a list of paths to uncorrected files in a directory.
    # path: the path to the directory
    # absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    # system_type: 'windows' or 'unix'
    files = [file for file in os.listdir(get_script_path(path)) if '.json' in file]
    return [get_script_path(path) + separator() + file for file in files] if absolute else files

def read_file(filename, dir='data'):
    file = open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + dir + separator() + filename)
    return file.read()

def read_csv(filename, dir='data'):
    with open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + dir + separator() + filename) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            yield row


def get_JSON_strings():
    """
    Maps the file name without the extension to the associated JSON string.
    """
    return {file.rsplit(".", 1)[0]: read_file(file) for file in get_JSON_files()}

