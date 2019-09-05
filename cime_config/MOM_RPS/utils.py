""" Utilities for MOM_RPS module"""

from __future__ import print_function
from collections import OrderedDict
import os
import re


def is_number(val):
    """ alternative to isnumeric(), which can't handle scientific notation"""
    try:
        float(val)
    except ValueError:
        return False
    return True

def get_str_type():
    try: # Python 2
        str_type = basestring
    except NameError: # Python 3
        str_type = str
    return str_type

def is_logical_expr(string):
    """ returns true if a string is a logical expression """
    logical_keywords = [' and ',' or ', ' not ', '==', '=', '>', '<', 'true', 'false']
    return len([key for key in logical_keywords if key in string.lower()])>0

def has_param_to_expand(entry):
    """ Checks if a given entry of type string has cime parameter to expand"""
    assert type(entry)!=OrderedDict
    if isinstance(entry,get_str_type()) and "$" in entry:
        return True
    else:
        return False

def expand_cime_parameter(entry, case):
    """ Returns the version of an entry where cime parameters are expanded"""

    assert has_param_to_expand(entry)
    str_type = get_str_type()

    entry_is_logical_str = isinstance(entry,str_type) and is_logical_expr(entry)

    # first, infer ${*}
    cime_params = re.findall(r'\$\{.+?\}',entry)
    for cime_param in cime_params:
        cime_param_strip = cime_param.replace("${","").replace("}","")
        cime_param_expanded = case.get_value(cime_param_strip)
        if cime_param_expanded==None:
            raise RuntimeError("The guard "+cime_param_strip+" is not a CIME xml"
                               " variable for this case")
        if isinstance(cime_param_expanded,str_type) and entry_is_logical_str:
            cime_param_expanded = '"'+cime_param_expanded+'"'
        entry = entry.replace(cime_param,cime_param_expanded)

    # now infer $*
    for word in entry.split():
        if word[0] == '$':
            cime_param = word[1:]
            cime_param_expanded = case.get_value(cime_param)
            if cime_param_expanded==None:
                raise RuntimeError("The guard "+cime_param+" is not a CIME xml"
                                   " variable for this case")
            if isinstance(cime_param_expanded,str_type) and entry_is_logical_str:
                cime_param_expanded = '"'+cime_param_expanded+'"'
            entry = entry.replace(word,str(cime_param_expanded))

    return entry

