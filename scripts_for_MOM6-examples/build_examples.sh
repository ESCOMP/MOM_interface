#!/bin/bash -e
### For NCAR machines, this script should be run as
### $ qcmd -- ./build_examples.sh

cd ../MOM6-examples

# 1) Build FMS
mkdir -p build/intel/shared/repro
cd build/intel/shared/repro
../../../../../scripts_for_MOM6-examples/mkmf/list_paths ../../../../src/FMS2/
../../../../../scripts_for_MOM6-examples/mkmf/mkmf -t ../../../../../scripts_for_MOM6-examples/templates/cheyenne-intel.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF -DSPMD" path_names
make NETCDF=3 REPRO=1 libfms.a -j
cd ../../../..

# 2) Build MOM6
mkdir -p build/intel/ocean_only/repro
cd build/intel/ocean_only/repro
../../../../../scripts_for_MOM6-examples/mkmf/list_paths -l ./ ../../../../../MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external,src/{*,*/*}}/
../../../../../scripts_for_MOM6-examples/mkmf/mkmf -t ../../../../../scripts_for_MOM6-examples/templates/cheyenne-intel.mk -o '-I../../shared/repro' -p MOM6 -l '-L../../shared/repro -lfms' -c '-Duse_libMPI -Duse_netCDF -DSPMD' path_names
make NETCDF=3 REPRO=1 MOM6 -j
cd ../../../..

