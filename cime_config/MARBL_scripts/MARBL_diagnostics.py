""" Interface to the marbl_diagnostics_class object
"""

class MARBL_diagnostics_for_MOM(object):
    def __init__(self, MARBL_dir, caseroot, MARBL_settings):

        import sys, os

        # Set up arguments for marbl_diagnostics_class constructor
        # Note that this is a dictionary that will be used to pass named variables to class constructor
        # Arguments to be passed are
        # 1. default_diagnostics_file: full path to default_diagnostics.json
        #      (can be in SourceMods, otherwise comes from MARBL)
        # 2. MARBL_settings: a MARBL_settings_for_MOM object
        MARBL_args = dict()

        # User can put default_values.json in SourceMods, otherwise use file provided by MARBL
        MARBL_args["default_diagnostics_file"] = os.path.join(caseroot,"SourceMods","src.mom","diagnostics_latest.json")
        if not os.path.isfile(MARBL_args["default_diagnostics_file"]):
            MARBL_args["default_diagnostics_file"] = os.path.join(MARBL_dir, "defaults", "json", "diagnostics_latest.json")

        MARBL_args["MARBL_settings"] = MARBL_settings._MARBL_settings

        # MARBL can run in mks unit system instead of requiring MOM to convert to / from cgs
        MARBL_args["unit_system"] = "mks"

        # Import MARBL_diagnostics_file_class, which may come from MARBL_tools or SourceMods/src.mom
        # (i) need MARBL_dir in path for both branches of this if statement because even if
        #     MARBL_diagnostics_file_class.py is in SourceMods, it needs to import MARBL_tools itself
        sys.path.append(MARBL_dir)
        # (ii) Here's where we import from either MARBL_tools or SourceMods
        diagnostics_class_dir = os.path.join(caseroot, "SourceMods", "src.mom")
        if not os.path.isfile(os.path.join(diagnostics_class_dir, "MARBL_diagnostics_file_class.py")):
            from MARBL_tools import MARBL_diagnostics_file_class
        else:
            import imp
            import logging
            logger = logging.getLogger(__name__)
            logging.info('Importing MARBL_diagnostics_file_class.py from %s' % diagnostics_class_dir)
            diagnostics_class_module = diagnostics_class_dir+'/MARBL_diagnostics_file_class.py'
            if os.path.isfile(diagnostics_class_module):
                MARBL_diagnostics_file_class = imp.load_source('MARBL_diagnostics_file_class', diagnostics_class_module)
            else:
                logger.error('Can not find %s' % diagnostics_class_module)
                sys.exit(1)

        # Generate diagnostics object
        self.MARBL_diagnostic_dict = MARBL_diagnostics_file_class.MARBL_diagnostics_class(**MARBL_args)

    ################################################################################
    #                             PUBLIC CLASS METHODS                             #
    ################################################################################

    def write_diagnostics_file(self, diagnostics_file_out, diag_mode, append):
        """ Add all MARBL diagnostics to file containing MOM diagnostics
            Also create a list of diagnostics generated by MOM
        """
        diag_mode_loc = 'full' if diag_mode == 'test_suite' else diag_mode
        from MARBL_tools import generate_diagnostics_file
        generate_diagnostics_file(self.MARBL_diagnostic_dict, diagnostics_file_out, diag_mode_loc, append)

