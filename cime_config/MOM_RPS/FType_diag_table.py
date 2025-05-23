import os
from CIME.ParamGen.paramgen import ParamGen


class FType_diag_table(ParamGen):
    """Encapsulates data and read/write methods for MOM6 diag_table input file."""

    @classmethod
    def resolve(cls, unresolved_diag_table_path, resolved_diag_table_path, casename):
        """Resolve the casename in an unresolved diag_table.

        Parameters
        ----------
        unresolved_diag_table_path : str
            The path to the unresolved diag_table.
        resolved_diag_table_path : str
            The path to the resolved diag_table to be created.
        casename : str
            The casename to be resolved.
        """
        assert os.path.exists(unresolved_diag_table_path), (
            "Unresolved diag_table file not found: " + unresolved_diag_table_path
        )

        with open(resolved_diag_table_path, "w") as resolved_diag_table:
            with open(unresolved_diag_table_path, "r") as diag_table_unresolved:
                for line in diag_table_unresolved:
                    resolved_diag_table.write(line.replace("${CASE}", casename))

    def write(self, output_path, case, MOM_input_final):
        def get_all_fields(fields_block):
            """Given a fields block, returns a list of all fields."""
            all_fields = []
            if fields_block is not None:
                all_fields = []
                all_lists_blocks = [
                    fields_block[lists_label]
                    for lists_label in fields_block
                    if lists_label.startswith("lists")
                ]
                for lists_block in all_lists_blocks:
                    if lists_block is not None:
                        all_fields.extend(sum(lists_block, []))
            return all_fields

        def is_empty_file(file_block):
            """Returns true if the fields list of file is empty."""
            all_fields_blocks = [
                file_block[fields_label]
                for fields_label in file_block
                if fields_label.startswith("fields")
            ]
            for fields_block in all_fields_blocks:
                if fields_block is None:
                    continue
                all_lists_blocks = [
                    fields_block[lists_label]
                    for lists_label in fields_block
                    if lists_label.startswith("lists")
                ]
                for lists_block in all_lists_blocks:
                    if len(lists_block) > 0:
                        return False
            return True

        def expand_func(varname):
            val = case.get_value(varname)
            if val is None:
                val = MOM_input_final.data["Global"][varname]["value"]
            if val is None:
                raise RuntimeError("Cannot determine the value of variable: " + varname)
            return val

        # From the general template (diag_table.yaml), reduce a custom diag_table for this case
        self.reduce(expand_func)

        with open(os.path.join(output_path), "w") as diag_table:

            # Print header:
            casename = "${CASE}"
            diag_table.write(
                '"MOM6 diagnostic fields table for CESM case: ' + casename + '"\n'
            )
            diag_table.write("1 1 1 0 0 0\n")  # TODO
            filename = lambda suffix: '"' + casename + ".mom6." + suffix + '"'

            # max filename length:
            mfl = (
                max(
                    [
                        len(filename(self._data["Files"][file_block_name]["suffix"]))
                        for file_block_name in self._data["Files"]
                    ]
                )
                + 4
            )  # quotation marks and tabbing

            # Section 1: File section
            diag_table.write("### Section-1: File List\n")
            diag_table.write("#========================\n")

            for file_block_name in self._data["Files"]:
                file_block = self._data["Files"][file_block_name]
                fname = filename(file_block["suffix"])

                # if the fields list(s) is empty, skip to the next file:
                if is_empty_file(file_block):
                    continue

                file_descr_str = (
                    "{fname:"
                    + str(mfl)
                    + "s} {output_freq:3s} {output_freq_units:9s} 1, "
                    '{time_axis_units:9s} "time"'
                ).format(
                    fname=fname + ",",
                    output_freq=str(file_block["output_freq"]) + ",",
                    output_freq_units='"' + file_block["output_freq_units"] + '",',
                    time_axis_units='"' + file_block["time_axis_units"] + '",',
                )

                if "new_file_freq" in file_block:
                    file_descr_str += ", " + str(file_block["new_file_freq"]) + ", "
                    if "time_axis_units" in file_block:
                        file_descr_str += (
                            '"' + str(file_block["new_file_freq_units"]) + '"'
                        )
                diag_table.write(file_descr_str + "\n")

            diag_table.write("\n")

            ## Field section (per file):
            diag_table.write("### Section-2: Fields List\n")
            diag_table.write("#=========================\n")
            for file_block_name in self._data["Files"]:
                file_block = self._data["Files"][file_block_name]
                fname = filename(file_block["suffix"])

                # if the fields list(s) is empty, skip to the next file:
                if is_empty_file(file_block):
                    continue

                # write the header for the fields list of this file block
                diag_table.write("# {fname}\n".format(fname=fname))

                # keep a record of all fields in this file to make sure no duplicate field exists
                all_fields = []

                # all of the fields blocks, i.e., blocks starting with "fields" prefix
                all_fields_blocks = [
                    file_block[fields_label]
                    for fields_label in file_block
                    if fields_label.startswith("fields")
                ]

                # Loop over fields blocks
                for field_block in all_fields_blocks:
                    module = field_block["module"]
                    packing = field_block["packing"]
                    field_list_1d = get_all_fields(field_block)

                    # seperate field_name, alias, and reduction method
                    # (the latter two are optional)
                    field_list_1d_seperated = []
                    for field in field_list_1d:
                        field_split = field.split(":")
                        field_name = field_split[0]
                        alias = field_name
                        reduction = file_block["reduction_method"]
                        assert 1 <= len(field_split) <= 3, (
                            "Invalid field format: " + field
                        )
                        if len(field_split) >= 2:
                            alias = field_split[1]
                        if len(field_split) >= 3:
                            reduction = field_split[2]

                        field_list_1d_seperated.append((field_name, alias, reduction))

                    # check if there are any duplicate fields in the same file:
                    field_set = set()
                    for field_name, alias, reduction in field_list_1d_seperated:
                        if alias in field_set:
                            raise ValueError(
                                'Field "'
                                + alias
                                + '" is listed more than once'
                                + " in file: "
                                + file_block["suffix"]
                            )
                        field_set.add(alias)

                    mfnl = max([len(field) for field in field_list_1d]) + 3
                    mfnl = min(16, mfnl)  # limit to 16
                    w = lambda s: f'"{s}",'  # wrap string in quotes and add comma
                    for field_name, alias, reduction in field_list_1d_seperated:
                        diag_table.write(
                            f'{w(module)} {w(field_name):{mfnl}}{w(alias):{mfnl}}{fname}, "all", '
                            f'{w(reduction)} {w(file_block["regional_section"])} {packing}\n'
                        )

                diag_table.write("\n")
