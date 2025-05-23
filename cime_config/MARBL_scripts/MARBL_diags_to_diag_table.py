#!/usr/bin/env python

""" Convert MARBL diagnostics file to diag_table_MARBL.json

MARBL diagnostics file is a file containing a list of

    DIAGNOSTIC_NAME : frequency_operator[,frequency2frequency2_operator2, ..., frequencyN_operatorN]

MOM uses this same format for defining its ecosystem-based diagnostics to allow
users to change the requested MOM and MARBL diagnostics in the same place.

usage: MARBL_diags_to_diag_table.py [-h] -i MARBL_DIAGNOSTICS_IN -t
                                    DIAG_TABLE_OUT [-l LOW_FREQUENCY_STREAM]
                                    [-m MEDIUM_FREQUENCY_STREAM]
                                    [-g HIGH_FREQUENCY_STREAM]
                                    [--lMARBL_output_all LMARBL_OUTPUT_ALL]
                                    [--lMARBL_output_alt_co2 LMARBL_OUTPUT_ALT_CO2]

Generate MOM diag table from MARBL diagnostics

optional arguments:
  -h, --help            show this help message and exit
  -i MARBL_DIAGNOSTICS_IN, --marbl_diagnostics_in MARBL_DIAGNOSTICS_IN
                        File generated by MARBL_generate_diagnostics_file
                        (default: None)
  -t DIAG_TABLE_OUT, --diag_table_out DIAG_TABLE_OUT
                        Location of diag table (JSON) file to create (default:
                        None)
  -l LOW_FREQUENCY_STREAM, --low_frequency_stream LOW_FREQUENCY_STREAM
                        Stream to put low frequency output into (required if
                        not lMARBL_output_all) (default: 0)
  -m MEDIUM_FREQUENCY_STREAM, --medium_frequency_stream MEDIUM_FREQUENCY_STREAM
                        Stream to put medium frequency output into (required
                        if not lMARBL_output_all) (default: 0)
  -g HIGH_FREQUENCY_STREAM, --high_frequency_stream HIGH_FREQUENCY_STREAM
                        Stream to put high frequency output into (required if
                        not lMARBL_output_all) (default: 0)
  --lMARBL_output_all LMARBL_OUTPUT_ALL
                        Put all MARBL diagnostics in h.native_bgc stream (default:
                        False)
  --lMARBL_output_alt_co2 LMARBL_OUTPUT_ALT_CO2
                        Include ALT_CO2 diagnostics in streams (default:
                        False)
"""

#######################################


