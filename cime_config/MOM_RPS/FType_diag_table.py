import os
from collections import OrderedDict

from CIME.ParamGen.paramgen import ParamGen

from diag_table_streams import (
    CASENAME,
    DiagTableError,
    Field,
    FieldGroup,
    int_setting,
    REQUIRED_SETTINGS,
    Stream,
    STREAM_SETTINGS,
    write_diag_table,
)


class FType_diag_table(ParamGen):
    """Encapsulates data and read/write methods for MOM6 diag_table input file."""

    @staticmethod
    def resolve(unresolved_diag_table_path, resolved_diag_table_path, casename):
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
                    resolved_diag_table.write(line.replace(CASENAME, casename))

    def write(self, output_path, case, MOM_input_final):
        """Writes out the diag_table of a case.

        Parameters
        ----------
        output_path : str
            The path of the diag_table to be created. The case name is left
            unresolved in it, to be substituted later by the resolve method.
        case : CIME.case.Case
            The case whose diag_table is to be written.
        MOM_input_final : FType_MOM_params
            The MOM6 parameters of the case, i.e., MOM_input updated with
            MOM_override. Consulted for expandable variables that are MOM6
            parameters rather than case variables.
        """

        def expand_func(varname):
            val = case.get_value(varname)
            if val is None:
                val = (
                    MOM_input_final.data.get("Global", {}).get(varname, {}).get("value")
                )
            if val is None:
                raise DiagTableError(
                    "Cannot determine the value of the variable {} appearing in "
                    "the diag_table template: it is neither a case variable nor a "
                    "MOM6 parameter of this case.".format(varname)
                )
            return val

        # From the general template (diag_table.yaml), reduce a custom diag_table
        # for this case, and turn its file entries into streams.
        self.reduce(expand_func)
        write_diag_table(list(self._streams().values()), output_path)

    def _streams(self):
        """Returns the streams of this case, keyed and ordered by stream name."""
        assert self.reduced, "May only collect streams from a reduced diag_table."
        defaults = self.data.get("FileDefaults") or {}
        _check_defaults(defaults)
        if not self.data.get("Files"):
            raise DiagTableError(
                "The diag_table template has no Files section, and so describes "
                "no output at all."
            )
        streams = OrderedDict()
        for label, entry in self.data["Files"].items():
            stream = _stream_from_entry(label, entry, defaults)
            if stream.name in streams:
                streams[stream.name].merge(stream)
            else:
                streams[stream.name] = stream
        return streams


def _check_defaults(defaults):
    """Checks that the FileDefaults section only provides stream settings."""
    unknown = [key for key in defaults if key not in STREAM_SETTINGS]
    if unknown:
        raise DiagTableError(
            "Unknown setting(s) {} in the FileDefaults section of the diag_table "
            "template. Only the settings of a file may be given a default: "
            "{}.".format(", ".join(unknown), ", ".join(STREAM_SETTINGS))
        )


def _value_of(setting, entry, defaults, fallback=None):
    """Returns the value of a setting: the entry's, else the default, else fallback."""
    for source in (entry, defaults):
        value = source.get(setting)
        if value is not None:
            return value
    return fallback


def _stream_from_entry(label, entry, defaults):
    """Builds a Stream from one entry of the Files section of the template.

    Parameters
    ----------
    label : str
        The label of the entry, which is also the name of the stream unless the
        entry provides an explicit, possibly configuration dependent, name.
    entry : dict
        The reduced entry, i.e., its settings and its fields blocks.
    defaults : dict
        The reduced FileDefaults section, providing the value of any setting that
        the entry itself does not specify.
    """
    unknown = [
        key
        for key in entry
        if key != "name" and key not in STREAM_SETTINGS and not key.startswith("fields")
    ]
    if unknown:
        raise DiagTableError(
            "Unknown setting(s) {} in diag_table template entry {}. Valid "
            "settings are: {}, name, and fields blocks.".format(
                ", ".join(unknown), label, ", ".join(STREAM_SETTINGS)
            )
        )
    # A stream is named after its entry, unless the entry names itself. Only the
    # MARBL entries do, in renaming their files to reflect the frequency of a
    # spinup run, which a label cannot express because guards live in values.
    stream = Stream(entry.get("name") or label, labels=[label])
    for setting in REQUIRED_SETTINGS:
        stream.settings[setting] = _value_of(setting, entry, defaults)

    # A file that is written only once is never rolled over, and so has neither a
    # new_file_freq nor a date template in its name. Otherwise a new file is
    # started once per unit of the output frequency, unless said otherwise.
    if int_setting(stream.settings["output_freq"], "output_freq", stream.source) > 0:
        stream.settings["new_file_freq"] = _value_of(
            "new_file_freq", entry, defaults, 1
        )
        stream.settings["new_file_freq_units"] = _value_of(
            "new_file_freq_units",
            entry,
            defaults,
            stream.settings["output_freq_units"],
        )

    for fields_label in [key for key in entry if key.startswith("fields")]:
        fields_block = entry[fields_label]
        if fields_block is None:  # the guards of this block are all false
            continue
        try:
            unknown = [
                key
                for key in fields_block
                if key != "module" and not key.startswith("lists")
            ]
            if unknown:
                raise DiagTableError(
                    "the {} block has unknown key(s) {}. A fields block may only "
                    "have a module and lists of fields.".format(
                        fields_label, ", ".join(unknown)
                    )
                )
            if fields_block.get("module") is None:
                raise DiagTableError(
                    "the {} block has no module. Add one, naming the MOM6 "
                    "diagnostics module that its fields come from.".format(fields_label)
                )
            group = FieldGroup(fields_block["module"])
            for lists_label in [key for key in fields_block if key.startswith("lists")]:
                lists_block = fields_block[lists_label]
                if lists_block is None:  # the guards of this block are all false
                    continue
                for field_list in lists_block:
                    if not isinstance(field_list, list):
                        raise DiagTableError(
                            "the {} block holds {!r} where a list of fields was "
                            "expected. Each element of a lists block is itself a "
                            "list, so that field lists can be combined.".format(
                                lists_label, field_list
                            )
                        )
                    group.fields.extend(Field(spec) for spec in field_list)
            stream.groups.append(group)
        except DiagTableError as error:
            raise DiagTableError(
                "Cannot write {}: {}".format(stream.source, error)
            ) from error

    return stream
