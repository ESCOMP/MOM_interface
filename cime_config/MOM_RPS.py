from __future__ import print_function
from collections import OrderedDict
import os
import abc
import re

class MOM_RPS(object,):
    """ Base class for MOM6 (R)untime (P)arameter (S)ystem fileiiiii including:
            - Params files (MOM_input, MOM_override, user_nl_mom)
            - MOM_namelist (input.nml)
            - diag_table
    """

    def __init__(self, input_path, input_format="json", output_path=None, output_format=None):
        self.input_file_read = False
        self.input_path = input_path
        self.input_format = input_format
        self.data = None

        self.read()

    def _read_json(self):
        import json
        with open(self.input_path) as json_file:
            self.data = json.load(json_file, object_pairs_hook=OrderedDict)
        self.input_file_read = True

    def _check_json_consistency(self):
        #TODO
        pass

    def apply_constraints(self, case):
        """ For a variable, if multiple values are provided in a value list, this function
            determines the appropriate value for the case by looking at constraints
            (guards) to the left of values in yaml file and by comparing them against
            the xml variable of the case, e.g. OCN_GRID."""

        if not self.data:
            raise RuntimeError("Cannot apply the constraints. No data found.")

        def _constraint_satisfied(constr_pair, case):
            " Checks if a given value constraint agrees with the case settings."

            # determine logical operation:
            op_str = None
            if "==" in constr_pair:
                op_str = "=="
            elif "!=" in constr_pair:
                op_str = "!="
            else:
                raise RuntimeError("Cannot determine logical operation for constr pair: "+constr_pair)


            constr_key = constr_pair.split(op_str)[0].strip()\
                .replace('"','').replace("'","")
            constr_val = constr_pair.split(op_str)[1].strip()\
                .replace('"','').replace("'","")

            try:
                case_val = case.get_value(constr_key)
            except:
                raise RuntimeError("Cannot find the constraint "+constr_key+" in xml files")

            # Note: Case-insensitive comparison!
            if op_str=='==':
                return str(case_val).lower() == str(constr_val).lower()
            elif op_str=='!=':
                return str(case_val).lower() != str(constr_val).lower()
            else:
                raise RuntimeError("Cannot determine logical operation for constr pair: "+constr_pair)

        def _do_determine_value(multi_option_dict):
            """ From an ordered dict (multi_option_dict), whose entries are alternative values
                with guards (constraints), returns the last entry whose guards are satisfied
                by the case"""

            assert(_is_multi_option_entry(multi_option_dict))
            assert( type(multi_option_dict)==OrderedDict )

            val = None
            for value_constraints in multi_option_dict:
                if value_constraints == "common":
                    val = multi_option_dict[value_constraints]

                # multiple constraint pairs in value_constraints
                elif ',' in value_constraints:
                    agrees = True
                    for constr_pair in value_constraints.split(','):
                        agrees = agrees and _constraint_satisfied(constr_pair, case)
                    if agrees: # with all constaints:
                        val = multi_option_dict[value_constraints]

                # a single constraint pair in value_constraints:
                elif ('==' in value_constraints) or\
                     ('!=' in value_constraints):
                    if _constraint_satisfied(value_constraints, case):
                        val = multi_option_dict[value_constraints]

                # not a multi-option entry
                else:
                    raise RuntimeError("Error while determining constraints")

            return val


        def _is_multi_option_entry(entry):
            """ returns true if a given dictionary has entries that consist of
                multi-option (alternative) guarded entries"""

            assert( type(entry)==OrderedDict )

            options = [child for child in entry if 'common' in child or '==' in child or '!=' in child]
            if (len(options)>0):
                return True
            else:
                return False

        def _determine_value_recursive(entry):
            """ Given a yaml entry, recursively determines values to be adopted
                by picking the values with guards that satisfy the case constraints"""

            for child in entry:
                if (isinstance(child,list)):
                    continue
                elif (type(entry[child])==OrderedDict):
                    if (_is_multi_option_entry(entry[child])):
                        entry[child] = _do_determine_value(entry[child])
                    else:
                        _determine_value_recursive(entry[child])
                else:
                    continue

        for entry in self.data:
            _determine_value_recursive(self.data[entry])



    def deduce_special_vals(self, case):
        """ Replaces the values defined with special keys, i.e., ${XML_VAR}, in yaml files"""

        def _has_special_value(entry):
            """ Checks if a given entry of type string has a special value to be deduced. """
            assert( type(entry)!=OrderedDict )
            if isinstance(entry,basestring) and "${" in entry:
                return True
            else:
                return False

        def _do_deduce_special_vals(entry):
            """ Returns the deduced value for a given entry with special value """

            assert(_has_special_value(entry))

            special_keys_list = re.findall(r'\$\{.+?\}',entry)
            for special_key in special_keys_list:
                special_key_strip = special_key.replace("$","").replace("{","").replace("}","")
                special_val = case.get_value(special_key_strip)
                if special_val==None:
                    raise RuntimeError("The constraint "+special_key_strip+" is not a CIME xml"
                                       " variable for this case")
                entry = entry.replace(special_key,special_val)
            return entry


        def _deduce_special_vals_recursive(entry):
            """ Recursive deduces special values of a given yaml entry. """

            for child in entry:
                if (isinstance(child,list)):
                    continue
                elif (type(entry[child])==OrderedDict):
                    _deduce_special_vals_recursive(entry[child])
                else:
                    if (_has_special_value(entry[child])):
                        entry[child] = _do_deduce_special_vals(entry[child])
                    else:
                        continue

        for entry in self.data:
            _deduce_special_vals_recursive(self.data[entry])

    @abc.abstractmethod
    def check_consistency(self):
        pass

    @abc.abstractmethod
    def read(self):
        raise NotImplementedError("read function must be implemented in the derived class.")


