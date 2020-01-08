import os
from MOM_RPS import MOM_RPS

class FType_input_nml(MOM_RPS):
    """Encapsulates data and read/write methods for MOM6 (FMS) input.nml file"""

    def write(self, output_path, case):

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_case_vars(case)

        # Apply the guards on the general data to get the targeted values
        self.infer_values(case)

        with open(os.path.join(output_path), 'w') as input_nml:
            for module in self._data:
                input_nml.write("&"+module+"\n")

                for var in self._data[module]:
                    val = self._data[module][var]["value"]
                    if val==None:
                        continue
                    input_nml.write("    "+var+" = "+str(self._data[module][var]["value"])+"\n")

                input_nml.write('/\n\n')

