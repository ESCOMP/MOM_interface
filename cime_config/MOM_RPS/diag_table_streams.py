"""Stream model and writer for the MOM6 diag_table.

A *stream* is one MOM6 output file: one entry in the file list of the diag_table
(its Section-1) together with the fields written to that file (its Section-3).
Streams are built from param_templates/diag_table.yaml by FType_diag_table.

The name of a stream is also the file name segment that follows the case name
and the component name, i.e., a stream named "h.native" is written to
${CASE}.mom6.h.native.<date>.nc. The <date> part is not specified by hand: it is
derived from how often a new file is started (new_file_freq_units).
"""

import re
from collections import OrderedDict

# File name date templates
DATE_TEMPLATES = OrderedDict(
    [
        ("years", "%4yr"),
        ("months", "%4yr-%2mo"),
        ("days", "%4yr-%2mo-%2dy"),
        ("hours", "%4yr-%2mo-%2dy-%2hr"),
        ("minutes", "%4yr-%2mo-%2dy-%2hr%2mi"),
        ("seconds", "%4yr-%2mo-%2dy-%2hr%2mi%2sc"),
    ]
)

# Units accepted for output_freq and new_file_freq.
FREQ_UNITS = tuple(DATE_TEMPLATES)

# MOM6 diagnostics modules, one per vertical coordinate of the output.
MODULES = ("ocean_model", "ocean_model_z", "ocean_model_rho2")

# The case name is not known when the diag_table is written, so the file names
# carry this placeholder, which FType_diag_table.resolve substitutes later.
CASENAME = "${CASE}"

# Reduction methods accepted by FMS. Within a group, the alternative spellings
# are equivalent (see init_output_field in FMS diag_util.F90).
REDUCTION_METHODS = (
    ".true.",
    "mean",
    "average",
    "avg",
    ".false.",
    "none",
    "point",
    "rms",
    "min",
    "minimum",
    "max",
    "maximum",
    "sum",
    "cumsum",
)

# Reduction methods that take a trailing sample count, e.g., diurnal8.
_COUNTED_REDUCTIONS = ("diurnal", "pow")

# Number of bytes per output value: 1 is double precision, 2 single precision.
PACKING_VALUES = (1, 2)

# Settings of a stream, i.e., of an entry in the file list of the diag_table.
# new_file_freq and new_file_freq_units are absent for streams that are written
# only once (output_freq < 0).
STREAM_SETTINGS = (
    "output_freq",
    "output_freq_units",
    "new_file_freq",
    "new_file_freq_units",
    "time_axis_units",
    "reduction_method",
    "regional_section",
    "packing",
)

# Settings that every stream must have a value for. The two of STREAM_SETTINGS
# that are missing here, new_file_freq and new_file_freq_units, are absent for a
# stream that is written only once, and so is never rolled over.
REQUIRED_SETTINGS = (
    "output_freq",
    "output_freq_units",
    "time_axis_units",
    "reduction_method",
    "regional_section",
    "packing",
)

_FIELD_NAME = re.compile(r"^\w+$")
_REGIONAL_SECTION = re.compile(r"^\s*(-?[\d.]+\s+){5}-?[\d.]+\s*$")


class DiagTableError(Exception):
    """Raised when a diag_table cannot be generated as specified."""


def is_valid_reduction(reduction):
    """Returns True if reduction is a reduction method accepted by FMS.

    Example
    -------
    >>> is_valid_reduction("mean") and is_valid_reduction("diurnal8")
    True
    >>> is_valid_reduction("median") or is_valid_reduction("pow")
    False
    """
    if reduction in REDUCTION_METHODS:
        return True
    return any(
        re.match(r"^" + prefix + r"\d+$", str(reduction))
        for prefix in _COUNTED_REDUCTIONS
    )


