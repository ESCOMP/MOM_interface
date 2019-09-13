from __future__ import print_function
from collections import OrderedDict
import os
import abc
import re
from rps_utils import get_str_type, is_logical_expr, has_param_to_expand, expand_cime_parameter

### MOM Runtime Parameter System Module =======================================

class MOM_RPS(object,):
    """ Base class for MOM6 (R)untime (P)arameter (S)ystem fileiiiii including:
            - Params files (MOM_input, MOM_override, user_nl_mom)
            - MOM_namelist (input.nml)
            - diag_table
    """

    def __init__(self, input_path, input_format="json", output_path=None, output_format=None):
        self.input_file_read = False
        self.input_path = input_path
        self.input_format = input_format
        self.output_format = output_format
        self.data = None

        self.read()

    def _read_json(self):
        import json
        with open(self.input_path) as json_file:
            self.data = json.load(json_file, object_pairs_hook=OrderedDict)
        self.input_file_read = True

    def _check_json_consistency(self):
        #TODO
        pass

    def infer_guarded_vals(self, case):
        """ For a variable, if multiple values are provided in a value list, this function
            determines the appropriate value for the case by looking at guards
            to the left of values in yaml file and by comparing them against
            the xml variable of the case, e.g. OCN_GRID."""

        if not self.data:
            raise RuntimeError("Cannot apply the guards. No data found.")

        def _guard_satisfied(guard, case):
            " Checks if a given value guard agrees with the case settings."

            if has_param_to_expand(guard):
                guard_inferred = expand_cime_parameter(guard, case)
            else:
                guard_inferred = guard

            try:
                result = eval(guard_inferred)
            except:
                raise RuntimeError("Cannot evaluate guard: "+guard+" in file: "+self.input_path)

            assert type(result)==type(True), "Guard is not boolean: "+str(guard)

            return result

        def _do_determine_value(multi_option_dict):
            """ From an ordered dict (multi_option_dict), whose entries are alternative values
                with guards, returns the last entry whose guards are satisfied
                by the case"""

            assert _is_multi_option_entry(multi_option_dict)
            assert type(multi_option_dict)==OrderedDict

            val = None
            for value_guards in multi_option_dict:
                if value_guards == "else":
                    pass # for now

                # multiple guard pairs in value_guards
                elif ',' in value_guards:
                    agrees = True
                    for guard_pair in value_guards.split(','):
                        agrees = agrees and _guard_satisfied(guard_pair, case)
                    if agrees: # with all guards:
                        val = multi_option_dict[value_guards]

                # a single guard pair in value_guards:
                elif ('==' in value_guards) or\
                     ('!=' in value_guards):
                    if _guard_satisfied(value_guards, case):
                        val = multi_option_dict[value_guards]

                # not a multi-option entry
                else:
                    raise RuntimeError("Error while determining guards")

            # If no other guard evaluates to true, get the value prefixed by "else":
            if val==None and "else" in multi_option_dict:
                val = multi_option_dict["else"]

            return val


        def _is_multi_option_entry(entry):
            """ returns true if a given dictionary has entries that consist of
                multi-option (alternative) guarded entries"""

            assert type(entry)==OrderedDict

            options = [child for child in entry if is_logical_expr(child)]
            if (len(options)>0):
                return True
            else:
                return False

        def _determine_value_recursive(entry):
            """ Given a yaml entry, recursively determines values to be adopted
                by picking the values with guards that are satisfied by the case config"""

            for child in entry:
                if (isinstance(child,list)):
                    continue
                elif (type(entry[child])==OrderedDict):
                    if (_is_multi_option_entry(entry[child])):
                        entry[child] = _do_determine_value(entry[child])
                    else:
                        _determine_value_recursive(entry[child])
                else:
                    continue

        for entry in self.data:
            _determine_value_recursive(self.data[entry])


    def expand_cime_params_in_vals(self, case):
        """ Expands cime parameters in values of key:value pairs"""

        def _expand_cime_params_in_vals_recursive(entry):
            """ Recursively expands cime parameters in values of key:value pairs"""

            for child in entry:
                if (isinstance(child,list)):
                    continue
                elif (type(entry[child])==OrderedDict):
                    _expand_cime_params_in_vals_recursive(entry[child])
                else:
                    if (has_param_to_expand(entry[child])):
                        entry[child] = expand_cime_parameter(entry[child],case)
                    else:
                        continue

        for entry in self.data:
            _expand_cime_params_in_vals_recursive(self.data[entry])

    @abc.abstractmethod
    def check_consistency(self):
        pass

    @abc.abstractmethod
    def read(self):
        raise NotImplementedError("read function must be implemented in the derived class.")
