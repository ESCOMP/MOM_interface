#!/usr/bin/env python

import yaml
import re


# List of filename regex patterns to exclude from the check between MOM_input.yaml and input_data_list.yaml
EXCEPTIONS = [
    "._velocity_truncations",
]


def extract_values(d):
    """Given a dictionary or value, this function recursively extracts all values from the dictionary."""
    if isinstance(d, dict):
        for key in d:
            yield from extract_values(d[key])
    else:
        yield d


def _retrieve_input_filenames(varname, values):
    """Given a variable name and values pair from a param template dict, this function extracts all
    input file names from the values. It attempts to filter out non-file names, output file names,
    and known exceptions. It also retains only the file names from relative/absolute paths.

    Parameters
    ----------
    varname : str
        The variable name from the param template dict.
    values : list
        A list of values for the variable name from the param template dict.

    Returns
    -------
    values : list
        A list of input file names extracted from the values.
    """
    # Remove all entries that are not strings
    values = [v for v in values if isinstance(v, str)]

    # Retain only values that are (most likely) file names: ending with '.nc' or '.txt' or containing 'FILE:'
    # or containing ':<filename>.nc' or ':<filename>.txt'
    values = [
        v
        for v in values
        if "FILE:" in v
        or re.search(":[\w\-\.]+\.(nc|txt)", v)
        or v.endswith(".nc")
        or v.endswith(".txt")
        or varname.endswith("_FILE")
        or v.strip("${}").endswith("_FILE")
    ]

    # Extract the file names from values of the form 'WORD:FILENAME[,]'
    values = [v.split(":")[1].split(",")[0].strip() if ":" in v else v for v in values]

    # If relative/absolute paths, retain only the file names
    values = [v.split("/")[-1] for v in values]

    # Exclude entries containing CASE-specific XML variables, as these indicate output files rather than inputs.
    values = [v for v in values if not re.search(r"\$\{.*CASE.*\}|\{\$.*CASE.*\}", v)]

    # Filter out known exceptions:
    for pattern in EXCEPTIONS:
        values = [v for v in values if not re.search(pattern, v)]

    return values


def get_input_files_in_MOM_input(MOM_input_yaml):
    """
    This function reads the MOM_input.yaml file and extracts all input file names that it can detect.

    Parameters
    ----------
    MOM_input_yaml : dict
        The dictionary object containing the parsed MOM_input.yaml file.

    Returns
    -------
    file_params: dict
        A dictionary of varname: file names pairs, where varname is the parameter name and file names are the input file names.
    """

    files = {}

    for module in MOM_input_yaml:
        for varname in MOM_input_yaml[module]:
            value_block = MOM_input_yaml[module][varname]["value"]
            values = _retrieve_input_filenames(varname, extract_values(value_block))
            if values:
                files[varname] = values

    return files


def get_input_data_list_files(input_data_list_yaml, MOM_input_files):
    """
    This function reads the input_data_list.yaml file and extracts all input file names that it can detect.
    To do so, it looks for all values in the input_data_list.yaml file.

    Parameters
    ----------
    input_data_list_yaml : dict
        The dictionary object containing the parsed input_data_list.yaml file.
    MOM_input_files : dict
        The dictionary object containing the varname: file names pairs extracted from the MOM_input.yaml file.
        To be used to expand expandable variables in the input_data_list.yaml file.

    Returns
    -------
    files: dict
        A dictionary of varname: file names pairs, where varname is the parameter name and file names are the input file names.
    """

    files = {}

    input_data_list = input_data_list_yaml["mom.input_data_list"]

    for varname in input_data_list:
        _files = _retrieve_input_filenames(
            varname, extract_values(input_data_list[varname])
        )
        if _files:
            # Expand expandable variables in the input_data_list.yaml file
            for i, _file in enumerate(_files):
                # Find all expandable variables in the file name:
                expandable_vars = re.findall(r"\$\{.*\}|\b\$.*\b", _file)
                for expandable_var in expandable_vars:
                    if expandable_var.strip("${}") in MOM_input_files:
                        # Replace the expandable variable with the corresponding file name from MOM_input.yaml
                        _files.pop(i)
                        _files.extend(MOM_input_files[expandable_var.strip("${}")])

            files[varname] = _files

    return files


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

    # Check if all files in MOM_input.yaml are present in input_data_list.yaml
    # If not, print the missing files and raise an error
    missing_files = set(
        filename for filelist in MOM_input_files.values() for filename in filelist
    ) - set(
        filename for filelist in input_data_list_files.values() for filename in filelist
    )
    if missing_files:
        raise ValueError(
            "Below parameter value(s) in MOM_input.yaml are suspected to be input file name(s), "
            "but are not present in input_data_list.yaml. If these are indeed input files, "
            "please add them to input_data_list.yaml. If not, please update this CI test module "
            "to exclude them from the check e.g., by adding them to the EXCEPTIONS list.\n\n  "
            + "\n  ".join(missing_files)
        )

    print("All input files in MOM_input.yaml are present in input_data_list.yaml.")
