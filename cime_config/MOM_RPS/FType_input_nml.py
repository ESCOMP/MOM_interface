import os
from CIME.ParamGen.paramgen import ParamGen

class FType_input_nml(ParamGen):
    """Encapsulates data and read/write methods for MOM6 (FMS) input.nml file"""

    def write(self, output_path, case):

        # From the general template (input_nml.yaml), reduce a custom input.nml for this case
        self.reduce(lambda varname: case.get_value(varname))

        # write the data in namelist format
        self.write_nml(output_path)
