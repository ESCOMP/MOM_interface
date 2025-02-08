# check that the MOM6 submodule commit is the same as what's specificed in .gitmodules:

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
        fxtag = None
        url = None
        in_MOM6_block = False
        for line in f:
            line = line.strip('[ ]\n').split()
            if not line:
                continue # skip empty lines
            if len(line) == 2 and line[0] == "submodule":
                in_MOM6_block = line[1] == '"MOM6"'
            if in_MOM6_block:
                if line[0] == "fxtag":
                    fxtag = line[2]
                elif line[0] == "url":
                    url = line[2]
    
    # get commit hash corresponding to fxtag
    if fxtag is None:
        raise Exception("Could not get MOM6 commit from .gitmodules")
    elif url is None:
        raise Exception("Could not get MOM6 url from .gitmodules")

    # check if fxtag is a commit hash and not a tag
    if re.match(r"^[0-9a-f]{40}$", fxtag) or re.match(r"^[0-9a-f]{7}$", fxtag):
        return fxtag

    # get commit hash from tag
    p = subprocess.Popen(
        ["git", "ls-remote", url, fxtag],
        stdout=subprocess.PIPE,
    )
    out, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("Could not get MOM6 commit from .gitmodules")
    return out.decode().split()[0][:40] # first 40 characters are the commit hash
    

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
    if mom6_commit[:7] != mom6_submodule_commit[:7]:
        print("ERROR: MOM6 commit in .gitmodules does not match the commit in src/MOM6")
        print("MOM6 commit in .gitmodules: {}".format(mom6_commit))
        print("MOM6 commit in src/MOM6: {}".format(mom6_submodule_commit))
        sys.exit(1)


if __name__ == "__main__":
    main()