class MOM_input_nml(MOM_RPS):

    def read(self):
        assert self.input_format=="json", "input.nml file defaults can only be read from a json file."
        self._read_json()
        self._check_json_consistency()

    def write(self, output_path, case):
        assert self.input_format=="json", "input.nml file can only be generated from a json input file."

        # Apply the constraints on the general data to get the targeted values
        self.apply_constraints(case)

        # Replace special xml values (e.g., $INPUTDIR) with their actual values
        self.deduce_special_vals(case)

        with open(os.path.join(output_path), 'w') as input_nml:
            for module in self.data:
                input_nml.write("&"+module+"\n")

                for var in self.data[module]:
                    val = self.data[module][var]["value"]
                    if val==None:
                        continue
                    input_nml.write("    "+var+" = "+str(self.data[module][var]["value"])+"\n")

                input_nml.write('/\n\n')

class Input_data_list(MOM_RPS):

    def read(self):
        assert self.input_format=="json", "input_data_list file defaults can only be read from a json file."
        self._read_json()
        self._check_json_consistency()

    def write(self, output_path, case, add_params=dict()):
        assert self.input_format=="json", "input_data_list file defaults can only be read from a json file."

        # Apply the constraints on the general data to get the targeted values
        self.apply_constraints(case)

        # Replace special xml values (e.g., $INPUTDIR) with their actual values
        self.deduce_special_vals(case)

        with open(os.path.join(output_path), 'w') as input_data_list:
            for module in self.data:
                for var in self.data[module]:
                    input_data_list.write(var+" = "+str(self.data[module][var]["value"])+"\n")

class Diag_table(MOM_RPS):

    def read(self):
        assert self.input_format=="json", "diag_table file defaults can only be read from a json file."
        self._read_json()

    def write(self, output_path, case, add_params=dict()):
        assert self.input_format=="json", "diag_table file defaults can only be read from a json file."

        # Apply the constraints on the general data to get the targeted values
        self.apply_constraints(case)

        # Replace special xml values (e.g., $INPUTDIR) with their actual values
        self.deduce_special_vals(case)

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
                    file_descr_str += ', "'+str(file_block['new_file_freq'])+'", '
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

                    # check if there are any duplicate fields in the same file:
                    for field in field_list_1d:
                        assert field not in fields_all, \
                            'Field "'+field+'" is listed more than once'+' in file: '+file_block['suffix']
                        fields_all.append(field)

                    mfnl = max([len(field) for field in field_list_1d]) + 3
                    mfnl = min(16,mfnl) # limit to 16
                    for field in field_list_1d:
                        diag_table.write(('{module_name:14s} {field:'+str(mfnl)+'}{field:'+str(mfnl)+'}'
                                          '{filename} "all", {reduction_method} {regional_section} {packing}\n').
                            format( module_name = '"'+module+'",',
                                    field = '"'+field+'",',
                                    filename = '"'+casename+'.'+str(file_block['suffix'])+'",',
                                    reduction_method = '"'+str(file_block['reduction_method'])+'",',
                                    regional_section = '"'+str(file_block['regional_section'])+'",',
                                    packing = str(packing)
                                ) )

                diag_table.write('\n')


