#!/usr/bin/env python

"""
Unit test for cime_config/buildnml and MOM parameter expansion.
Verifies MASKTABLE expansion under single-instance and multi-instance modes with AUTO_MASKTABLE True/False.
"""

import os
import sys

# Add cime_config/MOM_RPS to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "cime_config", "MOM_RPS"))
from FType_MOM_params import FType_MOM_params


def get_param_val(mom_params, varname):
    for module in mom_params._data:
        if varname in mom_params._data[module]:
            return mom_params._data[module][varname]["value"]
    return None


def test_masktable_expansion():
    json_path = os.path.join(
        os.path.dirname(__file__), "..", "param_templates", "json", "MOM_input.json"
    )

    # Provide default CIME environment mock values (booleans, floats, strings) to satisfy
    # CIME.ParamGen formulas/guards across all MOM_input.json parameters and prevent
    # Python eval() type errors (e.g., float / str or bool vs str comparisons).
    default_env = {
        "OCN_GRID": "tx2_3v2",
        "TEST": False,
        "NTASKS_OCN": 64,
        "DIN_LOC_ROOT": "/tmp/inputdata",
        "CASEROOT": "/tmp/caseroot",
        "CASEBUILD": "/tmp/casebuild",
        "CASE": "case",
        "SRCROOT": "/tmp/srcroot",
        "RUNDIR": "/tmp/rundir",
        "COMP_ROOT_DIR_OCN": "/tmp/mom",
        "RUN_TYPE": "startup",
        "CONTINUE_RUN": False,
        "GET_REFCASE": False,
        "RUN_REFCASE": "refcase",
        "RUN_REFDATE": "0001-01-01",
        "RUN_REFTOD": "00000",
        "CPL_I2O_PER_CAT": False,
        "ICE_NCAT": 5,
        "MARBL_DIAG_MODE": "none",
        "MOM6_INFRA_API": "FMS2",
        "MOM6_VERTICAL_GRID": "zstar_65L",
        "COMP_ATM": "cam",
        "COMP_ICE": "cice",
        "COMP_WAVE": "ww3",
        "RESTINT": 1.0,
        "REST_OPTION": "nmonths",
        "REST_N": 1,
        "REST_FREQ": "monthly",
        "STOP_OPTION": "nmonths",
        "STOP_N": 1,
        "STOP_FREQ": "monthly",
        "ATM_CO2_OPT": "constant",
        "ATM_ALT_CO2_OPT": "constant",
        "ATM_CO2_CONST": 280.0,
        "ATM_ALT_CO2_CONST": 280.0,
        "USE_MARBL_TRACERS": False,
        "NCPL_BASE_PERIOD": "day",
        "OCN_NCPL": 24,
        "DT": 3600.0,
    }

    def run_reduction(auto_masktable, inst_suffix):
        mom_params = FType_MOM_params.from_json(json_path)
        dyn_env = {
            "AUTO_MASKTABLE": auto_masktable,
            "INST_SUFFIX": inst_suffix,
        }
        mom_params.reduce(lambda var: dyn_env.get(var, default_env.get(var, "")))
        return get_param_val(mom_params, "MASKTABLE")

    # 1. Test Single-Instance, AUTO_MASKTABLE=True
    val1 = run_reduction(auto_masktable=True, inst_suffix="")
    print(f"Single-instance AUTO_MASKTABLE=True MASKTABLE: {val1}")
    assert (
        val1 == "MOM_auto_mask_table"
    ), f"Expected 'MOM_auto_mask_table', got '{val1}'"

    # 2. Test Multi-Instance, AUTO_MASKTABLE=True (_0001)
    val2 = run_reduction(auto_masktable=True, inst_suffix="_0001")
    print(f"Multi-instance _0001 AUTO_MASKTABLE=True MASKTABLE: {val2}")
    assert (
        val2 == "MOM_auto_mask_table_0001"
    ), f"Expected 'MOM_auto_mask_table_0001', got '{val2}'"

    # 3. Test Single-Instance, AUTO_MASKTABLE=False
    val3 = run_reduction(auto_masktable=False, inst_suffix="")
    print(f"Single-instance AUTO_MASKTABLE=False MASKTABLE: {val3}")
    assert val3 == "MOM_mask_table", f"Expected 'MOM_mask_table', got '{val3}'"

    # 4. Test Multi-Instance, AUTO_MASKTABLE=False (_0001)
    val4 = run_reduction(auto_masktable=False, inst_suffix="_0001")
    print(f"Multi-instance _0001 AUTO_MASKTABLE=False MASKTABLE: {val4}")
    assert val4 == "MOM_mask_table", f"Expected 'MOM_mask_table', got '{val4}'"

    print("ALL MASKTABLE TESTS PASSED")


if __name__ == "__main__":
    test_masktable_expansion()
