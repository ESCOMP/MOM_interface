#!/bin/bash -e
### For NCAR machines, this script should be run as
### $ qcmd -- ./build_examples.sh

# Save various paths to use as shortcuts
cd ..
INTERFACE_ROOT=`pwd -P`
MKMF_ROOT=${INTERFACE_ROOT}/scripts_for_MOM6-examples/mkmf
TEMPLATE_DIR=${INTERFACE_ROOT}/scripts_for_MOM6-examples/templates
MOM_ROOT=${INTERFACE_ROOT}/MOM6
cd ../..
CESM_ROOT=`pwd -P`
FMS_ROOT=${CESM_ROOT}/libraries/FMS
SHR_ROOT=${CESM_ROOT}/components/cdeps/share

# 1) Build FMS

#    (b) build FMS
cd ${INTERFACE_ROOT}/MOM6-examples
mkdir -p build/intel/shared/repro
cd build/intel/shared/repro
${MKMF_ROOT}/list_paths ${FMS_ROOT}/src
${MKMF_ROOT}/mkmf -t ${TEMPLATE_DIR}/cheyenne-intel.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF -DSPMD" path_names
make NETCDF=3 REPRO=1 libfms.a -j

# 2) Build MOM6
cd ${INTERFACE_ROOT}/MOM6-examples
mkdir -p build/intel/ocean_only/repro
cd build/intel/ocean_only/repro
${MKMF_ROOT}/list_paths -l ${MOM_ROOT}/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external,src/{*,*/*}}/
${MKMF_ROOT}/mkmf -t ${TEMPLATE_DIR}/cheyenne-intel.mk -o '-I../../shared/repro' -p MOM6 -l '-L../../shared/repro -lfms' -c '-Duse_libMPI -Duse_netCDF -DSPMD' path_names
make NETCDF=3 REPRO=1 MOM6 -j
