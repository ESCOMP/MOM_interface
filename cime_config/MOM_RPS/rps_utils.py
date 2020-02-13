"""Auxiliary functions to be used in MOM_RPS."""

from __future__ import print_function
from collections import OrderedDict
import os
import re

def is_number(var):
    """
    Returns True if the passed var (of type string) is a number. Returns
    False if var is not a string or if it is not a number.
    This function is an alternative to isnumeric(), which can't handle
    scientific notation.

    Parameters
    ----------
    var: str
        variable to check whether number or not

    Returns
    -------
    True or False

    >>> "1e-6".isnumeric()
    False
    >>> is_number("1e-6") and is_number(1) and is_number(3.14)
    True
    >>> is_number([1,2]) or is_number("hello")
    False
    """
    try:
        float(var)
    except ValueError:
        return False
    except TypeError:
        return False
    return True

def get_str_type():
    """Returns the base string type, which depends on the major Python version."""

    try: # Python 2
        str_type = basestring
    except NameError: # Python 3
        str_type = str
    return str_type

def is_logical_expr(expr):
    """
    Returns True if a string is a logical expression.

    Parameters
    ----------
    expr: str
        expression to check whether logical or not

    Returns
    -------
    True or False

    >>> is_logical_expr("0 > 1000")
    True
    """

    evaluated_val = None
    if expr.strip() == "else":
        evaluated_val = True
    else:
        try:
            evaluated_val = eval(expr)
        except (NameError):
            pass # not an expr to evaluate.
    return type(evaluated_val) == type(True)

def is_formula(expr):
    """
    Returns True if expr is a MOM_RPS formula to evaluate. This is determined by
    checking whether expr is a string with a length of 1 or greater and if the
    first character of expr is '='.

    Parameters
    ----------
    expr: str
        expression to check whether formula or not

    Returns
    -------
    True or False

    >>> is_formula("3*5")
    False
    >>> is_formula("= 3*5")
    True
    """

    return (isinstance(expr, get_str_type()) and len(expr)>0 and expr[0]=='=')

def has_expandable_var(expr):
    """
    Checks if a given expression has an expandable variable, e.g., $OCN_GRID.

    Parameters
    ----------
    expr: str
        expression to check

    Returns
    -------
    True or False

    >>> has_expandable_var("${OCN_GRID} == tx0.66v1")
    True
    """

    if isinstance(expr,get_str_type()) and "$" in expr:
        return True
    else:
        return False


def _check_comparison_types(formula):
    """
    A check to detect the comparison of different data types. This function
    replaces equality comparisons with order comparisons to check whether
    any variables of different types are compared. From Python 3.6 documentation:
    A default order comparison (<, >, <=, and >=) is not provided; an attempt
    raises TypeError. A motivation for this default behavior is the lack of a
    similar invariant as for equality.

    Parameters
    ----------
    formula: str
        formula to check if it includes comparisons of different data types

    Returns
    -------
    True (or raises TypeError)

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
    carries out several sanity checks before evaluation.

    Parameters
    ----------
    formula: str
        formula to evaluate

    Returns
    -------
    eval(formula)

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
