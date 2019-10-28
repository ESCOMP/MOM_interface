from __future__ import print_function
from collections import OrderedDict
import os
import abc
import re
from rps_utils import get_str_type, is_logical_expr, has_param_to_expand, expand_cime_parameter

### MOM Runtime Parameter System Module =======================================

class MOM_RPS(object,):
    """ Base class for MOM6 (R)untime Parameter System manager to provide the following
    three main functionalities:
        * Read in an input file to generate self.data dictionary
        * Determine the values of expandable variables and evaluate formulas involving them.
        * Infer the final values of parameters for a given CIME case instance

    Attributes
    ----------
    input_format : str
        The format of input file to be read in to generate the data
    """

    def __init__(self, input_path, input_format=None, output_path=None, output_format=None):
        self.input_file_read = False
        self.input_path = input_path
        self._input_format = input_format
        self.output_format = output_format
        self.data = None

        self.read()

    @property
    def input_format(self):
        if self._input_format == None:
            if self.input_path.endswith('.json'):
                self._input_format = 'json'
            elif self.input_path.endswith(('.yml', 'yaml')):
                self._input_format = 'yaml'
            else:
                raise RuntimeError("Cannot infer input format")
        return self._input_format

    def _read_json(self):
        """ Read in the json input file to initialize self.data. """
        import json
        with open(self.input_path) as json_file:
            self.data = json.load(json_file, object_pairs_hook=OrderedDict)
        self.input_file_read = True

    def _read_yaml(self):
        """ Read in the yaml input file to initialize self.data. """
        import yaml
        with open(self.input_path) as yaml_file:
            self.data = yaml.safe_load(yaml_file)

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
                assert type(result)==type(True), "Guard is not boolean: "+str(guard)
            except:
                raise RuntimeError("Cannot evaluate guard: "+guard+" in file: "+self.input_path)

            return result

        def _do_determine_value(multi_option_dict):
            """ From an ordered dict (multi_option_dict), whose entries are alternative values
                with guards, returns the last entry whose guards are satisfied
                by the case"""

            assert _is_guarded_entry(multi_option_dict)
            assert type(multi_option_dict) in [dict, OrderedDict]

            val = None
            for value_guard in multi_option_dict:
                if value_guard == "else":
                    pass # for now
                elif is_logical_expr(value_guard):
                    if _guard_satisfied(value_guard, case):
                        val = multi_option_dict[value_guard]
                else: # invalid guard
                    print("Options:", multi_option_dict)
                    raise RuntimeError("Error while determining guards")

            # If no other guard evaluates to true, get the value prefixed by "else":
            if val==None and "else" in multi_option_dict:
                val = multi_option_dict["else"]

            return val


        def _is_guarded_entry(entry):
            """ returns true if a given dictionary has entries that consist of
                conditional (possibly with alternatives), i.e., guarded entries"""

            assert type(entry) in [dict, OrderedDict]

            entry_logical = [is_logical_expr(child) for child in entry]
            if all(entry_logical):
                return True
            elif any(entry_logical):
                print("Entry: ", entry)
                raise RuntimeError("Not all members of the above entry is conditional:")
            else:
                return False

        def _determine_value_recursive(entry):
            """ Given a yaml entry, recursively determines values to be adopted
                by picking the values with guards that are satisfied by the case config"""

            for child in entry:
                if (isinstance(child,list)):
                    continue
                elif (type(entry[child]) in [dict, OrderedDict]):
                    if (_is_guarded_entry(entry[child])):
                        entry[child] = _do_determine_value(entry[child])
                    else:
                        _determine_value_recursive(entry[child])
                else:
                    continue

        for entry in self.data:
            _determine_value_recursive(self.data[entry])


    def expand_cime_params(self, case):
        """ Expands cime parameters in key:value pairs"""

        str_type = get_str_type()

        def _expand_cime_params_recursive(entry):
            """ Recursively expands cime parameters in key:value pairs"""

            children = [child for child in entry]
            for child in children:

                # first, values
                if (isinstance(child,list)):
                    pass
                elif (type(entry[child]) in [dict, OrderedDict]):
                    _expand_cime_params_recursive(entry[child])
                else:
                    if (has_param_to_expand(entry[child])):
                        entry[child] = expand_cime_parameter(entry[child],case)
                    else:
                        pass

                # now, keys:
                if has_param_to_expand(child):
                    child_expanded = expand_cime_parameter(child, case)
                    entry[child_expanded] = entry[child]
                    entry.pop(child)
                else:
                    child_expanded = child

                # now, evaluate formulas, if any:
                if (not isinstance(child_expanded,list)):
                    formula = entry[child_expanded]
                    if (isinstance(formula,str_type) and len(formula)>0 and formula[0]=='='):
                        try:
                            entry[child_expanded] = eval(formula[1:])
                        except:
                            raise RuntimeError("Cannot evaluate formula: "+formula+" for variable "+child_expanded)

        for entry in self.data:
            _expand_cime_params_recursive(self.data[entry])

    @abc.abstractmethod
    def check_consistency(self):
        pass

    def read(self):
        if self.input_format == "json":
            self._read_json()
        elif self.input_format == "yaml":
            self._read_yaml()
        else:
            raise NotImplementedError("Unknown input format: "+self.input_format+\
                                "\nMay need to implement a read() method in derived class")
