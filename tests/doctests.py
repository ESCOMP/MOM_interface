#!/usr/bin/env python

import os, sys
import unittest
from doctest import testmod 

sys.path.append(os.path.join("cime_config","MOM_RPS"))
sys.path.append(os.path.join("../","cime_config","MOM_RPS"))

import rps_utils

if __name__ == '__main__': 
    testmod(rps_utils, verbose=True)
