from __future__ import print_function
from collections import OrderedDict
import os

class MOM_params(object,):
    """ Encapsulates data and methods for MOM6 case parameter files with the following formats:
        MOM_input, user_nl, json.
    """

    supported_formats = ["MOM_input", "user_nl", "json"]

    def __init__(self, path, file_format):

        self.path = path
        self.file_format = file_format

        if file_format not in MOM_params.supported_formats:
            raise RuntimeError("MOM parameter file format "+file_format+\
                                " not supported")

        if self.file_format == "MOM_input":
            self._read_MOM_input()
        elif self.file_format == "user_nl":
            self._read_user_nl()
        elif self.file_format == "json":
            self._read_json()


    def _read_MOM_input(self):
        #TODO
        pass

    def _read_user_nl(self):
        #TODO
        pass

    def _read_json(self):
        import json
        with open(self.path) as json_file:
            self._params = json.load(json_file, object_pairs_hook=OrderedDict)

        # 3. Check consistency
        self._check_json_consistency()

    def _check_json_consistency(self):
        #TODO
        pass

    def write_MOM_input(self, outfile_path, constraints=dict(), add_params=dict()):

        assert self.file_format=="json", "MOM_input file can only be generated from a json file."

        self.constraints = constraints

        # 1. First, determine parameter values for the given constraints of the case

        def _constraint_satisfied(constr_pair):
            " Checks if a given value constraint agrees with the constraints of the case"
            constr_key = constr_pair.split('==')[0].strip()\
                .replace('"','').replace("'","")
            constr_val = constr_pair.split('==')[1].strip()\
                .replace('"','').replace("'","")
            return self.constraints[constr_key] == constr_val

        for module in self._params:
            for var in self._params[module]:

                # list of potential values for this variable.
                value_list = self._params[module][var]["value"]

                # current value for this variable:
                val = None

                for value_constraints in value_list:
                    if value_constraints == "common":
                        val = value_list[value_constraints]

                    # multiple constraint pairs in value_constraints
                    elif ',' in value_constraints:
                        agrees = True
                        for constr_pair in value_constraints.split(','):
                            agrees = agrees and _constraint_satisfied(constr_pair)
                        if agrees:
                            val = value_list[value_constraints]

                    # a single constraint pair in value_constraints:
                    elif '==' in value_constraints:
                        if _constraint_satisfied(value_constraints):
                            val = value_list[value_constraints]

                    # value is to be received from add_params filled by buildnml:
                    elif self._params[module][var]["value"] == "None" and var in add_params:
                         val = add_params[var]

                    else:
                        print(self._params[module][var])
                        print("-----------------")
                        print(add_params)
                        raise RuntimeError("Cannot parse configurations for variable "+var)

                assert (val != None), "Cannot determine the value of "+var
                self._params[module][var]['final_val'] = val

        # 2. Now, write MOM_input
        with open(os.path.join(outfile_path), 'w') as MOM_input:
            tab = " "*32
            for module in self._params:
    
                # Begin module block:
                if module != "Global":
                    MOM_input.write("%"+module+"\n")

                for var in self._params[module]:
                    MOM_input.write(var+" = "+str(self._params[module][var]["final_val"])+"\n")
                    var_comments = self._params[module][var]["description"].split('\n')
                    var_comments[-1] += " Units: "+self._params[module][var]["units"]
                    for line in var_comments:
                         MOM_input.write(tab+"!"+line+"\n")
                    MOM_input.write("\n")

                # End module block:
                if module != "Global":
                    MOM_input.write(module+"%\n")

