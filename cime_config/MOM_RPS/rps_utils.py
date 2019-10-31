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

    evaluated_val = None
    if string.strip() == "else":
        evaluated_val = True
    else:
        try:
            evaluated_val = eval(string)
        except (NameError):
            pass # not a string to evaluate.
    return type(evaluated_val) == type(True)
