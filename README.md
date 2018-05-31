# MOM_interface
CESM interface to MOM Ocean Model

------------
MOM6 is the provisional ocean component of CESM3, a future version of NCAR's global climate model. This repository is the CESM interface for MOM6. The repository provides CIME compatibility and is used within CESM framework to check out core MOM6 repository and other packages via manage_externals utility.

### Quick Start:

1. Check out CESM2+MOM6:

       git clone https://github.com/alperaltuntas/cesm.git cesm2.mom6
       cd cesm2.mom6
       git checkout mom6
       ./manage_externals/checkout_externals
       
2. Run CESM2+MOM6:
       
    *Create a new case*
   
       cd cime/scripts
       ./create_newcase --case cmom_test --compset CMOM --res T62_g16 --walltime 00:30
       
    *Set up, build, and run the case:*
   
       cd cmom_test
       ./case.setup
       ./case.build
       ./case.submit