def int_setting(value, setting, source):
    """Returns the value of a whole number setting, or reports what is wrong.

    int() is not called on a setting directly, so that a missing or non-numeric
    value is reported in terms of the stream it belongs to rather than escaping
    as a TypeError or a ValueError.

    Parameters
    ----------
    value:
        The value to interpret, which may be missing, i.e., None.
    setting: str
        Name of the setting, for the error message.
    source: str
        Where the setting came from, for the error message.

    Example
    -------
    >>> int_setting(2, "packing", 'stream "h.native"')
    2
    """
    if value is None:
        raise DiagTableError(
            "Cannot write {}: it has no value for {}.".format(source, setting)
        )
    try:
        return int(value)
    except (TypeError, ValueError):
        raise DiagTableError(
            'Cannot write {}: its {} is "{}", which is not a whole '
            "number.".format(source, setting, value)
        ) from None


def is_valid_regional_section(section):
    """Returns True if section is "none" (global) or six coordinate bounds.

    Example
    -------
    >>> is_valid_regional_section("none")
    True
    >>> is_valid_regional_section("-5.75 19.0 78.93 78.93 -1 -1")
    True
    >>> is_valid_regional_section("-5.75 19.0")
    False
    """
    return str(section) == "none" or bool(_REGIONAL_SECTION.match(str(section)))


class Field:
    """A single diagnostic field written to a stream.

    A field is given as "name[:output_name[:reduction]]", where output_name
    defaults to name, and reduction defaults to the reduction method of the
    stream that the field belongs to.

    Example
    -------
    >>> field = Field("KPP_OBLdepth:oml_max:max")
    >>> field.name, field.output_name, field.reduction
    ('KPP_OBLdepth', 'oml_max', 'max')
    >>> Field("tos").output_name, Field("tos").reduction
    ('tos', None)
    """

    def __init__(self, spec):
        self.spec = str(spec).strip()
        parts = [part.strip() for part in self.spec.split(":")]
        if not 1 <= len(parts) <= 3 or not all(parts):
            raise DiagTableError(
                'Invalid field: "{}". Expected "name", "name:output_name", or '
                '"name:output_name:reduction".'.format(self.spec)
            )
        for part in parts[:2]:
            if not _FIELD_NAME.match(part):
                raise DiagTableError(
                    'Invalid field name "{}" in "{}". Field and output names may '
                    "contain letters, digits and underscores only.".format(
                        part, self.spec
                    )
                )
        self.name = parts[0]
        self.output_name = parts[1] if len(parts) > 1 else self.name
        self.reduction = parts[2] if len(parts) > 2 else None
        if self.reduction is not None and not is_valid_reduction(self.reduction):
            raise DiagTableError(
                'Invalid reduction method "{}" in field "{}". Valid methods are: '
                "{}, diurnal<n>, pow<n>.".format(
                    self.reduction, self.spec, ", ".join(REDUCTION_METHODS)
                )
            )

    def __repr__(self):
        return "Field({!r})".format(self.spec)


class FieldGroup:
    """The fields that a stream receives from one MOM6 diagnostics module."""

    def __init__(self, module, fields=None):
        if module not in MODULES:
            raise DiagTableError(
                'Invalid diagnostics module "{}". Valid modules are: {}.'.format(
                    module, ", ".join(MODULES)
                )
            )
        self.module = module
        self.fields = list(fields) if fields else []

    def __repr__(self):
        return "FieldGroup({!r}, {} fields)".format(self.module, len(self.fields))


