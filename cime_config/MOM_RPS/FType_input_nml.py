from CIME.ParamGen.paramgen import ParamGen


class FType_input_nml(ParamGen):
    """Encapsulates data and read/write methods for MOM6 (FMS) input.nml file"""

    def write(self, output_path, case):

        # From the general template (input_nml.yaml), reduce a custom input.nml for this case
        self.reduce(lambda varname: case.get_value(varname))

        # Drop the variables whose guards are all false, rather than writing them as None
        for group in self._data.values():
            for var in [var for var, entry in group.items() if entry["values"] is None]:
                del group[var]

        # write the data in namelist format
        self.write_nml(output_path)
