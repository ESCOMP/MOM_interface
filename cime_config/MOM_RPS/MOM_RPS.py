from __future__ import print_function
from collections import OrderedDict
import os
import abc
import re
from rps_utils import get_str_type, is_logical_expr, has_expandable_var, eval_formula
from rps_utils import is_formula, eval_formula, search_nested_dict
import copy

### MOM Runtime Parameter System Module =======================================

class MOM_RPS(object,):
    """
    Base class for MOM6 Runtime Parameter System manager that provides the following
    three main functionalities:
    * Read in an input file to generate data dictionary.
    * Determine the values of expandable variables and evaluate formulas involving them.
    * Infer the final values of parameters for a given CIME case instance

    Attributes
    ----------
    data : dict or OrderedDict
        The data attribute to operate over. See Methods for the list of operations.

    Methods
    -------
    from_json(input_path)
        Reads in a given json input file and initializes a MOM_RPS object.
    from_yaml(input_path)
        Reads in a given yalm input file and initializes a MOM_RPS object.
    expand_case_vars(case)
        Replaces case variables (e.g., $OCN_GRID) in self.data entries (both in keys and values)
        with their values (e.g, tx0.66v1) and evaluates formulas
    infer_values(case)
        Determines the final values of all parameters in self.data by evaluating the
        conditional formulas preceding each option.
    """

    def __init__(self, data_dict):
        assert type(data_dict) in [dict, OrderedDict], \
            "MOM_RPS class requires a dict or OrderedDict as the initial data."
        self._data = copy.deepcopy(data_dict)

    @property
    def data(self):
        """Returns the data attribute of the MOM_RPS instance."""
        return self._data

    @classmethod
    def from_json(cls, input_path):
        """
        Reads in a given json input file and initializes a MOM_RPS object.

        Parameters
        ----------
        input_path: str
            Path to json input file containing the defaults.

        Returns
        -------
        MOM_RPS
            A MOM_RPS object with the data read from input_path.
        """

        import json
        with open(input_path) as json_file:
            _data = json.load(json_file, object_pairs_hook=OrderedDict)
        return cls(_data)

    @classmethod
    def from_yaml(cls, input_path):
        """
        Reads in a given yaml input file and initializes a MOM_RPS object.

        Parameters
        ----------
        input_path: str
            Path to yaml input file containing the defaults.

        Returns
        -------
        MOM_RPS
            A MOM_RPS object with the data read from input_path.
        """

        import yaml
        with open(input_path) as yaml_file:
            _data = yaml.safe_load(yaml_file)
        return cls(_data)

    def expand_case_vars(self, case, aux_rps_obj=None):
        """
        Replaces case variables (e.g., $OCN_GRID) in self._data entries (both in keys and values)
        with their values (e.g, tx0.66v1). Also evaluates formulas in values and replaces them
        with the outcome of their evaluations.

        Parameters
        ----------
        case: CIME.case.case.Case
            A cime case object whose parameter values are to be acquired when expanding parameters.
        aux_rps_obj: MOM_RPS
            An auxiliary MOM_RPS object to search when attempting to expand an expandable parameter
        """

        str_type = get_str_type()

        def _expand_case_var(entry, case):
            """ Returns the version of an entry where cime parameters are expanded"""

            def is_cime_param(param_str):
                """ Returns True if the parameter to expand is a CIME parameter, e.g., OCN_GRIDi."""
                cime_param = case.get_value(param_str)
                if cime_param==None:
                    return False
                return True

            def aux_rps_param(param_str):
                """ Returns True if the parameter to expand is a variable in the given aux_rps_obj data."""
                assert (isinstance(aux_rps_obj, MOM_RPS))
                vals = search_nested_dict(aux_rps_obj._data, param_str)
                if len(vals) > 1:
                    raise RuntimeError("Multiple entries of "+param_str+" found in aux_rps_obj")
                elif len(vals) == 0:
                    return None
                else:
                    val = vals[0]
                    if "value" in val:
                        val = val['value']
                    assert not isinstance(val, str_type) or "$" not in val, \
                        "Nested expandable parameters detected when inferring "+entry
                    return str(val).strip()

            assert has_expandable_var(entry)
            str_type = get_str_type()

            # first, infer ${*}
            expandable_params = re.findall(r'\$\{.+?\}',entry)
            for word in expandable_params:
                expandable_param = word.replace("${","").replace("}","")
                param_expanded = None
                if is_cime_param(expandable_param):
                    param_expanded = case.get_value(expandable_param)
                elif aux_rps_obj!=None:
                    param_expanded = aux_rps_param(expandable_param)
                if param_expanded == None:
                    raise RuntimeError("The param "+expandable_param+" is not a CIME xml"
                                       " variable for this case")
                entry = entry.replace(word, str(param_expanded))

            # now infer $*
            for word in entry.split():
                if word[0] == '$':
                    expandable_param = word[1:]
                    param_expanded = None
                    if is_cime_param(expandable_param):
                        param_expanded = case.get_value(expandable_param)
                    elif aux_rps_obj!=None:
                        param_expanded = aux_rps_param(expandable_param)
                    if param_expanded == None:
                        raise RuntimeError("The param "+expandable_param+" is not a CIME xml"
                                           " variable for this case")

                    if isinstance(param_expanded,str_type):
                        param_expanded = '"'+param_expanded+'"'
                    entry = entry.replace(word,str(param_expanded))

            return entry

        def _expand_val(val):

            if type(val) in [dict, OrderedDict]:
                for key_, val_ in val.items():
                    val[key_] = _expand_val(val_)
            elif isinstance(val, list):
                pass
            else:
                if has_expandable_var(val):
                    val_eval = _expand_case_var(val, case)
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


    def infer_values(self, case):
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
                                   "infer_values method is called!")
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

        def _eval_formula_recursive(val):
            if type(val) in [dict, OrderedDict]:
                for key_, val_ in val.items():
                    val[key_] = _eval_formula_recursive(val_)
            elif isinstance(val, list):
                pass
            else:
                if is_formula(val):
                    val = eval_formula(val[1:])
            return val

        # Step 1: Recursively determine the values to be picked
        _determine_value_recursive(self._data)

        # Step 2: Evaluate the formulas, if any:
        for key, val in self._data.items():
            self._data[key] = _eval_formula_recursive(val)

    def append(self, rps_obj):
        """ Adds the data of given rps_obj to the self data. If a data entry already exists in self,
            the value is overriden. Otherwise, the new data entry is simply added to self.
        """

        def update_recursive(old_dict,new_dict):
            for key, val in new_dict.items():
                if key in old_dict:
                    old_val = old_dict[key]
                    if type(val) in [dict, OrderedDict] and type(old_val) in [dict, OrderedDict]:
                        update_recursive(old_dict[key], new_dict[key])
                    else:
                        old_dict[key] = new_dict[key]
                else:
                    old_dict[key] = new_dict[key]

        update_recursive(self._data, rps_obj._data)

    @abc.abstractmethod
    def check_consistency(self):
        pass