class Stream:
    """One MOM6 output file, i.e., one entry in the diag_table file list.

    Attributes
    ----------
    name: str
        Name of the stream, e.g., "h.native". Also the file name segment that
        follows the case name and the component name.
    settings: dict
        Stream settings, keyed by the names in STREAM_SETTINGS.
    groups: list of FieldGroup
        The fields written to this stream, grouped by diagnostics module.
    labels: list of str
        Labels of the diag_table template entries that this stream was built
        from. Used in error messages only.
    """

    def __init__(self, name, settings=None, groups=None, labels=None):
        self.name = name
        self.settings = dict(settings) if settings else {}
        self.groups = list(groups) if groups else []
        self.labels = list(labels) if labels else []

    @property
    def source(self):
        """Describes this stream and its origin, for error messages."""
        return 'stream "{}" (from template entry {})'.format(
            self.name, " and ".join(self.labels) or "(unknown)"
        )

    @property
    def date_template(self):
        """The date part of the file name, derived from new_file_freq_units."""
        if self.settings.get("new_file_freq") is None:
            return ""
        units = self.settings.get("new_file_freq_units")
        if units not in DATE_TEMPLATES:
            raise DiagTableError(
                'Cannot write {}: its new_file_freq_units is "{}", which is not '
                "one of: {}.".format(self.source, units, ", ".join(FREQ_UNITS))
            )
        return DATE_TEMPLATES[units]

    @property
    def suffix(self):
        """The full file name segment, i.e., the name plus the date template."""
        return self.name + self.date_template

    @property
    def is_empty(self):
        """Returns True if no field is written to this stream."""
        return not any(group.fields for group in self.groups)

    def output_names(self):
        """Returns the output names of all fields written to this stream."""
        return [field.output_name for group in self.groups for field in group.fields]

    def group_for(self, module):
        """Returns the field group of a module, creating it if necessary."""
        for group in self.groups:
            if group.module == module:
                return group
        group = FieldGroup(module)
        self.groups.append(group)
        return group

    def merge(self, other):
        """Merges the fields of another stream of the same name into this one.

        Two template entries may resolve to the same stream name, in which case
        they describe the same output file and must agree on its settings. Fields
        that both entries request are written only once.
        """
        for setting in STREAM_SETTINGS:
            mine, theirs = self.settings.get(setting), other.settings.get(setting)
            if mine != theirs:
                raise DiagTableError(
                    'Template entries {} and {} both describe the stream "{}", '
                    "but they disagree on {}: {!r} vs {!r}.".format(
                        " and ".join(self.labels),
                        " and ".join(other.labels),
                        self.name,
                        setting,
                        mine,
                        theirs,
                    )
                )
        for group in other.groups:
            target = self.group_for(group.module)
            existing = {field.output_name: field for field in target.fields}
            for field in group.fields:
                duplicate = existing.get(field.output_name)
                if duplicate is None:
                    target.fields.append(field)
                elif duplicate.spec != field.spec:
                    raise DiagTableError(
                        'Template entries {} and {} both write "{}" to stream '
                        '"{}", but they request it differently: "{}" vs '
                        '"{}".'.format(
                            " and ".join(self.labels),
                            " and ".join(other.labels),
                            field.output_name,
                            self.name,
                            duplicate.spec,
                            field.spec,
                        )
                    )
        self.labels.extend(other.labels)

    def validate(self):
        """Checks that this stream can be written to the diag_table."""
        settings = self.settings
        for setting in REQUIRED_SETTINGS:
            if settings.get(setting) is None:
                raise DiagTableError(
                    "Cannot write {}: it has no value for {}.".format(
                        self.source, setting
                    )
                )
        int_setting(settings["output_freq"], "output_freq", self.source)
        if settings["output_freq_units"] not in FREQ_UNITS:
            raise DiagTableError(
                'Cannot write {}: its output_freq_units is "{}", which is not one '
                "of: {}.".format(
                    self.source, settings["output_freq_units"], ", ".join(FREQ_UNITS)
                )
            )
        if not is_valid_reduction(settings["reduction_method"]):
            raise DiagTableError(
                'Cannot write {}: its reduction_method is "{}", which is not one '
                "of: {}, diurnal<n>, pow<n>.".format(
                    self.source,
                    settings["reduction_method"],
                    ", ".join(REDUCTION_METHODS),
                )
            )
        if not is_valid_regional_section(settings["regional_section"]):
            raise DiagTableError(
                'Cannot write {}: its regional_section is "{}", which is neither '
                '"none" nor six space separated bounds.'.format(
                    self.source, settings["regional_section"]
                )
            )
        packing = int_setting(settings["packing"], "packing", self.source)
        if packing not in PACKING_VALUES:
            raise DiagTableError(
                "Cannot write {}: its packing is {}, which is not one of: "
                "{}.".format(
                    self.source,
                    settings["packing"],
                    ", ".join(str(value) for value in PACKING_VALUES),
                )
            )
        self.date_template  # raises if new_file_freq_units is invalid

        # A given output name may be written to a file only once.
        seen = set()
        for name in self.output_names():
            if name in seen:
                raise DiagTableError(
                    'Cannot write {}: the field "{}" is written to it more than '
                    "once.".format(self.source, name)
                )
            seen.add(name)

    def __repr__(self):
        return "Stream({!r}, {} fields)".format(self.name, len(self.output_names()))


