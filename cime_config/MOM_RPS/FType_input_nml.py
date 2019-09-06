import os
from MOM_RPS import MOM_RPS

class FType_input_nml(MOM_RPS):
    """Encapsulates data and read/write methods for MOM6 (FMS) input.nml file"""

    def read(self):
        assert self.input_format=="json", "input.nml file defaults can only be read from a json file."
        self._read_json()
        self._check_json_consistency()

    def write(self, output_path, case):
        assert self.input_format=="json", "input.nml file can only be generated from a json input file."

        # Apply the guards on the general data to get the targeted values
        self.infer_guarded_vals(case)

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_cime_params_in_vals(case)

        with open(os.path.join(output_path), 'w') as input_nml:
            for module in self.data:
                input_nml.write("&"+module+"\n")

                for var in self.data[module]:
                    val = self.data[module][var]["value"]
                    if val==None:
                        continue
                    input_nml.write("    "+var+" = "+str(self.data[module][var]["value"])+"\n")

                input_nml.write('/\n\n')

