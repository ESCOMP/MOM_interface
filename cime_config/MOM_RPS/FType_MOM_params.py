import os
from MOM_RPS import MOM_RPS
from rps_utils import get_str_type
from collections import OrderedDict

class FType_MOM_params(MOM_RPS):
    """ Encapsulates data and read/write methods for MOM6 case parameter files: MOM_input, user_nl.
    """

    supported_formats_out   = ["MOM_input", "MOM_override"]

    @classmethod
    def from_MOM_input(cls, input_path):
        """
        Reads in a given MOM_input file (or user_nl_mom) and initializes an FType_MOM_params
        object. This method is an alternative to from_yaml(input_path) and from_json(input_path)
        methods already available from the base MOM_RPS class.

        Parameters
        ----------
        input_path: str
            Path to MOM_input file to read in and generate a FType_MOM_params object.
        """

        _data = FType_MOM_params._read_MOM_input(input_path)
        return FType_MOM_params(_data)

    @staticmethod
    def _read_MOM_input(input_path):
        """Reads in input files in MOM_input syntax. Note that this method may be used to
           read in MOM_override and user_nl_mom too, since the syntax is the same, but
           write methods for MOM_input and MOM_override are different."""

        _data = OrderedDict()
        with open(input_path,'r') as param_file:
            within_comment_block = False
            curr_module = "Global"
            for line in param_file:
                if len(line)>1:
                    line_s = line.split()

                    # check if within comment block.
                    if (not within_comment_block) and line.strip()[0:2] == "/*":
                        within_comment_block = True

                    if within_comment_block and line.strip()[-2:] == "*/":
                        within_comment_block = False
                        continue

                    if not within_comment_block and line_s[0][0] != "!": # not a single comment line either
                        # check format:
                        if (curr_module=="Global") and line.strip()[-1] == "%":
                            curr_module = line.strip()[:-1]
                        elif curr_module!="Global" and line.strip()[0] == "%":
                            curr_module = "Global"
                        else:
                            # discard override keyword if provided:
                            if line_s[0] == "#override" and len(line_s)>1:
                                line_s = line_s[1:]
                            line_j = ' '.join(line_s)

                            # now parse the line:
                            if ("=" in line_j):
                                line_ss     = line_j.split("=")
                                param_str   = (line_ss[0]).strip()  # the first element is the parameter name
                                val_str     = ' '.join(line_ss[1:]) # the rest is tha value string
                                if '!' in val_str:
                                    val_str = val_str.split("!")[0] # discard the comment in val str, if there is

                                # add this module if not added before:
                                if not curr_module in _data:
                                    _data[curr_module] = dict()

                                # check if param already provided:
                                if param_str in _data[curr_module]:
                                    raise SystemExit('ERROR: '+param_str+' listed more than once in '+file_name)

                                # enter the parameter in the dictionary:
                                _data[curr_module][param_str] = {'value':val_str}
                            else:
                                raise SystemExit('ERROR: Cannot parse the following line in user_nl_mom: '+line)

            # Check if there is unclosed block:
            if within_comment_block:
                raise SystemExit('ERROR: faulty comment block!')
            if curr_module!="Global":
                raise SystemExit('ERROR: faulty module block!')

        return _data

    def write(self, output_path, output_format, case=None, def_params=None):
        if output_format == "MOM_input":
            assert case!=None, "Must provide a case object to write out MOM_input"
            self._write_MOM_input(output_path, case)
        elif output_format == "MOM_override":
            assert def_params!=None, "Must provide a def_params object to write out MOM_override"
            self._write_MOM_override(output_path, def_params)

    def _write_MOM_input(self, output_path, case):
        """ writes a MOM_input file from a given json or yaml parameter file in accordance with
            the guards and additional parameters that are passed. """

        str_type = get_str_type()

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_case_vars(case)

        # Apply the guards on the general data to get the targeted values
        self.infer_values(case)

        # 2. Now, write MOM_input

        MOM_input_header =\
        """/* WARNING: DO NOT EDIT this file. Any changes you make will be
        overriden. To make changes in MOM6 parameters within CESM
        framework, use SourceMods or user_nl_mom mechanisms.

        This input file provides the adjustable run-time parameters
        for version 6 of the Modular Ocean Model (MOM6). By default,
        this file contains the out-of-the-box CESM configuration. A
        full list of parameters for this case can be found in the
        corresponding MOM_parameter_doc.all file which is generated
        by the model at runtime. */\n\n"""

        with open(os.path.join(output_path), 'w') as MOM_input:

            MOM_input.write(MOM_input_header)

            tab = " "*32
            for module in self._data:

                # Begin module block:
                if module != "Global":
                    MOM_input.write(module+"%\n")

                for var in self._data[module]:
                    val = self._data[module][var]["value"]
                    if val==None:
                        continue

                    # write "variable = value" pair
                    MOM_input.write(var+" = "+ str(val) +"\n")

                    # Write the variable description:
                    var_comments = self._data[module][var]["description"].split('\n')
                    if len(var_comments[-1])==0:
                        var_comments.pop()
                    for line in var_comments:
                         MOM_input.write(tab+"! "+line+"\n")
                    MOM_input.write("\n")

                # End module block:
                if module != "Global":
                    MOM_input.write("%"+module+"\n")

    def _write_MOM_override(self, output_path, def_params):

        str_type = get_str_type()

        MOM_override_header =\
        """/* WARNING: DO NOT EDIT this file! Any user changes made in files
        in RUNDIR will be overriden. This file is automatically generated.
        MOM6 parameter changes may ve made via SourceMods or user_nl_mom
        within CASEROOT.*/\n"""

        with open(os.path.join(output_path), 'w') as MOM_override:

           MOM_override.write(MOM_override_header)

           for module in self._data:
                #Begin module block:
                if module != "Global":
                    MOM_override.write("\n"+module+"%\n")

                for var in self._data[module]:
                    val = self._data[module][var]["value"]

                    # parameter is provided in both MOM_input and user_nl_mom
                    if module in def_params.data and var in def_params.data[module]:

                        # values are different
                        if val != def_params.data[module][var]["value"]:
                            MOM_override.write('#override {varname} = {value}\n'.\
                                                format(varname=var, value=val) )

                        # values are the same
                        else:
                            MOM_override.write('!!! {varname} = {value} !(UNCHANGED)\n'.\
                                                format(varname=var, value=val) )

                    # parameter is provided only in user_nl_mom
                    else:
                        MOM_override.write('{varname} = {value}\n'.\
                                            format(varname=var, value=val) )

                #End module block:
                if module != "Global":
                    MOM_override.write("%"+module+"\n\n")
