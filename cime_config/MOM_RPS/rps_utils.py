""" Utilities for MOM_RPS module"""

from __future__ import print_function
from collections import OrderedDict
import os
import re


def is_number(val):
    """
    Alternative to isnumeric(), which can't handle scientific notation
    >>> is_number("1e-6") and is_number(1) and is_number(3.14)
    True
    >>> is_number([1,2]) or is_number("hello")
    False
    """
    try:
        float(val)
    except ValueError:
        return False
    except TypeError:
        return False
    return True

def get_str_type():
    try: # Python 2
        str_type = basestring
    except NameError: # Python 3
        str_type = str
    return str_type

def is_logical_expr(string):
    """
    Returns true if a string is a logical expression.

    >>> is_logical_expr("0 > 1000")
    True
    """

    evaluated_val = None
    if string.strip() == "else":
        evaluated_val = True
    else:
        try:
            evaluated_val = eval(string)
        except (NameError):
            pass # not a string to evaluate.
    return type(evaluated_val) == type(True)

def has_expandable_var(entry):
    """
    Checks if a given entry of type string has an expandable variable

    >>> has_expandable_var("${OCN_GRID} == tx0.66v1")
    True
    """
    if isinstance(entry,get_str_type()) and "$" in entry:
        return True
    else:
        return False


def _check_comparison_types(formula):
    """
    A check to prevent the comparison of different data types. This function
    replaces equality comparisons with order comparisons to check whether
    any variables of different types are compared. From Python 3.6 documentation:
    A default order comparison (<, >, <=, and >=) is not provided; an attempt
    raises TypeError. A motivation for this default behavior is the lack of a
    similar invariant as for equality.

    >>> _check_comparison_types("3.1 > 3")
    True
    >>> _check_comparison_types("'3.1' == 3.1")
    Traceback (most recent call last):
    ...
    TypeError: The following formula may be comparing different types of variables: '3.1' == 3.1
    """

    guard_test = formula.replace('==', '>').replace('!=', '>').replace('<>', '>')
    try:
        eval(guard_test)
    except TypeError:
        raise TypeError("The following formula may be comparing different types of variables: "+formula)
    return True

def eval_formula(formula):
    """
    This function evaluates a given formula and returns the result. It also
    carries out sanity checks before evaluation.

    >>> eval_formula("3*5")
    15
    >>> eval_formula("'tx0.66v1' != 'gx1v6'")
    True
    >>> eval_formula('$OCN_GRiD != "gx1v6"')
    Traceback (most recent call last):
    ...
    AssertionError
    """

    # make sure no expandable var exists in the formula. (They must already
    # be expanded before this function is called.)
    assert not has_expandable_var(formula)

    # Check whether any different data types are being compared
    _check_comparison_types(formula)

    # now try to evaluate the formula:
    try:
        result = eval(formula)
    except:
        raise RuntimeError("Cannot evaluate formula: "+formula)

    return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()
