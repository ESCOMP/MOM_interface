"""
Implementation of the CIME MOM6 DIMCSL (Dimensional Consistency Lite) test.

This is a MOM6 specific test:
Implements rescaling test to check dimensional consistency.
(1) do a run with no scaling
(2) do a series of runs, each with different scale factors: 
    T: Time
    L: Horizontal length
    H: Layer thickness
    Z: Vertical length
    R: Density
    Q: Enthalpy
"""

from CIME.SystemTests.system_tests_compare_n import SystemTestsCompareN
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.test_utils.user_nl_utils import append_to_user_nl_files

logger = logging.getLogger(__name__)

nl_contents = [
    "!!! base run",
    "T_RESCALE_POWER = 11",
    "L_RESCALE_POWER = 11",
    "H_RESCALE_POWER = 11",
    "Z_RESCALE_POWER = 11",
    "R_RESCALE_POWER = 11",
    "Q_RESCALE_POWER = 11",
    ]

run_suffixes = [
    "base",
    "dimscale_1_Tp",
    "dimscale_2_Lp",
    "dimscale_3_Hp",
    "dimscale_4_Zp",
    "dimscale_5_Rp",
    "dimscale_6_Qp",
]

run_descriptions = [
    "base run with no namelist changes",
    "scale the dimension T by 2**11",
    "scale the dimension L by 2**11",
    "scale the dimension H by 2**11",
    "scale the dimension Z by 2**11",
    "scale the dimension R by 2**11",
    "scale the dimension Q by 2**11",
]

class DIMCSL(SystemTestsCompareN):

    def __init__(self, case):
        self.comp = case.get_value("COMP_OCN")
        SystemTestsCompareN.__init__(self, case, N=len(nl_contents),
                                     separate_builds = False,
                                     run_suffixes = run_suffixes,
                                     run_descriptions = run_descriptions,
                                     ignore_fieldlist_diffs = True)

    def _common_setup(self):
        nl_contents_common = '''
            ! DIMCSL test changes
        '''
        append_to_user_nl_files(caseroot = self._case.get_value("CASEROOT"),
                                component = self.comp,
                                contents = nl_contents_common)

    def _case_setup(self, i):

        # Second append user_nl change sepecific to case-i
        append_to_user_nl_files(caseroot = self._case.get_value("CASEROOT"),
                                component = self.comp,
                                contents = nl_contents[i])