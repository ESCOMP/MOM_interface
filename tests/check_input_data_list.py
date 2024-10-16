#!/usr/bin/env python

import yaml
import re


# List of regex patterns to exclude known non-input files
EXCEPTIONS = ["._velocity_truncations"]


def filter_files(func):
    """This decorator function filters out all non-input file names from the set of file names
    returned by the decorated function. The decorator function removes all entries that are not
    strings, all entries that contain expandable variables other than $DIN_LOC_ROOT and $INPUTDIR.
    It also extracts only the file name from entries that contain relative or absolute paths.
    Finally, it filters out known exceptions.
    """

    def wrapper():

        files = func()

        # Remove all entries that are not strings
        files = {f for f in files if isinstance(f, str)}

        # In file names, replace all occurrences of DIN_LOC_ROOT:
        files = {
            f.replace("${DIN_LOC_ROOT}/", "").replace("{$DIN_LOC_ROOT}/", "")
            for f in files
        }

        # In file names, replace all occurrences of INPUTDIR:
        files = {
            f.replace("${INPUTDIR}/", "").replace("{$INPUTDIR}/", "") for f in files
        }

        # Remove all remaining files with expandable variables, since they most likely correspond to output file names
        files = {f for f in files if "$" not in f}

        # For entries corresponding to relative or absolute paths, retrieve only the file name:
        files = {f.split("/")[-1] for f in files}

        # Filter out known exceptions:
        for pattern in EXCEPTIONS:
            files = {f for f in files if not re.match(pattern, f)}

        return files

    return wrapper


@filter_files
def get_input_files_in_MOM_input():
    """
    This function reads the MOM_input.yaml file and extracts all input file names that it can detect.
    To do so, it looks for all parameters ending with _FILE and all parameters with values of the form '*.FILE: ...'.
    """

    MOM_input_yaml = yaml.safe_load(open("./param_templates/MOM_input.yaml", "r"))

    files = set()

    # Part 1 - Find all input parameters ending with _FILE
    for module in MOM_input_yaml:
        for varname in MOM_input_yaml[module]:
            if varname.endswith("_FILE"):
                value = MOM_input_yaml[module][varname]["value"]
                if isinstance(value, str):
                    files.add(value)
                elif isinstance(value, dict):
                    for key in value:
                        files.add(value[key])
                else:
                    raise ValueError("Unexpected value type: {}".format(type(value)))

    # Part 2 - Go through all parameters and gather those with values '*.FILE: ...'
    extract_filename = lambda x: x.split("FILE:")[1].split(",")[0]
    for module in MOM_input_yaml:
        for varname in MOM_input_yaml[module]:
            value = MOM_input_yaml[module][varname]["value"]
            if isinstance(value, str) and "FILE:" in value:
                files.add(extract_filename(value))
            elif isinstance(value, dict):
                for key in value:
                    if isinstance(value[key], str) and "FILE:" in value[key]:
                        files.add(extract_filename(value[key]))

    return files


@filter_files
def get_input_data_list_files():
    """
    This function reads the input_data_list.yaml file and extracts all input file names in it.
    """

    # a recursive function to extract all values from a nested dictionary:
    def extract_values(d):
        if isinstance(d, dict):
            for key in d:
                yield from extract_values(d[key])
        else:
            yield d

    input_data_list_yaml = yaml.safe_load(
        open("./param_templates/input_data_list.yaml", "r")
    )
    input_data_list = input_data_list_yaml["mom.input_data_list"]

    files = {
        v for file in input_data_list for v in extract_values(input_data_list[file])
    }

    return files


if __name__ == "__main__":
    mom_input_files = get_input_files_in_MOM_input()
    input_data_list_files = get_input_data_list_files()

    # Check if all files in input_data_list.yaml are also in MOM_input.yaml
    # If not, print the missing files and raise an error
    missing_files = mom_input_files - input_data_list_files
    if missing_files:
        raise ValueError(
            "Below parameter value(s) in MOM_input.yaml are suspected to be input file name(s), "
            "but are not present in input_data_list.yaml. If these are indeed input files, "
            "please add them to input_data_list.yaml. If not, please update this CI test module "
            "to exclude them from the check e.g., by adding them to the EXCEPTIONS list.\n\n  "
            + "\n  ".join(missing_files)
        )
