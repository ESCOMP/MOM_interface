""" Interface to the marbl_settings_class object
"""

class MARBL_settings_for_MOM(object):
    def __init__(self, MARBL_dir, caseroot, ocn_grid, run_type, continue_run, ocn_bgc_config):

        import sys, os

        # Set up arguments for marbl_settings_class constructor
        # Note that this is a dictionary that will be used to pass named variables to class constructor
        # Arguments to be passed are
        # 1. default_settings_file: full path to default_settings.json; can be in SourceMods, otherwise comes from MARBL
        # 2. grid: CESM_x1 if running tx0.66v1 (until we come up with better tunings)
        # 3. saved_state_vars_source: "settings_file" for startup run, otherwise GCM
        MARBL_args = dict()

        settings_file = "settings_"+ocn_bgc_config+".json"

        # User can put settings_file in SourceMods, otherwise use file provided by MARBL
        MARBL_args["default_settings_file"] = os.path.join(caseroot,"SourceMods","src.mom", settings_file)
        if not os.path.isfile(MARBL_args["default_settings_file"]):
            MARBL_args["default_settings_file"] = os.path.join(MARBL_dir, "defaults", "json", settings_file)

        # User can modify user_nl_marbl (or user_nl_marbl_####) in caseroot
        MARBL_args["input_file"] = os.path.join(caseroot, "user_nl_marbl")
        if not os.path.isfile(MARBL_args["input_file"]):
            MARBL_args["input_file"] = None

        # Specify grid
        if ocn_grid.startswith("tx0.6"):
            MARBL_args["grid"] = "CESM_x1"
        else:
            MARBL_args["grid"] = "CESM_other"

        # If not a startup run, MARBL may want initial bury coefficient from restart file
        if run_type == "startup" and not continue_run:
            MARBL_args["saved_state_vars_source"] = "settings_file"
        else:
            MARBL_args["saved_state_vars_source"] = "GCM"

        # Import MARBL_settings_file_class, which may come from MARBL_tools or SourceMods/src.mom
        # (i) need MARBL_dir in path for both branches of this if statement because even if
        #     MARBL_settings_file_class.py is in SourceMods, it needs to import MARBL_tools itself
        sys.path.append(MARBL_dir)
        # (ii) Here's where we import from either MARBL_tools or SourceMods
        settings_class_dir = os.path.join(caseroot, "SourceMods", "src.mom")
        if not os.path.isfile(os.path.join(settings_class_dir, "MARBL_settings_file_class.py")):
            from MARBL_tools import MARBL_settings_file_class
        else:
            import imp
            import logging
            logger = logging.getLogger(__name__)
            logging.info('Importing MARBL_settings_file_class.py from %s' % settings_class_dir)
            settings_class_module = settings_class_dir+'/MARBL_settings_file_class.py'
            if os.path.isfile(settings_class_module):
                MARBL_settings_file_class = imp.load_source('MARBL_settings_file_class', settings_class_module)
            else:
                logger.error('Can not find %s' % settings_class_module)
                sys.exit(1)

        # Generate settings object
        self._MARBL_settings = MARBL_settings_file_class.MARBL_settings_class(**MARBL_args)

    ################################################################################
    #                             PUBLIC CLASS METHODS                             #
    ################################################################################

    def get_tracer_names(self):
        """ Returns a list of all tracers in current configuration
        """
        return self._MARBL_settings.get_tracer_names()

    #######################################

    def write_settings_file(self, settings_file_out):
        """ Write a settings file containing all MARBL settings
        """
        from MARBL_tools import generate_settings_file
        generate_settings_file(self._MARBL_settings, settings_file_out)

