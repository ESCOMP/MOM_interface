"""
Implementation of the CIME MOM6 MEMCS (Memory Mode Consistency) test.

This is a MOM6 specific test. Comparison being made:
 - symm vs base: Checks whether changing the memory mode changes answers.
"""

from CIME.SystemTests.system_tests_compare_n import SystemTestsCompareN
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.test_utils.user_nl_utils import append_to_user_nl_files

logger = logging.getLogger(__name__)

class MEMCS(SystemTestsCompareN):

    def __init__(self, case):
        self.comp = case.get_value("COMP_OCN")
        SystemTestsCompareN.__init__(self, case, N=2,
                                     separate_builds = True,
                                     run_suffixes = ["base", "symm"],
                                     ignore_fieldlist_diffs = True)

    def _case_setup(self, i):

        if i==0:
            # this is the default case
            self._case.set_value("MOM6_MEMORY_MODE", "dynamic_nonsymmetric")
        elif i==1:
            with self._case as case:
                case.set_value("MOM6_MEMORY_MODE", "dynamic_symmetric")