class DiagTableClass(object):
    """
    Class that is used to generate JSON file to extend diag_table from MARBL_diagnostics file
    """

    def __init__(self, vert_grid):
        """
        Constructor: creates a dictionary object to eventually dump to JSON
        """
        self._diag_table_dict = dict()
        # TODO: need a cleaner way to implement this; basically it's a flag that changes the monthly bgc
        #       history file to nstep output (also requires a change in MOM_MARBL_diags to drop dust / iron
        #       fluxes and RIV_FLUX diags... for some reason they can't be written at first time step?
        #       One possible solution: OCN_BGC_DIAG_MODE in env_run?
        self._nstep_output = False

        # "medium" frequency should be treated like "mom6.h.native" stream -- annual in spinup runs, monthly otherwise
        # i. 2D vars
        new_file_freq_units = "days" if self._nstep_output else None
        suffix_dict = {
            '$OCN_DIAG_MODE == "spinup"': "h.bgc.native_annual%4yr",
            "$TEST == True": "h.bgc.native%4yr-%2mo-%2dy",
            "else": "h.bgc.native%4yr-%2mo",
        }
        output_freq_units_dict = {
            '$OCN_DIAG_MODE == "spinup"': "years",
            "$TEST == True": "days",
            f"{self._nstep_output} == True": "hours",
            "else": "months",
        }
        self._diag_table_dict["medium"] = self._dict_template(
            suffix_dict, output_freq_units_dict, new_file_freq_units=new_file_freq_units
        )
        # ii. 3D vars on interpolated grid
        if vert_grid in ["interpolated", "both"]:
            suffix_dict = {
                '$OCN_DIAG_MODE == "spinup"': "h.bgc.z_annual%4yr",
                "$TEST == True": "h.bgc.z%4yr-%2mo-%2dy",
                f"{self._nstep_output} == True": "h.bgc.z_nstep%4yr-%2mo-%2dy",
                "else": "h.bgc.z%4yr-%2mo",
            }
            self._diag_table_dict["medium_z"] = self._dict_template(
                suffix_dict,
                output_freq_units_dict,
                new_file_freq_units=new_file_freq_units,
                module="ocean_model_z",
            )
        # iii. 3D vars on native grid
        if vert_grid in ["native", "both"]:
            suffix_dict = {
                '$OCN_DIAG_MODE == "spinup"': "h.bgc.native_annual%4yr",
                "$TEST == True": "h.bgc.native%4yr-%2mo",
                f"{self._nstep_output} == True": "h.bgc.native_nstep%4yr-%2mo-%2dy",
                "else": "h.bgc.native%4yr-%2mo",
            }
            self._diag_table_dict["medium_native_z"] = self._dict_template(
                suffix_dict,
                output_freq_units_dict,
                new_file_freq_units=new_file_freq_units,
                module="ocean_model",
            )

        # "high" frequency should be treated like "mom6.h.sfc" stream -- 5-day averages in spinup, daily otherwise
        # unlike "sfc", this stream will write one file per month instead of per year (except in spinup)
        # i. 2D vars
        suffix_dict = {
            '$OCN_DIAG_MODE == "spinup"': "h.bgc.daily5%4yr",
            "else": "h.bgc.daily%4yr-%2mo",
        }
        output_freq_dict = {'$OCN_DIAG_MODE == "spinup"': 5, "else": 1}
        new_file_freq_units_dict = {
            '$OCN_DIAG_MODE == "spinup"': "years",
            "else": "months",
        }
        self._diag_table_dict["high"] = self._dict_template(
            suffix_dict, "days", new_file_freq_units_dict, output_freq_dict
        )
        # ii. 3D vars on interpolated grid
        if vert_grid in ["interpolated", "both"]:
            suffix_dict = {
                '$OCN_DIAG_MODE == "spinup"': "h.bgc.z_daily5%4yr",
                "else": "h.bgc.z_daily%4yr-%2mo",
            }
            self._diag_table_dict["high_z"] = self._dict_template(
                suffix_dict,
                "days",
                new_file_freq_units_dict,
                output_freq_dict,
                module="ocean_model_z",
            )
        # iii. 3D vars on native grid
        if vert_grid in ["native", "both"]:
            suffix_dict = {
                '$OCN_DIAG_MODE == "spinup"': "h.bgc.native_daily5%4yr",
                "else": "h.bgc.native_daily5%4yr-%2mo",
            }
            self._diag_table_dict["high_native_z"] = self._dict_template(
                suffix_dict,
                "days",
                new_file_freq_units_dict,
                output_freq_dict,
                module="ocean_model",
            )

        # "low" frequency should be treated as annual averages
        # i. 2D vars
        suffix_dict = {
            '$OCN_DIAG_MODE == "spinup"': "h.bgc.native_annual2%4yr",
            "else": "h.bgc.native_annual%4yr",
        }
        self._diag_table_dict["low"] = self._dict_template(suffix_dict, "years")
        # ii. 3D vars on interpolated grid
        if vert_grid in ["interpolated", "both"]:
            suffix_dict = {
                '$OCN_DIAG_MODE == "spinup"': "h.bgc.z_annual2%4yr",
                "else": "h.bgc.z_annual%4yr",
            }
            self._diag_table_dict["low_z"] = self._dict_template(
                suffix_dict, "years", module="ocean_model_z"
            )
        # iii. 3D vars on native grid
        if vert_grid in ["native", "both"]:
            suffix_dict = {
                '$OCN_DIAG_MODE == "spinup"': "h.bgc.native_annual2%4yr",
                "else": "h.bgc.native_annual%4yr",
            }
            self._diag_table_dict["low_native_z"] = self._dict_template(
                suffix_dict, "years", module="ocean_model"
            )

    def update(self, varname, frequency, is2D, lMARBL_output_all, vert_grid):
        if lMARBL_output_all:
            use_freq = ["medium"]
        else:
            use_freq = []
            for freq in frequency:
                use_freq.append(freq)

        # iv. Update dictionary
        for freq in use_freq:
            if freq == "never":
                continue
            # append _z to frequency for 3D vars
            if is2D:
                self._diag_table_dict[f"{freq}"]["fields"]['$OCN_DIAG_MODE != "none"'][
                    "lists"
                ][0].append(varname)
            else:
                if vert_grid in ["interpolated", "both"]:
                    self._diag_table_dict[f"{freq}_z"]["fields"][
                        '$OCN_DIAG_MODE != "none"'
                    ]["lists"][0].append(varname)
                if vert_grid in ["native", "both"]:
                    self._diag_table_dict[f"{freq}_native_z"]["fields"][
                        '$OCN_DIAG_MODE != "none"'
                    ]["lists"][0].append(varname)

    def combine_medium_native_z(self):
        """
        If both medium and medium_native_z streams are requested,
        combine into single stream (with _z to get volcello and h)
        """
        if not (
            "medium" in self._diag_table_dict
            and "medium_native_z" in self._diag_table_dict
        ):
            return

        # Make list of all fields in "medium" (and remove "medium" from _diag_table_dict)
        new_fields = []
        for field_list in self._diag_table_dict.pop("medium")["fields"][
            '$OCN_DIAG_MODE != "none"'
        ]["lists"]:
            new_fields = new_fields + field_list

        # Make list of all fields in "medium_native_z"
        existing_fields = []
        for field_list in self._diag_table_dict["medium_native_z"]["fields"][
            '$OCN_DIAG_MODE != "none"'
        ]["lists"]:
            existing_fields = existing_fields + field_list

        new_field_list = list(set(new_fields) - set(existing_fields))
        if new_fields:
            self._diag_table_dict["medium_native_z"]["fields"][
                '$OCN_DIAG_MODE != "none"'
            ]["lists"].append(new_field_list)

    def dump_to_json(self, filename):
        import json

        out_dict = dict()
        out_dict["Files"] = dict()
        for freq in self._diag_table_dict:
            if (
                len(
                    self._diag_table_dict[freq]["fields"]['$OCN_DIAG_MODE != "none"'][
                        "lists"
                    ][0]
                )
                > 0
            ):
                out_dict["Files"][freq] = self._diag_table_dict[freq].copy()
                out_dict["Files"][freq]["fields"]['$OCN_DIAG_MODE != "none"'][
                    "lists"
                ].append(["geolat", "geolon"])
                if (
                    out_dict["Files"][freq]["fields"]['$OCN_DIAG_MODE != "none"'][
                        "module"
                    ]
                    == "ocean_model"
                    and freq[-2:] == "_z"
                ) or out_dict["Files"][freq]["fields"]['$OCN_DIAG_MODE != "none"'][
                    "module"
                ] == "ocean_model_z":
                    out_dict["Files"][freq]["fields"]['$OCN_DIAG_MODE != "none"'][
                        "lists"
                    ].append(["volcello", "h"])
        if out_dict["Files"]:
            with open(filename, "w") as fp:
                json.dump(
                    out_dict, fp, separators=(",", ": "), sort_keys=False, indent=3
                )
        else:
            print("WARNING: no JSON file written as no variables were requested")

    def _dict_template(
        self,
        suffix,
        output_freq_units,
        new_file_freq_units=None,
        output_freq=1,
        new_file_freq=1,
        module="ocean_model",
    ):
        """
        Return the basic template for MOM6 diag_table dictionary.
        Variables will be added to output file by appending to template["fields"]['$OCN_DIAG_MODE != "none"']["lists"][0]

        Parameters:
            * suffix: string used to identify output file; could also be a dictionary
                      where keys are logical evaluations
            * output_freq_units: units used to determine how often to output; similar
                                 to suffix, this can also be a dictionary
            * new_file_freq_units: units used to determine how often to generate new stream
                                   files; if None, will use output_freq_units (default: None)
            * output_freq: how frequently to output (default: 1)
            * new_file_freq: how frequently to create new files (default: 1)
            * module: string that determines vertical grid; "ocean_model_z" maps to Z space, "ocean_model" stays on native grid, "ocean_model_rho2" is sigma2
        """
        template = dict()
        template["suffix"] = suffix
        template["output_freq"] = output_freq
        template["new_file_freq"] = new_file_freq
        template["output_freq_units"] = output_freq_units
        if new_file_freq_units:
            template["new_file_freq_units"] = new_file_freq_units
        else:
            template["new_file_freq_units"] = output_freq_units
        template["time_axis_units"] = "days"
        template["reduction_method"] = "mean"
        template["regional_section"] = "none"
        template["fields"] = {
            '$OCN_DIAG_MODE != "none"': {
                "module": module,
                "packing": "= 1 if $TEST or $MARBL_DIAG_MODE == 'test_suite' else 2",
                "lists": [[]],
            }
        }
        return template


