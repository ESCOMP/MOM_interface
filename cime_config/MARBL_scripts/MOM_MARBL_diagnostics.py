""" Scripts to generate MOM-specific diagnostic list in generic MARBL format
    (e.g. MARBL tracer state)
"""


def write_MARBL_diagnostics_file(
    active_tracers,
    autotroph_list,
    zooplankton_list,
    calcifier_list,
    ladjust_bury_coeff,
    MARBL_diag_filename,
    ice_ncat,
    diag_mode,
):
    """Subroutine to write a file in the same format as marbl_diagnostics containing
    a list of MOM-generated diagnostics that should be included based on the
    MARBL configuration
    """

    # each subsequent diag_mode is a superset of the previous mode; if we have a list of valid modes
    # then we can use integer comparison with the .index() function to determine if a variable should
    # be included.
    valid_diag_modes = ["none", "minimal", "full", "test_suite"]
    # For now we hard-code the tracers we want included in the output when diag_mode = 'minimal'
    # (and for the Jint_100m diagnostics)
    # If we expand the minimal set, we may need to change how we track what is included
    tracers_in_minimal_diag_output = [
        "Fe",
        "DIC",
        "ALK",
        "PO4",
        "NO3",
        "NH4",
        "SiO3",
        "O2",
        "DOC",
        "DOCr",
        "coccoC",
        "diatC",
        "diazC",
        "mesozooC",
        "microzooC",
        "spC",
        "coccoCaCO3",
        "spChl",
        "diatChl",
        "diazChl",
        "coccoChl",
        "microzooC",
        "mesozooC",
    ]
    Jint_100m_in_minimal_diag_output = ["ALK", "DIC"]

    with open(MARBL_diag_filename, "w") as fout:
        # File header with information on how to use generated file
        fout.write(
            "# This file contains a list of all ecosystem-related diagnostics MOM output for a given MARBL configuration,\n"
        )
        fout.write(
            "# as well as the recommended frequency and operator for outputting each diagnostic.\n"
        )
        fout.write(
            "# Some diagnostics are computed in MOM, while others are provided by MARBL.\n"
        )
        fout.write("# The format of this file is:\n")
        fout.write("#\n")
        fout.write("# DIAGNOSTIC_NAME : frequency_operator\n")
        fout.write("#\n")
        fout.write(
            "# And fields that should be output at multiple different frequencies will be comma-separated:\n"
        )
        fout.write("#\n")
        fout.write(
            "# DIAGNOSTIC_NAME : frequency1_operator1, frequency2_operator2, ..., frequencyN_operatorN\n"
        )
        fout.write("#\n")
        fout.write("# Frequencies are never, low, medium, and high.\n")
        fout.write("# Operators are instantaneous, average, minimum, and maximum.\n")
        fout.write("#\n")
        fout.write(
            "# To change BGC-related diagnostic output, copy this file to SourceMods/src.mom/\n"
        )
        fout.write("# and edit as desired.\n")

        # File will contain MOM and MARBL diagnostics, so we provide header to make
        # the provenance of each diagnostic clear
        fout.write("#\n########################################\n")
        fout.write("#       MOM-generated diagnostics      #\n")
        fout.write("########################################\n")

        if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("minimal"):
            freq_op = "medium_average"
        else:
            freq_op = "never_average"
        fout.write("#\n# Dust and Carbon Fluxes from the Coupler\n#\n")
        fout.write(f"ATM_FINE_DUST_FLUX_CPL : {freq_op}\n")
        fout.write(f"ATM_COARSE_DUST_FLUX_CPL : {freq_op}\n")
        fout.write(f"SEAICE_DUST_FLUX_CPL : {freq_op}\n")
        fout.write(f"ATM_BLACK_CARBON_FLUX_CPL : {freq_op}\n")
        fout.write(f"SEAICE_BLACK_CARBON_FLUX_CPL : {freq_op}\n")
        fout.write("#\n# temperature and salinity\n#\n")
        fout.write(
            f"so: {freq_op}\n"
        )  # so should be included when diag_mode = "minimal"

        if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("full"):
            freq_op = "medium_average"
        else:
            freq_op = "never_average"
        fout.write(
            f"thetao: {freq_op}\n"
        )  # thetao should not be included when diag_mode = "minimal"
        fout.write("#\n# Bottom Flux to Tendency Conversion\n#\n")
        fout.write(f"BOT_FLUX_TO_TEND : {freq_op}\n")

        if ice_ncat > 0:
            fout.write("#\n# per-category forcings\n#\n")
            for m in range(ice_ncat + 1):
                fout.write(f"FRACR_CAT_{m+1}: {freq_op}\n")
                fout.write(f"QSW_CAT_{m+1}: {freq_op}\n")

        # TODO: add running means, and then define these diagnostics
        # If adjusting bury coefficients, add running means to requested diagnostics
        if ladjust_bury_coeff:
            fout.write("#\n# Running means computed for MARBL\n#\n")
            fout.write(f"MARBL_rmean_glo_scalar_POC_bury_coeff : {freq_op}\n")
            fout.write(f"MARBL_rmean_glo_scalar_POP_bury_coeff : {freq_op}\n")
            fout.write(f"MARBL_rmean_glo_scalar_bSi_bury_coeff : {freq_op}\n")

        # 1. Create dictionary with default tracer output for all tracers
        #    - This dictionary also stores some tracer properties (currently just for budget-specific diagnostics)
        full_diag_dict = {}
        Jint_100m_freq_op = {}
        for tracer_short_name in sorted(active_tracers):
            per_tracer_dict = dict()

            # Properties used to determine frequency of budget terms
            per_tracer_dict["properties"] = dict()
            per_tracer_dict["properties"]["include budget terms"] = False
            per_tracer_dict["properties"]["has surface flux"] = False

            # Default frequencies for per-tracer diagnostics
            # - tracer state should be output monthly
            # - everything else is off by default
            # TODO: add vertical integral for tend_zint_100m_{tracer}
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index(
                "test_suite"
            ):
                freq_op = "medium_average"
            else:
                freq_op = "never_average"
            per_tracer_dict["diags"] = {}
            # Tracers themselves and Jint_100m diags  have different defaults than the rest
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("full") or (
                valid_diag_modes.index(diag_mode) == valid_diag_modes.index("minimal")
                and tracer_short_name in tracers_in_minimal_diag_output
            ):
                per_tracer_dict["diags"][tracer_short_name] = "medium_average"
            else:
                per_tracer_dict["diags"][tracer_short_name] = "never_average"
            per_tracer_dict["diags"][
                "Jint_100m_%s" % tracer_short_name
            ] = "never_average"
            per_tracer_dict["diags"]["STF_%s" % tracer_short_name] = freq_op
            per_tracer_dict["diags"]["J_%s" % tracer_short_name] = freq_op
            per_tracer_dict["diags"]["Jint_%s" % tracer_short_name] = freq_op
            per_tracer_dict["diags"]["%s_zint_100m" % tracer_short_name] = freq_op
            # per_tracer_dict['diags']['tend_zint_100m_%s' % tracer_short_name] = 'never_average'

            # Some diagnostics are not defined for all tracers; diagnostics with 'none'
            # are not added to diagnostics file and will not show up in tavg_contents
            per_tracer_dict["diags"]["%s_RIV_FLUX" % tracer_short_name] = "none"
            full_diag_dict[tracer_short_name] = dict(per_tracer_dict)

            # Set up dictionary for tracking the Jint_100m_{tracer} freq_ops
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("full") or (
                valid_diag_modes.index(diag_mode) == valid_diag_modes.index("minimal")
                and tracer_short_name in Jint_100m_in_minimal_diag_output
            ):
                Jint_100m_freq_op[tracer_short_name] = "medium_average"
            else:
                Jint_100m_freq_op[tracer_short_name] = "never_average"

        # TODO: turn on some of these diagnostics once they are properly defined
        # 2. Update dictionary for tracers that don't just rely on default diagnostic output
        #    This is organized per-tracer, and specific blocks are ignored if MARBL is not
        #    configured to run with that particular tracer
        # PO4
        if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("full"):
            freq_op = "medium_average"
            low_freq_op = "low_average"
            high_freq_op = "high_average"
        else:
            freq_op = "never_average"
            low_freq_op = "never_average"
            high_freq_op = "never_average"
        if "PO4" in full_diag_dict.keys():
            full_diag_dict["PO4"]["diags"]["PO4_RIV_FLUX"] = freq_op
            full_diag_dict["PO4"]["diags"]["J_PO4"] = low_freq_op
            full_diag_dict["PO4"]["diags"]["Jint_100m_PO4"] = Jint_100m_freq_op["PO4"]
            # full_diag_dict['PO4']['diags']['tend_zint_100m_PO4'] = freq_op
            full_diag_dict["PO4"]["properties"]["has surface flux"] = True
        # NO3
        if "NO3" in full_diag_dict.keys():
            full_diag_dict["NO3"]["diags"]["NO3_RIV_FLUX"] = freq_op
            full_diag_dict["NO3"]["diags"]["J_NO3"] = low_freq_op
            full_diag_dict["NO3"]["diags"]["Jint_100m_NO3"] = Jint_100m_freq_op["NO3"]
            # full_diag_dict['NO3']['diags']['tend_zint_100m_NO3'] = freq_op
            full_diag_dict["NO3"]["properties"]["has surface flux"] = True
        # SiO3
        if "SiO3" in full_diag_dict.keys():
            full_diag_dict["SiO3"]["diags"]["SiO3_RIV_FLUX"] = freq_op
            full_diag_dict["SiO3"]["diags"]["J_SiO3"] = low_freq_op
            full_diag_dict["SiO3"]["diags"]["Jint_100m_SiO3"] = Jint_100m_freq_op[
                "SiO3"
            ]
            # full_diag_dict['SiO3']['diags']['tend_zint_100m_SiO3'] = freq_op
            full_diag_dict["SiO3"]["properties"]["has surface flux"] = True
        # NH4
        if "NH4" in full_diag_dict.keys():
            full_diag_dict["NH4"]["diags"]["J_NH4"] = low_freq_op
            full_diag_dict["NH4"]["diags"]["Jint_100m_NH4"] = Jint_100m_freq_op["NH4"]
            # full_diag_dict['NH4']['diags']['tend_zint_100m_NH4'] = freq_op
            full_diag_dict["NH4"]["properties"]["has surface flux"] = True
        # Fe
        if "Fe" in full_diag_dict.keys():
            full_diag_dict["Fe"]["diags"]["Fe_RIV_FLUX"] = freq_op
            full_diag_dict["Fe"]["diags"]["J_Fe"] = low_freq_op
            full_diag_dict["Fe"]["diags"]["Jint_100m_Fe"] = Jint_100m_freq_op["Fe"]
            # full_diag_dict['Fe']['diags']['tend_zint_100m_Fe'] = freq_op
            full_diag_dict["Fe"]["properties"]["include budget terms"] = True
            full_diag_dict["Fe"]["properties"]["has surface flux"] = True
        # Lig
        if "Lig" in full_diag_dict.keys():
            pass  # Lig just uses default settings
        # O2
        if "O2" in full_diag_dict.keys():
            # STF_O2 is special case
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("full"):
                full_diag_dict["O2"]["diags"]["STF_O2"] = "medium_average, high_average"
            else:
                full_diag_dict["O2"]["diags"]["STF_O2"] = "never_average"
            full_diag_dict["O2"]["diags"]["Jint_100m_O2"] = Jint_100m_freq_op["O2"]
            # full_diag_dict['O2']['diags']['tend_zint_100m_O2'] = freq_op
            full_diag_dict["O2"]["properties"]["include budget terms"] = True
            full_diag_dict["O2"]["properties"]["has surface flux"] = True
        # DIC
        if "DIC" in full_diag_dict.keys():
            # STF_SALT_DIC is special case
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("minimal"):
                full_diag_dict["DIC"]["diags"]["STF_SALT_DIC"] = "medium_average"
            full_diag_dict["DIC"]["diags"]["DIC_RIV_FLUX"] = freq_op
            full_diag_dict["DIC"]["diags"]["J_DIC"] = freq_op
            full_diag_dict["DIC"]["diags"]["Jint_100m_DIC"] = Jint_100m_freq_op["DIC"]
            # full_diag_dict['DIC']['diags']['tend_zint_100m_DIC'] = freq_op
            full_diag_dict["DIC"]["properties"]["include budget terms"] = True
            full_diag_dict["DIC"]["properties"]["has surface flux"] = True
        # DIC_ALT_CO2
        if "DIC_ALT_CO2" in full_diag_dict.keys():
            full_diag_dict["DIC_ALT_CO2"]["diags"]["DIC_ALT_CO2_RIV_FLUX"] = freq_op
            full_diag_dict["DIC_ALT_CO2"]["diags"]["J_DIC_ALT_CO2"] = freq_op
            full_diag_dict["DIC_ALT_CO2"]["diags"]["Jint_100m_DIC_ALT_CO2"] = (
                Jint_100m_freq_op["DIC_ALT_CO2"]
            )
            # full_diag_dict['DIC_ALT_CO2']['diags']['tend_zint_100m_DIC_ALT_CO2'] = freq_op
            full_diag_dict["DIC_ALT_CO2"]["properties"]["include budget terms"] = True
            full_diag_dict["DIC_ALT_CO2"]["properties"]["has surface flux"] = True
        # ALK
        if "ALK" in full_diag_dict.keys():
            # STF_SALT_ALK is special case
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("minimal"):
                full_diag_dict["ALK"]["diags"]["STF_SALT_ALK"] = "medium_average"
            full_diag_dict["ALK"]["diags"]["ALK_RIV_FLUX"] = freq_op
            full_diag_dict["ALK"]["diags"]["STF_ALK"] = freq_op
            full_diag_dict["ALK"]["diags"]["J_ALK"] = low_freq_op
            full_diag_dict["ALK"]["diags"]["Jint_100m_ALK"] = Jint_100m_freq_op["ALK"]
            # full_diag_dict['ALK']['diags']['tend_zint_100m_ALK'] = freq_op
            full_diag_dict["ALK"]["properties"]["has surface flux"] = True
        # ALK_ALT_CO2
        if "ALK_ALT_CO2" in full_diag_dict.keys():
            full_diag_dict["ALK_ALT_CO2"]["diags"]["ALK_ALT_CO2_RIV_FLUX"] = freq_op
            full_diag_dict["ALK_ALT_CO2"]["diags"]["STF_ALK_ALT_CO2"] = freq_op
            full_diag_dict["ALK_ALT_CO2"]["diags"]["J_ALK_ALT_CO2"] = low_freq_op
            full_diag_dict["ALK_ALT_CO2"]["diags"]["Jint_100m_ALK_ALT_CO2"] = (
                Jint_100m_freq_op["ALK_ALT_CO2"]
            )
            # full_diag_dict['ALK_ALT_CO2']['diags']['tend_zint_100m_ALK_ALT_CO2'] = freq_op
            full_diag_dict["ALK_ALT_CO2"]["properties"]["has surface flux"] = True
        # DOC
        if "DOC" in full_diag_dict.keys():
            full_diag_dict["DOC"]["diags"]["DOC_RIV_FLUX"] = freq_op
            full_diag_dict["DOC"]["diags"]["Jint_100m_DOC"] = Jint_100m_freq_op["DOC"]
            # full_diag_dict['DOC']['diags']['tend_zint_100m_DOC'] = freq_op
            full_diag_dict["DOC"]["properties"]["include budget terms"] = True
            full_diag_dict["DOC"]["properties"][
                "has surface flux"
            ] = False  # this should be True if EBM is off
        # DON
        if "DON" in full_diag_dict.keys():
            full_diag_dict["DON"]["diags"]["DON_RIV_FLUX"] = freq_op
            full_diag_dict["DON"]["properties"]["has surface flux"] = True
        # DOP
        if "DOP" in full_diag_dict.keys():
            full_diag_dict["DOP"]["diags"]["DOP_RIV_FLUX"] = freq_op
            full_diag_dict["DOP"]["properties"]["has surface flux"] = True
        # DOPr
        if "DOPr" in full_diag_dict.keys():
            full_diag_dict["DOPr"]["diags"]["DOPr_RIV_FLUX"] = freq_op
            full_diag_dict["DOPr"]["properties"]["has surface flux"] = True
        # DONr
        if "DONr" in full_diag_dict.keys():
            full_diag_dict["DONr"]["diags"]["DONr_RIV_FLUX"] = freq_op
            full_diag_dict["DONr"]["properties"]["has surface flux"] = True
        # DOCr
        if "DOCr" in full_diag_dict.keys():
            full_diag_dict["DOCr"]["diags"]["DOCr_RIV_FLUX"] = freq_op
            full_diag_dict["DOCr"]["diags"]["Jint_100m_DOCr"] = Jint_100m_freq_op[
                "DOCr"
            ]
            # full_diag_dict['DOCr']['diags']['tend_zint_100m_DOCr'] = freq_op
            full_diag_dict["DOCr"]["properties"]["include budget terms"] = True
            full_diag_dict["DOCr"]["properties"][
                "has surface flux"
            ] = False  # this should be True if EBM is off
        # DI13C
        if "DI13C" in full_diag_dict.keys():
            # full_diag_dict['DI13C']['diags']['DI13C_RIV_FLUX'] = freq_op
            full_diag_dict["DI13C"]["diags"]["J_DI13C"] = freq_op
            full_diag_dict["DI13C"]["diags"]["Jint_100m_DI13C"] = Jint_100m_freq_op[
                "DI13C"
            ]
            # full_diag_dict['DI13C']['diags']['tend_zint_100m_DI13C'] = freq_op
            full_diag_dict["DI13C"]["properties"]["has surface flux"] = True
        # DO13Ctot
        if "DO13Ctot" in full_diag_dict.keys():
            # full_diag_dict['DO13Ctot']['diags']['DO13Ctot_RIV_FLUX'] = freq_op
            full_diag_dict["DO13Ctot"]["diags"]["Jint_100m_DO13Ctot"] = (
                Jint_100m_freq_op["DO13Ctot"]
            )
            # full_diag_dict['DO13Ctot']['diags']['tend_zint_100m_DO13Ctot'] = freq_op
            full_diag_dict["DO13Ctot"]["properties"]["has surface flux"] = True
        # DI14C
        if "DI14C" in full_diag_dict.keys():
            # full_diag_dict['DI14C']['diags']['DI14C_RIV_FLUX'] = freq_op
            full_diag_dict["DI14C"]["diags"]["J_DI14C"] = freq_op
            full_diag_dict["DI14C"]["diags"]["Jint_100m_DI14C"] = Jint_100m_freq_op[
                "DI14C"
            ]
            # full_diag_dict['DI14C']['diags']['tend_zint_100m_DI14C'] = freq_op
            full_diag_dict["DI14C"]["properties"]["has surface flux"] = True
        # DO14Ctot
        if "DO14Ctot" in full_diag_dict.keys():
            # full_diag_dict['DO14Ctot']['diags']['DO14Ctot_RIV_FLUX'] = freq_op
            full_diag_dict["DO14Ctot"]["diags"]["Jint_100m_DO14Ctot"] = (
                Jint_100m_freq_op["DO14Ctot"]
            )
            # full_diag_dict['DO14Ctot']['diags']['tend_zint_100m_DO14Ctot'] = freq_op
            full_diag_dict["DO14Ctot"]["properties"]["has surface flux"] = True
        # ABIO_DIC
        if "ABIO_DIC" in full_diag_dict.keys():
            # STF_SALT_ABIO_DIC is special case
            if valid_diag_modes.index(diag_mode) >= valid_diag_modes.index("minimal"):
                full_diag_dict["ABIO_DIC"]["diags"][
                    "STF_SALT_ABIO_DIC"
                ] = "medium_average"
            # full_diag_dict['ABIO_DIC']['diags']['J_ABIO_DIC'] = freq_op
            full_diag_dict["ABIO_DIC"]["diags"]["STF_ABIO_DIC"] = freq_op
            # full_diag_dict['ABIO_DIC']['diags']['FvPER_ABIO_DIC'] = freq_op
            # full_diag_dict['ABIO_DIC']['diags']['FvICE_ABIO_DIC'] = freq_op
            full_diag_dict["ABIO_DIC"]["properties"]["has surface flux"] = True
        # DI14C
        if "ABIO_DI14C" in full_diag_dict.keys():
            # full_diag_dict['ABIO_DI14C']['diags']['J_ABIO_DI14C'] = freq_op
            full_diag_dict["ABIO_DI14C"]["diags"]["STF_ABIO_DI14C"] = freq_op
            full_diag_dict["ABIO_DI14C"]["diags"]["Jint_ABIO_DI14C"] = freq_op
            # full_diag_dict['ABIO_DI14C']['diags']['FvPER_ABIO_DI14C'] = freq_op
            # full_diag_dict['ABIO_DI14C']['diags']['FvICE_ABIO_DI14C'] = freq_op
            full_diag_dict["ABIO_DI14C"]["properties"]["has surface flux"] = True

        # 3. Per-autotroph diagnostics
        for autotroph_name in autotroph_list:
            tracer_short_name = autotroph_name + "C"
            if tracer_short_name in full_diag_dict.keys():
                full_diag_dict[tracer_short_name]["diags"][
                    "%s_zint_100m" % tracer_short_name
                ] = high_freq_op
            tracer_short_name = autotroph_name + "CaCO3"
            if tracer_short_name in full_diag_dict.keys():
                full_diag_dict[tracer_short_name]["diags"][
                    "%s_zint_100m" % tracer_short_name
                ] = high_freq_op
            tracer_short_name = autotroph_name + "Chl"
            if tracer_short_name in full_diag_dict.keys():
                full_diag_dict[tracer_short_name]["diags"][
                    "%s_SURF" % tracer_short_name
                ] = high_freq_op

        # 4. Per-zooplankton diagnostics
        for zooplankton_name in zooplankton_list:
            tracer_short_name = zooplankton_name + "C"
            if tracer_short_name in full_diag_dict.keys():
                full_diag_dict[tracer_short_name]["diags"][
                    "%s_zint_100m" % tracer_short_name
                ] = high_freq_op

        # 5. Write tracer-specific diagnostics to file
        for tracer_short_name in full_diag_dict.keys():
            # (a) Process ['properties'] dictionary for budget terms
            #     Note that this step will add to the ['diags'] dictionary but will not change previously set values
            per_tracer_properties = full_diag_dict[tracer_short_name]["properties"]
            if per_tracer_properties["include budget terms"]:
                value = low_freq_op
            else:
                value = "never_average"

            # These diagnostics should be included by default for tracers requested budget terms
            for key in ["adx", "ady", "dfx", "dfy", "tendency_vert_remap", "tendency"]:
                specific_key = "%s_%s" % (tracer_short_name, key)
                if (
                    specific_key
                    not in full_diag_dict[tracer_short_name]["diags"].keys()
                ):
                    full_diag_dict[tracer_short_name]["diags"][specific_key] = value

            if (
                per_tracer_properties["include budget terms"]
                and per_tracer_properties["has surface flux"]
            ):
                value = low_freq_op
            else:
                value = "never_average"

            # TODO: one more variable to figure out MOM6 equivalent of
            if False:
                # This diagnostic should be included by default for tracers requested budget terms
                # ONLY for tracers that have non-zero surface fluxes
                for key in ["KPP_NLtransport_"]:
                    specific_key = "%s_%s" % (key, tracer_short_name)
                    if (
                        specific_key
                        not in full_diag_dict[tracer_short_name]["diags"].keys()
                    ):
                        full_diag_dict[tracer_short_name]["diags"][specific_key] = value

            # (b) Loop through ['diags'] dictionary and write all diagnostics to file
            fout.write("#\n# Diagnostics for tracer %s\n#\n" % tracer_short_name)
            for diag in full_diag_dict[tracer_short_name]["diags"].keys():
                per_tracer_dict = full_diag_dict[tracer_short_name]["diags"]
                if per_tracer_dict[diag] != "none":
                    fout.write("%s : %s\n" % (diag, per_tracer_dict[diag]))

        # 6. Add section header for MARBL diagnostics
        #    (Another tool appends MARBL diagnostics to this file)
        fout.write("#\n########################################\n")
        fout.write("#      MARBL-generated diagnostics     #\n")
        fout.write("########################################\n#\n")


def get_2D_vars_from_MARBL_diagnostics(MARBL_diag_filename):
    """
    Read in MARBL_diagnostics, return a list of all variables that are 2D
    whether they are written to a stream or not
    """
    varlist = []
    with open(MARBL_diag_filename, "r") as fin:
        lines = fin.readlines()

    for line in lines:
        lstr = line.strip()
        # if user has modified MARBL_diagnostics and put it in SourceMods,
        # then file may include MARBL diagnostics. We can stop looking at
        # variable names when we reach that section
        if "MARBL-generated diagnostics" in lstr:
            break

        # if line starts with "#" it is a comment and we can continue to next line
        if lstr[0] == "#":
            continue

        # Pull varname out of line, append it to varlist if it is 2D
        varname = lstr.split(":")[0].strip()
        if _2D_varcheck(varname):
            varlist.append(varname)

    return varlist


def _2D_varcheck(varname):
    """
    Return true if variable is 2D
    """
    return (
        varname.startswith("STF_")
        or varname.startswith("Jint")
        or varname.endswith("_FLUX_CPL")
        or varname.endswith("_RIV_FLUX")
        or varname.endswith("_SURF")
        or varname.endswith("_zint_100m")
        or "_CAT_" in varname
    )
