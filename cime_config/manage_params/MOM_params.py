
class MOM_params(object,):
    """ Encapsulates data and methods for MOM6 case parameters """

    def __init__(self, path, file_format, grid, compset):

        # 2. Read default_params.json file:
        import json
        with open(default_params_path) as default_params:
            self._params = json.load(default_params)

        # 3. Check consistency
        self._check_json_consistency()

    def _check_json_consistency(self):
        #TODO
        pass

    def write_MOM_input(self, rundir, grid, compset):

        self._config = {"GRID": grid.strip(),
                        "COMPSET": compset.strip()}
        for module in self._params:
            for var in self._params[module]:
                print("Variable: ", var)

                # list of configurations for this variable.
                config_list = self._params[module][var]["value"]

                # the value determined by how the keys match self._config
                val = None

                for config in config_list:
                    print("\t", config)
                    if config == "common":
                        val = config_list[config] 

                    # multiple constraints in config
                    elif ',' in config:
                        agrees = True
                        for constraint in config.split(','):
                            constr_key = constraint.split('==')[0].strip()
                            constr_val = constraint.split('==')[1].strip()
                            agrees = agrees and self._config[constr_key] == constr_val
                            print ("\t\t\t\t\t\t",constr_key,constr_val, self._config[constr_key])
                        if agrees:
                            val = config_list[config] 

                    # a single constraint in config:
                    elif '==' in config:
                        constr_key = config.split('==')[0].strip()
                        constr_val = config.split('==')[1].strip()
                        if self._config[constr_key] == constr_val:
                            val = config_list[config]
                    

                    else:
                        raise RuntimeError("Cannot parse configurations for variable "+var)

                print("\t\t\t ", val)
                        
                             


    #def _get_param()
        
test = MOM_Params("json/default_params.json", "tx0.66v1", "C")
test.write_MOM_input("")
