#!/usr/bin/env python

from __future__ import print_function
from collections import OrderedDict
import os
import json
import yaml

# Check if yaml and json files are equivalent
for f in os.listdir('./param_templates/'):
    if f.endswith(".yaml"):
        f_yaml = yaml.safe_load(open(os.path.join("./param_templates/",f), 'r'))
        f_json = json.load(open(os.path.join("./param_templates/json/",f.replace('yaml','json')), 'r'),
                        object_pairs_hook=OrderedDict)
        print("Checking ",f)
        assert (f_yaml==f_json), f"{f} and .json files appear to have different "\
                                 "information. If you have updated yaml file but not json file, "\
                                 "update it by running param_templates/yaml_to_json.py and then "\
                                 "push the updated json file."
        print("PASSED")
