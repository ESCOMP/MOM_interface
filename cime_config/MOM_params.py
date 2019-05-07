
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
            self._params = json.load(json_file)

        # 3. Check consistency
        self._check_json_consistency()

    def _check_json_consistency(self):
        #TODO
        pass




    def write_MOM_input(self, rundir, grid, compset):

        assert self.file_format=="json", "MOM_input file can only be generated from a json file."

        self.constraints = {"GRID": grid.strip(),
                            "COMPSET": compset.strip()}

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
                print("Variable: ", var)

                # list of potential values for this variable.
                value_list = self._params[module][var]["value"]

                val = None

                for value_constraints in value_list:
                    print("\t", value_constraints)
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


                    else:
                        raise RuntimeError("Cannot parse configurations for variable "+var)

                assert (val != None), "Cannot determine the value of "+var
                self._params[module][var]['final_value'] = val
                print("\t\t\t ", val)

            # 2. Now, write the MOM_input file


