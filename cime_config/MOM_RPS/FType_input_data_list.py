import os
from MOM_RPS import MOM_RPS

class FType_input_data_list(MOM_RPS):
    """Encapsulates data and read/write methods for MOM6 input_data_list file."""

    def write(self, output_path, case):

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_case_vars(case)

        # Apply the guards on the general data to get the targeted values
        self.infer_guarded_vals(case)

        with open(os.path.join(output_path), 'w') as input_data_list:
            for module in self._data:
                for var in self._data[module]:
                    val = self._data[module][var]
                    if val != None:
                        input_data_list.write(var+" = "+str(val)+"\n")

