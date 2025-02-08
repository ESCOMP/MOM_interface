# check that the MOM6 submodule commit is the same as what's specificed in .gitmodules:

import os
import sys
import subprocess
import re
from pathlib import Path

# path to this file:
this_file = Path(__file__).resolve()
mom_interface_root = this_file.parent.parent


def get_mom6_gitmodules_commit():
    """Get the commit hash of the MOM6 submodule from .gitmodules"""

    with open(mom_interface_root / ".gitmodules") as f:
        for line in f:
            if "url = " in line:
                url = line.split("=")[-1].strip()
                break
    if not url:
        raise Exception("Could not find MOM6 url in .gitmodules")
    p = subprocess.Popen(["git", "ls-remote", url], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("Could not get MOM6 commit")
    return out.decode().split()[0]


def get_mom6_submodule_commit():
    """Get the commit hash of the MOM6 submodule from the src/MOM6 directory"""

    p = subprocess.Popen(
        ["git", "submodule", "status", mom_interface_root / "MOM6"],
        stdout=subprocess.PIPE,
    )
    out, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("Could not get MOM6 submodule commit")
    return out.decode().split()[0]


def main():
    """Check that the MOM6 submodule commit is the same as what's specificed in .gitmodules"""

    mom6_commit = get_mom6_gitmodules_commit()
    mom6_submodule_commit = get_mom6_submodule_commit()
    if mom6_commit != mom6_submodule_commit:
        print("ERROR: MOM6 commit in .gitmodules does not match the commit in src/MOM6")
        print("MOM6 commit in .gitmodules: {}".format(mom6_commit))
        print("MOM6 commit in src/MOM6: {}".format(mom6_submodule_commit))
        sys.exit(1)


if __name__ == "__main__":
    main()
