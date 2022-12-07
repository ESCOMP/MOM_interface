#!/bin/bash -e
### For NCAR machines, this script should be run as
### $ qcmd -- ./build_examples.sh

# Save various paths to use as shortcuts
cd ../..
INTERFACE_ROOT=`pwd -P`
MKMF_ROOT=${INTERFACE_ROOT}/standalone/mkmf
TEMPLATE_DIR=${INTERFACE_ROOT}/standalone/templates
MOM_ROOT=${INTERFACE_ROOT}/MOM6
cd ../..
CESM_ROOT=`pwd -P`
FMS_ROOT=${CESM_ROOT}/libraries/FMS
SHR_ROOT=${CESM_ROOT}/components/cdeps/share

COMPILER=intel

# 1) Build FMS

#    (b) build FMS
cd ${INTERFACE_ROOT}/standalone/build
mkdir -p ${COMPILER}/FMS
cd ${COMPILER}/FMS
${MKMF_ROOT}/list_paths ${FMS_ROOT}/src
${MKMF_ROOT}/mkmf -t ${TEMPLATE_DIR}/cheyenne-${COMPILER}.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF -DSPMD" path_names
make -j36 NETCDF=3 REPRO=1 libfms.a

# 2) Build MOM6
cd ${INTERFACE_ROOT}/standalone/build
mkdir -p ${COMPILER}/MOM6
cd ${COMPILER}/MOM6
${MKMF_ROOT}/list_paths -l ${MOM_ROOT}/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external,src/{*,*/*}}/
${MKMF_ROOT}/mkmf -t ${TEMPLATE_DIR}/cheyenne-${COMPILER}.mk -o '-I../FMS' -p MOM6 -l '-L../FMS -lfms' -c '-Duse_libMPI -Duse_netCDF -DSPMD' path_names
make -j36 NETCDF=3 REPRO=1 MOM6
