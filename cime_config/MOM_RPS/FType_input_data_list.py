import os
from MOM_RPS import MOM_RPS

class FType_input_data_list(MOM_RPS):
    """Encapsulates data and read/write methods for MOM6 input_data_list file."""

    def read(self):
        assert self.input_format=="json", "input_data_list file defaults can only be read from a json file."
        self._read_json()
        self._check_json_consistency()

    def write(self, output_path, case, add_params=dict()):
        assert self.input_format=="json", "input_data_list file defaults can only be read from a json file."

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_cime_params(case)

        # Apply the guards on the general data to get the targeted values
        self.infer_guarded_vals(case)

        with open(os.path.join(output_path), 'w') as input_data_list:
            for module in self.data:
                for var in self.data[module]:
                    val = self.data[module][var]
                    if val != None:
                        input_data_list.write(var+" = "+str(val)+"\n")

