#!/usr/bin/env python

import yaml
import svn.remote as sr
from check_input_data_list import (
    get_input_files_in_MOM_input,
    get_input_data_list_files,
)

if __name__ == "__main__":

    # Read in the MOM_input.yaml file and extract all input file names
    MOM_input_yaml = yaml.safe_load(open("./param_templates/MOM_input.yaml", "r"))
    MOM_input_files = get_input_files_in_MOM_input(MOM_input_yaml)

    # Read in the input_data_list.yaml file and extract all input file names
    input_data_list_yaml = yaml.safe_load(
        open("./param_templates/input_data_list.yaml", "r")
    )
    input_data_list_files = get_input_data_list_files(
        input_data_list_yaml, MOM_input_files
    )

    # all mom input file names in svn inputdata repository
    r = sr.RemoteClient(
        "https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/ocn/mom/"
    )
    repo_files = {f["name"] for relpath, f in r.list_recursive() if f["kind"] == "file"}

    # File names missing in the svn repository
    missing_files = (
        set(
            filename
            for filelist in input_data_list_files.values()
            for filename in filelist
        )
        - repo_files
    )
    if missing_files:
        raise ValueError(
            "Below file names are listed in input_data_list.yaml but are missing "
            "in the svn inputdata repository. If these files are not needed, "
            "please remove them from input_data_list.yaml. If they are needed, "
            "please import them to the svn repository.\n\n  "
            + "\n  ".join(missing_files)
        )
    else:
        print("All files in input_data_list.yaml are present in the svn repository.")