#######################################


def _parse_args():
    """Parse command line arguments"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MOM diag table from MARBL diagnostics",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Command line argument to point to MARBL diagnostics input file (required!)
    parser.add_argument(
        "-i",
        "--marbl_diagnostics_in",
        action="store",
        dest="MARBL_diagnostics_in",
        required=True,
        help="File generated by MARBL_generate_diagnostics_file",
    )

    # Command line argument to point to diag table output file (required!)
    parser.add_argument(
        "-t",
        "--diag_table_out",
        action="store",
        dest="diag_table_out",
        required=True,
        help="Location of diag table (JSON) file to create",
    )

    # Command line arguments for the different streams to use (low, medium, high)
    parser.add_argument(
        "-l",
        "--low_frequency_stream",
        action="store",
        dest="low_frequency_stream",
        type=int,
        default=0,
        help="Stream to put low frequency output into (required if not lMARBL_output_all)",
    )

    parser.add_argument(
        "-m",
        "--medium_frequency_stream",
        action="store",
        dest="medium_frequency_stream",
        type=int,
        default=0,
        help="Stream to put medium frequency output into (required if not lMARBL_output_all)",
    )

    parser.add_argument(
        "-g",
        "--high_frequency_stream",
        action="store",
        dest="high_frequency_stream",
        type=int,
        default=0,
        help="Stream to put high frequency output into (required if not lMARBL_output_all)",
    )

    parser.add_argument(
        "-v",
        "--vert_grid",
        action="store",
        dest="vert_grid",
        default="native",
        choices=["native", "interpolated", "both"],
        help="BGC history output grid",
    )

    # Should all MARBL diagnostics be included in the h.native_bgc stream?
    parser.add_argument(
        "--lMARBL_output_all",
        action="store",
        dest="lMARBL_output_all",
        type=bool,
        default=False,
        help="Put all MARBL diagnostics in h.native_bgc stream",
    )

    # Should MARBL's ALT_CO2 diagnostics be included in the diag table?
    parser.add_argument(
        "--lMARBL_output_alt_co2",
        action="store",
        dest="lMARBL_output_alt_co2",
        type=bool,
        default=False,
        help="Include ALT_CO2 diagnostics in streams",
    )

    return parser.parse_args()


#######################################


def _parse_line(line_in):
    """Take a line of input from the MARBL diagnostic output and return the variable
    name, frequency, and operator. Lines that are commented out or empty should
    return None for all three; non-empty lines that are not in the proper format
    should trigger errors.

    If they are not None, frequency and operator are always returned as lists
    (although they often have just one element).
    """
    import logging
    import sys

    line_loc = line_in.split("#")[0].strip()
    # Return None, None if line is empty
    if len(line_loc) == 0:
        return None, None, None

    logger = logging.getLogger("__name__")
    line_split = line_loc.split(":")
    if len(line_split) != 2:
        logger.error(
            "Can not determine variable name from following line: '%s'" % line_in
        )
        sys.exit(1)

    freq = []
    op = []
    for freq_op in line_split[1].split(","):
        freq_op_split = freq_op.strip().split("_")
        if len(freq_op_split) != 2:
            logger.error(
                "Can not determine frequency and operator from following entry: '%s'"
                % line_split[1]
            )
            sys.exit(1)
        freq.append(freq_op_split[0])
        op.append(freq_op_split[1])

    return line_split[0].strip(), freq, op


#######################################


def diagnostics_to_diag_table(
    MARBL_diagnostics_in,
    diag_table_out,
    diag2D_list,
    vert_grid,
    lMARBL_output_all,
    lMARBL_output_alt_co2,
):
    """
    Build a diag_table dictionary to dump to JSON format
    """

    import os, sys, logging

    logger = logging.getLogger("__name__")
    labort = False
    processed_vars = dict()

    # 1. Check arguments:
    #    MARBL_diagnostics_in can not be None and must be path of an existing file
    if MARBL_diagnostics_in == None:
        logger.error("Must specific MARBL_diagnostics_in")
        labort = True
    elif not os.path.isfile(MARBL_diagnostics_in):
        logger.error("File not found %s" % MARBL_diagnostics_in)
        labort = True
    if labort:
        sys.exit(1)

    # 2. Set up diag_table object
    diag_table = DiagTableClass(vert_grid)

    # 3. Read MARBL_diagnostics_in line by line, convert each line to diag table entry
    with open(MARBL_diagnostics_in, "r") as file_in:
        all_lines = file_in.readlines()

    for line in all_lines:
        varname, frequency, operator = _parse_line(line.strip())
        # i. Continue to next line in the following circumstances
        #    * varname = None
        if varname == None:
            continue
        #    * Skip ALT_CO2 vars unless explicitly requested
        if (not lMARBL_output_alt_co2) and ("ALT_CO2" in varname):
            continue

        # ii. Abort if varname has already appeared in file at given frequency
        for freq in frequency:
            if freq not in processed_vars:
                processed_vars[freq] = []
            if varname in processed_vars[freq]:
                logger.error(
                    f"{varname} appears in {MARBL_diagnostics_in} with frequency %{freq} multiple times"
                )
                sys.exit(1)
            processed_vars[freq].append(varname)

        # iii. Update diag table
        is2D = varname in diag2D_list
        diag_table.update(varname, frequency, is2D, lMARBL_output_all, vert_grid)

    # 4. Combine "medium" and "medium_native_z"
    diag_table.combine_medium_native_z()

    # File footer
    diag_table.dump_to_json(diag_table_out)


#######################################

if __name__ == "__main__":
    # Parse command line arguments
    import logging

    args = _parse_args()

    logging.basicConfig(
        format="%(levelname)s (%(funcName)s): %(message)s", level=logging.DEBUG
    )

    # call diagnostics_to_diag_table()
    diagnostics_to_diag_table(
        args.MARBL_diagnostics_in,
        args.diag_table_out,
        args.diag2D_list,
        args.vert_grid,
        args.lMARBL_output_all,
        args.lMARBL_output_alt_co2,
    )
