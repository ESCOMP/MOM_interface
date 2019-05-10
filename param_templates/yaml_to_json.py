#!/usr/bin/env python

"""
YAML to JSON converter for MOM_Interface developers. This script is intented to be used for
converting default parameter files from yaml to json, since yaml is not a part of the standarti
Python library. The script should be used to update default.json whenever default.yaml file is 
modified. Adapted from the corresponding MARBL tool.
"""

import sys, os, logging
import argparse

parser = argparse.ArgumentParser(description="Convert MOM6 Runtime Parameter System file templates from"
                                             " YAML files to JSON")

parser.add_argument('-d', default='./',
                    help="path to manage_params directory")
args = parser.parse_args()

#######################################

def yaml_to_json(workdir):

    print(workdir)
    yaml_files = [os.path.join(workdir,"MOM_input.yaml"),
                  os.path.join(workdir,"input_nml.yaml"),
                  os.path.join(workdir,"input_data_list.yaml")]
    output_dir = os.path.join(workdir,"json")

    import json
    # This tool requires PyYAML, error if it is not available
    try:
        import yaml
    except:
        logger.error("Can not find PyYAML library")
        sys.exit(1)

    # Read YAML files
    for rel_file in yaml_files:
        filename = os.path.abspath(rel_file)
        yaml_filename = filename.split(os.path.sep)[-1]
        if not os.path.isfile(filename):
            logger.error("File not found: "+filename)
            sys.exit(1)
        with open(filename) as file_in:
            yaml_in = yaml.safe_load(file_in)

        # YAML consistency checks (MARBL expects these files to be formatted
        # in a specific way)
        #if yaml_filename.startswith("settings"):
        #    check_func=settings_dictionary_is_consistent
        #elif yaml_filename.startswith("diagnostics"):
        #    check_func=diagnostics_dictionary_is_consistent
        #else:
        #    logger.error("Can not find consistency check for %s" % filename)
        #    sys.exit(1)

        #logger.info("Running consistency check for %s" % filename)
        #if not check_func(yaml_in):
        #    logger.error("Formatting error in %s reported from %s" % (filename, check_func.__name__))
        #    sys.exit(1)

        # Write JSON file
        if yaml_filename[-5:].lower() == ".yaml":
            json_filename = yaml_filename[:-5] + ".json"
        elif yaml_filename[-4:].lower() == ".yml":
            json_filename = yaml_filename[:-4] + ".json"
        else:
            json_filename = yaml_filename + ".json"
        json_fullname = os.path.abspath(os.path.join(output_dir, json_filename))
        with open(json_fullname, "w") as file_out:
            logger.info('Writing %s' % json_fullname)
            json.dump(yaml_in, file_out, separators=(',', ': '), sort_keys=False, indent=3)

#######################################

if __name__ == "__main__":

    # Set up logging
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    logger = logging.getLogger("__name__")

    yaml_to_json(args.d)
