from __future__ import print_function
from collections import OrderedDict
import os
import abc
import re
from rps_utils import get_str_type, is_logical_expr, has_expandable_var, eval_formula

### MOM Runtime Parameter System Module =======================================

class MOM_RPS(object,):
    """
    Base class for MOM6 (R)untime Parameter System manager to provide the following
    three main functionalities:
        * Read in an input file to generate data dictionary
        * Determine the values of expandable variables and evaluate formulas involving them.
        * Infer the final values of parameters for a given CIME case instance

    Attributes
    ----------
    input_format : str
        The format of input file to be read in to generate the data

    Methods
    -------
    expand_case_vars(case)
        Replaces case variables (e.g., $OCN_GRID) in self.data entries (both in keys and values)
        with their values (e.g, tx0.66v1)

    """

    def __init__(self, input_path, input_format=None, output_path=None, output_format=None):
        self.input_file_read = False
        self.input_path = input_path
        self._input_format = input_format
        self.output_format = output_format
        self._data = None

        self.read()

    @property
    def data(self):
        return self._data

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
        """ Read in the json input file to initialize self._data. """
        import json
        with open(self.input_path) as json_file:
            self._data = json.load(json_file, object_pairs_hook=OrderedDict)
        self.input_file_read = True

    def _read_yaml(self):
        """ Read in the yaml input file to initialize self._data. """
        import yaml
        with open(self.input_path) as yaml_file:
            self._data = yaml.safe_load(yaml_file)

        self.input_file_read = True

    def _check_json_consistency(self):
        #TODO
        pass

    def expand_case_vars(self, case):
        """
        Replaces case variables (e.g., $OCN_GRID) in self._data entries (both in keys and values)
        with their values (e.g, tx0.66v1). Also evaluates formulas in values and replaces them
        with the outcome of their evaluations.

        Parameters
        ----------
        case: CIME.case.case.Case
            A cime case object whose parameter values are to be adopted.
        """

        str_type = get_str_type()

        def _expand_case_var(entry, case):
            """ Returns the version of an entry where cime parameters are expanded"""

            assert has_expandable_var(entry)
            str_type = get_str_type()

            # first, infer ${*}
            cime_params = re.findall(r'\$\{.+?\}',entry)
            for cime_param in cime_params:
                cime_param_strip = cime_param.replace("${","").replace("}","")
                cime_param_expanded = case.get_value(cime_param_strip)
                if cime_param_expanded==None:
                    raise RuntimeError("The guard "+cime_param_strip+" is not a CIME xml"
                                       " variable for this case")
                entry = entry.replace(cime_param,cime_param_expanded)

            # now infer $*
            for word in entry.split():
                if word[0] == '$':
                    cime_param = word[1:]
                    cime_param_expanded = case.get_value(cime_param)
                    if cime_param_expanded==None:
                        raise RuntimeError("The guard "+cime_param+" is not a CIME xml"
                                           " variable for this case")
                    if isinstance(cime_param_expanded,str_type):
                        cime_param_expanded = '"'+cime_param_expanded+'"'
                    entry = entry.replace(word,str(cime_param_expanded))

            return entry

        def _eval_formula(formula):
            if (isinstance(formula,str_type) and len(formula)>0 and formula[0]=='='):
                check_comparison_types(formula[1:])
                try:
                    formula = eval(formula[1:])
                except:
                    raise RuntimeError("Cannot evaluate formula: "+formula)
            return formula

        def _expand_val(val):

            if type(val) in [dict, OrderedDict]:
                for key_, val_ in val.items():
                    val[key_] = _expand_val(val_)
            elif isinstance(val, list):
                pass
            else:
                if has_expandable_var(val):
                    val_eval = _expand_case_var(val, case)
                    if (isinstance(val_eval, str_type) and len(val_eval)>0 and val_eval[0]=='='):
                        val_eval = eval_formula(val_eval[1:])
                    return val_eval

            return val

        def _expand_key(key, val):

            if type(val) in [dict, OrderedDict]:
                data_copy = val.copy() # a copy to iterate over while making changes in original dict
                for key_, val_ in data_copy.items():
                    val.pop(key_)
                    val[_expand_key(key_, val_)] = val_
            if has_expandable_var(key):
                    return _expand_case_var(key, case)
            return key

        # Step 1: Expand values:
        for key, val in self._data.items():
            self._data[key] = _expand_val(val)

        # Step 2: Expand keys:
        data_copy = self._data.copy() # a copy to iterate over while making changes in original dict
        for key, val in data_copy.items():
            self._data.pop(key)
            self._data[_expand_key(key, val)] = val


    def infer_guarded_vals(self, case):
        """ For a variable, if multiple values are provided in a value list, this function
            determines the appropriate value for the case by looking at guards
            to the left of values in yaml file and by comparing them against
            the xml variable of the case, e.g. OCN_GRID."""

        if not self._data:
            raise RuntimeError("Cannot apply the guards. No data found.")

        def _check_guard_satisfied(guard, case):
            " Checks if a given value guard agrees with the case settings."

            if has_expandable_var(guard):
                raise RuntimeError("The guard "+guard+" has an expandable case variable! "+\
                                   "expand_case_vars method must be called before "+\
                                   "infer_guarded_vals method is called!")
            else:
                guard_inferred = guard

            result = eval_formula(guard_inferred)
            assert type(result)==type(True), "Guard is not boolean: "+str(guard)
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
                    if _check_guard_satisfied(value_guard, case):
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

        # Recursive determine the values to be picked
        _determine_value_recursive(self._data)

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