def write_diag_table(streams, output_path):
    """Writes a diag_table for the given streams.

    Parameters
    ----------
    streams: list of Stream
        The streams of the case, in the order their files are to be listed.
        Streams with no fields are not written out.
    output_path: str
        Path of the diag_table to write.
    """

    def filename(stream):
        return '"{}.mom6.{}"'.format(CASENAME, stream.suffix)

    def quoted(value):
        """Renders one column: the value in quotes, and the separating comma."""
        return '"{}",'.format(value)

    # The streams are gone over twice, once to validate them and once to write
    # them out, so a one-shot iterable would yield a table with no files in it.
    assert isinstance(
        streams, (list, tuple)
    ), "write_diag_table needs a list of streams, not a one-shot iterable."

    for stream in streams:
        stream.validate()
    written = [stream for stream in streams if not stream.is_empty]

    # Width of the file name column, including the quotes and the comma. Only
    # the files that are actually written have a say in it.
    name_width = max((len(filename(stream)) for stream in written), default=0) + 4

    with open(output_path, "w") as diag_table:
        diag_table.write(
            '"MOM6 diagnostic fields table for CESM case: {}"\n'.format(CASENAME)
        )
        diag_table.write("1 1 1 0 0 0\n")  # TODO
        diag_table.write("### Section-1: File List\n")
        diag_table.write("#========================\n")
        for stream in written:
            settings = stream.settings
            entry = '{fname:{width}s} {output_freq:3s} {output_freq_units:9s} 1, {time_axis_units:9s} "time"'.format(
                width=name_width,
                fname=filename(stream) + ",",
                output_freq="{},".format(settings["output_freq"]),
                output_freq_units='"{}",'.format(settings["output_freq_units"]),
                time_axis_units='"{}",'.format(settings["time_axis_units"]),
            )
            if settings.get("new_file_freq") is not None:
                entry += ', {}, "{}"'.format(
                    settings["new_file_freq"], settings["new_file_freq_units"]
                )
            diag_table.write(entry + "\n")
        diag_table.write("\n")

        diag_table.write("### Section-2: Fields List\n")
        diag_table.write("#=========================\n")
        for stream in written:
            settings = stream.settings
            fname = filename(stream)
            diag_table.write("# {}\n".format(fname))
            for group in stream.groups:
                if not group.fields:
                    continue
                # Width of the two field name columns.
                field_width = min(
                    16, max(len(field.spec) for field in group.fields) + 3
                )
                for field in group.fields:
                    diag_table.write(
                        "{module} {name:{width}}{output_name:{width}}{fname}, "
                        '"all", {reduction} {regional_section} {packing}\n'.format(
                            module=quoted(group.module),
                            name=quoted(field.name),
                            output_name=quoted(field.output_name),
                            width=field_width,
                            fname=fname,
                            reduction=quoted(
                                field.reduction or settings["reduction_method"]
                            ),
                            regional_section=quoted(settings["regional_section"]),
                            packing=settings["packing"],
                        )
                    )
            diag_table.write("\n")