#                for file_list file_block['field_lists']:


            ## Field section:
            #for file_block in self.data:
            #    fields = []
            #    if 'native' in self.data[file_block]['fields']:
            #        fields += [("ocean_model",f) for f in self.data[file_block]['fields']['native']]
            #    if 'z_star' in self.data[file_block]['fields']:
            #        fields += [("ocean_model_z",f) for f in self.data[file_block]['fields']['z_star']]

            #    # header:
            #    diag_table.write('### Field list for {filename}\n'.
            #        format(filename = '"'+casename+'.'+self.data[file_block]['suffix']+'":'))

            #    # max fieldname length:
            #    mfnl = max([len(field) for m,field in fields]) + 4 # plus tabbing
            #    mfnl = min([mfnl, 14]) # limit to 14?

            #    for module_name, field in fields:
            #        dia8yyg_table.write(('{module_name:16s}{field:'+str(mfnl)+'}{field:'+str(mfnl)+'}'
            #                          '{filename}"all",{reduction_method}"none",8\n').
            #            format( module_name = '"'+module_name+'",',
            #                    field = '"'+field+'",',
            #                    filename = '"'+casename+'.'+self.data[file_block]['suffix']+'",',
            #                    reduction_method = '"'+self.data[file_block]['reduction_method']+'",'
            #                ) )

            #    diag_table.write('\n')


class MOM_Params(MOM_RPS):
    """ Encapsulates data and methods for MOM6 case parameter files with the following formats:
        MOM_input, user_nl, json.
    """

    supported_formats = ["MOM_input", "user_nl", "json"]

    def __init__(self, input_path, input_format="json"):
        MOM_RPS.__init__(self, input_path, input_format)

        if self.input_format not in MOM_Params.supported_formats:
            raise RuntimeError("MOM parameter file format "+file_format+\
                                " not supported")

    def read(self):
        if self.input_format == "MOM_input":
            self._read_MOM_input()
        elif self.input_format == "user_nl":
            self._read_user_nl()
        elif self.input_format == "json":
            self._read_json()
            self._check_json_consistency()


    def _read_MOM_input(self):
        #TODO
        pass

    def _read_user_nl(self):
        #TODO
        pass

    def write(self, output_path, case, add_params=dict()):
        """ writes a MOM_input file from a given json parameter file in accordance with
            the constraints and additional parameters that are passed. """

        assert self.input_format=="json", "MOM_input file can only be generated from a json input file."


        # Apply the constraints on the general data to get the targeted values
        self.apply_constraints(case)

        # Replace special xml values (e.g., $INPUTDIR) with their actual values
        self.deduce_special_vals(case)

        # 2. Now, write MOM_input

        MOM_input_header =\
        """/* WARNING: DO NOT EDIT this file. Any changes you make will be overriden. To make
        changes in MOM6 parameters within CESM framework, use SourceMods or
        user_nl_mom mechanisms.

        This input file provides the adjustable run-time parameters for version 6 of
        the Modular Ocean Model (MOM6), a numerical ocean model developed at NOAA-GFDL.
        Where appropriate, parameters use usually given in MKS units.

        This MOM_input file contains the default configuration for CESM. A full list of
        parameters for this example can be found in the corresponding
        MOM_parameter_doc.all file which is generated by the model at run-time. */\n\n"""

        with open(os.path.join(output_path), 'w') as MOM_input:

            MOM_input.write(MOM_input_header)

            tab = " "*32
            for module in self.data:

                # Begin module block:
                if module != "Global":
                    MOM_input.write(module+"%\n")

                for var in self.data[module]:
                    val = self.data[module][var]["value"]
                    if val==None:
                        continue

                    # write "variable = value" pair
                    MOM_input.write(var+" = "+str(self.data[module][var]["value"])+"\n")

                    # Write the variable description:
                    var_comments = self.data[module][var]["description"].split('\n')
                    if len(var_comments[-1])==0:
                        var_comments.pop()
                    for line in var_comments:
                         MOM_input.write(tab+"! "+line+"\n")
                    MOM_input.write("\n")

                # End module block:
                if module != "Global":
                    MOM_input.write("%"+module+"\n")

