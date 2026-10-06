"""Readers for the MOM6 parameter files of a case.

This module does not depend on CIME, so that it can be tested on its own.
"""

import re
from collections import OrderedDict


def read_MOM_params(input_path):
    """Reads in a parameter file in MOM_input syntax, e.g., MOM_input or MOM_override."""

    _data = OrderedDict()
    with open(input_path, "r") as param_file:
        within_comment_block = False
        curr_module = "Global"
        for line in param_file:
            # a comment starts at the first !, // or /*, and a comment block
            # (/* ... */) may only be opened on a line that has nothing but a
            # comment on it (as per MOM6 behavior)
            if within_comment_block:
                within_comment_block = "*/" not in line
                continue
            line_s = re.split(r"!|//|/\*", line, maxsplit=1)[0].split()
            if not line_s:
                opening = line.find("/*")
                within_comment_block = opening >= 0 and "*/" not in line[opening + 2 :]
                continue
            line = " ".join(line_s)

            # check format:
            if line[0] == "%":  # closes a parameter block, by name or not
                if curr_module == "Global":
                    raise SystemExit(
                        f"ERROR: {line} in {input_path} closes a parameter block "
                        "that is not open."
                    )
                if line[1:].strip() not in ("", curr_module):
                    raise SystemExit(
                        f"ERROR: {line} in {input_path} does not close the open "
                        f"parameter block, {curr_module}%."
                    )
                curr_module = "Global"
            elif line[-1] == "%":  # opens a parameter block
                if curr_module != "Global":
                    raise SystemExit(
                        f"ERROR: {line} in {input_path} opens a parameter block "
                        f"within {curr_module}%, but nested blocks are not supported."
                    )
                curr_module = line[:-1].strip()
                if not re.fullmatch(r"\w+", curr_module):
                    raise SystemExit(
                        f"ERROR: {line} in {input_path} does not open a parameter "
                        "block: block names may contain letters, digits and "
                        "underscores only."
                    )
            else:
                # discard override keyword if provided:
                if line_s[0] == "#override" and len(line_s) > 1:
                    line_s = line_s[1:]
                line_j = " ".join(line_s)

                # now parse the line:
                if re.search(r"^(\w+%)*\w+\s*=\s*\S", line_j):
                    eq_ix = line_j.index("=")
                    varname = line_j[:eq_ix].strip()
                    val_str = line_j[eq_ix + 1 :].strip()

                    # a parameter may be prefixed by its block, e.g., KPP%N_SMOOTH,
                    # in which case that is its block, whether a block is open or not.
                    module = curr_module
                    if "%" in varname:
                        module, _, varname = varname.rpartition("%")
                        if "%" in module:
                            raise SystemExit(
                                f"ERROR: {line} in {input_path} sets a parameter "
                                f"within the nested block {module}%, but nested "
                                "blocks are not supported."
                            )

                    # add this module if not added before:
                    if not module in _data:
                        _data[module] = dict()

                    # check if param already provided:
                    if varname in _data[module]:
                        raise SystemExit(
                            "ERROR: "
                            + varname
                            + " listed more than once in "
                            + str(input_path)
                        )

                    # enter the parameter in the dictionary:
                    _data[module][varname] = {"value": val_str}
                else:
                    raise SystemExit(
                        "ERROR: Cannot parse the following line in "
                        + str(input_path)
                        + ": "
                        + line
                    )

        # Check if there is unclosed block:
        if within_comment_block:
            raise SystemExit(
                f"ERROR: A comment block (/* ... */) is not closed in {input_path}."
            )
        if curr_module != "Global":
            raise SystemExit(
                f"ERROR: The parameter block {curr_module}% is not closed in "
                f"{input_path}."
            )

    return _data
