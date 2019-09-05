import os
from MOM_RPS import MOM_RPS

class FType_diag_table(MOM_RPS):
    """diag_table file type encapsulator. Derived from MOM_RPS."""

    def read(self):
        assert self.input_format=="json", "diag_table file defaults can only be read from a json file."
        self._read_json()

    def write(self, output_path, case, add_params=dict()):
        assert self.input_format=="json", "diag_table file defaults can only be read from a json file."

        # Apply the guards on the general data to get the targeted values
        self.infer_guarded_vals(case)

        # Expand cime parameters in values of key:value pairs (e.g., $INPUTDIR)
        self.expand_cime_params_in_vals(case)

        with open(os.path.join(output_path), 'w') as diag_table:

            # Print header:
            casename = case.get_value("CASE")
            diag_table.write('"MOM6 diagnostic fields table for CESM case: '+casename+'"\n')
            diag_table.write('1 1 1 0 0 0\n') #TODO

            # max filename length:
            mfl = len(casename) +\
                  max([len(self.data['Files'][file_block_name]['suffix'])\
                              for file_block_name in self.data['Files']])\
                  + 4 # quotation marks and tabbing

            # Section 1: File section
            diag_table.write('### Section-1: File List\n')
            diag_table.write('#========================\n')
            for file_block_name in self.data['Files']:
                file_block = self.data['Files'][file_block_name]

                if file_block['fields']==None:
                    # No fields for this file. Skip to next file.
                    continue

                file_descr_str = ('{filename:'+str(mfl)+'s} {output_freq:3s} {output_freq_units:9s} 1, '
                                  '{time_axis_units:9s} "time"').\
                    format( filename = '"'+casename+'.'+file_block['suffix']+'",',
                            output_freq = str(file_block['output_freq'])+',',
                            output_freq_units = '"'+file_block['output_freq_units']+'",',
                            time_axis_units = '"'+file_block['time_axis_units']+'",')

                if 'new_file_freq' in file_block:
                    file_descr_str += ', '+str(file_block['new_file_freq'])+', '
                    if 'time_axis_units' in file_block:
                        file_descr_str += '"'+str(file_block['new_file_freq_units'])+'"'
                diag_table.write(file_descr_str+'\n')

            diag_table.write('\n')

            ## Field section (per file):
            diag_table.write('### Section-2: Fields List\n')
            diag_table.write('#=========================\n')
            for file_block_name in self.data['Files']:
                file_block = self.data['Files'][file_block_name]

                if file_block['fields']==None:
                    # No fields for this file. Skip to next file.
                    continue

                diag_table.write('# {filename}\n'.\
                    format(filename = file_block_name + ' ("'+casename+'.'+file_block['suffix']+'"):'))

                # keep a record of all fields in this file to make sure no duplicate field exists
                fields_all = []

                # Loop over bullet list of fields
                for field_block in file_block['fields']:
                    module = field_block['module']
                    packing = field_block['packing']
                    field_list_1d = sum(field_block['lists'],[])

                    # seperate field_name and output_name:
                    field_list_1d_seperated = []
                    for field in field_list_1d:
                        field_split = field.split(':')
                        if len(field_split)==2:
                            field = field_split[0], field_split[1]
                        elif len(field_split)==1:
                            field = field_split[0], field_split[0]
                        else:
                            raise RuntimeError("Cannot infer field name and output name for "+field)
                        field_list_1d_seperated.append(field)

                    # check if there are any duplicate fields in the same file:
                    for field_name, output_name in field_list_1d_seperated:
                        assert field_name not in fields_all, \
                            'Field "'+field_name+'" is listed more than once'+' in file: '+file_block['suffix']
                        fields_all.append(field_name)

                    mfnl = max([len(field) for field in field_list_1d]) + 3
                    mfnl = min(16,mfnl) # limit to 16
                    for field_name, output_name in field_list_1d_seperated:
                        diag_table.write(('{module_name:14s} {field_name:'+str(mfnl)+'}{output_name:'+str(mfnl)+'}'
                                          '{filename} "all", {reduction_method} {regional_section} {packing}\n').
                            format( module_name = '"'+module+'",',
                                    field_name = '"'+field_name+'",',
                                    output_name = '"'+output_name+'",',
                                    filename = '"'+casename+'.'+str(file_block['suffix'])+'",',
                                    reduction_method = '"'+str(file_block['reduction_method'])+'",',
                                    regional_section = '"'+str(file_block['regional_section'])+'",',
                                    packing = str(packing)
                                ) )

                diag_table.write('\n')

