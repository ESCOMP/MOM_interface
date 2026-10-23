#!/usr/bin/env python3
"""Runs the doctests of the modules in cime_config/MOM_RPS.

Modules that depend on CIME, i.e., the FType classes built on ParamGen, are
tested only if CIMEROOT is set, e.g.:
    CIMEROOT=/path/to/cime python tests/doctests.py
"""

import doctest
import importlib
import os
import sys

MOM_RPS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "cime_config", "MOM_RPS"
)
sys.path.append(MOM_RPS)
if os.environ.get("CIMEROOT"):
    sys.path.append(os.environ["CIMEROOT"])

failed = 0
for filename in sorted(os.listdir(MOM_RPS)):
    if not filename.endswith(".py"):
        continue
    name = filename[:-3]
    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError as error:
        if error.name.split(".")[0] != "CIME":
            raise
        print("{}: skipped, as it requires CIME (set CIMEROOT)".format(name))
        continue
    results = doctest.testmod(module)
    failed += results.failed
    print("{}: {} tests, {} failed".format(name, results.attempted, results.failed))

sys.exit(1 if failed else 0)
