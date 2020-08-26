import os
from MOM_RPS import MOM_RPS

class FType_input_data_list(MOM_RPS):
    """Encapsulates data and read/write methods for MOM6 input_data_list file."""

    def write(self, output_path, case, MOM_input_final=None):

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_case_vars(case, MOM_input_final)

        # Apply the guards on the general data to get the targeted values
        self.infer_values(case)

        with open(os.path.join(output_path), 'w') as input_data_list:
            for module in self._data:
                for file_category in self._data[module]:
                    file_path = self._data[module][file_category]
                    if file_path != None:
                        file_path = file_path.replace('"','').replace("'","")
                        if os.path.isabs(file_path):
                            input_data_list.write(file_category+" = "+file_path+"\n")
                        else:
                            pass # skip if custom INPUTDIR is used.

