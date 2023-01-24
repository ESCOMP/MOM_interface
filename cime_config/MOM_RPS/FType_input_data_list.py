import os
from CIME.ParamGen.paramgen import ParamGen

class FType_input_data_list(ParamGen):
    """Encapsulates data and read/write methods for MOM6 input_data_list file."""

    def write(self, output_path, case, MOM_input_final=None):

        def expand_func(varname):
            val = case.get_value(varname)
            if val is None:
                val = MOM_input_final.data['Global'][varname]['value']
            if val is None:
                raise RuntimeError("Cannot determine the value of variable: "+varname)
            return val

        # From the general template (input_data_list.yaml), reduce a custom input_data_list for this case
        self.reduce(expand_func)

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

