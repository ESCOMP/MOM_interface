#!/usr/bin/env python

from __future__ import print_function
from collections import OrderedDict
import json
import yaml

# Check if yaml and json files are equivalent
yaml_params = yaml.safe_load(open('./param_templates/default_params.yaml', 'r'))
json_params = json.load(open('./param_templates/json/default_params.json', 'r'),
                        object_pairs_hook=OrderedDict)
assert (yaml_params==json_params), "default_params.yaml and .json files appear to have different "+\
                                   "information. If you have updated yaml file but not json file, "+\
                                   "update it by running param_templates/yaml_to_json.py and then "+\
                                   "push the updated json file."


print("check_default_params: PASSED")
