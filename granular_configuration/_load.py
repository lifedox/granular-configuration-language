from __future__ import print_function, absolute_import
import os
from granular_configuration.yaml_handler import loads as yaml_loads
from granular_configuration.ini_handler import loads as ini_loads


def load_file(filename, obj_pairs_hook=None):
    try:
        ext = os.path.splitext(filename)[1]
        if ext == ".ini":
            loader = ini_loads
        else:
            loader = yaml_loads

        with open(filename, "r") as f:
            return loader(f.read(), obj_pairs_hook=obj_pairs_hook)
    except Exception as e:
        raise ValueError('Problem in file "{}": {}'.format(filename, e))
