#!/bin/bash -e
### For NCAR machines, this script should be run as
### $ qcmd -- ./build_examples.sh

echo "Starting build at `date`"

# Save various paths to use as shortcuts
cd ../..
INTERFACE_ROOT=`pwd -P`
MKMF_ROOT=${INTERFACE_ROOT}/standalone/mkmf
TEMPLATE_DIR=${INTERFACE_ROOT}/standalone/templates
MOM_ROOT=${INTERFACE_ROOT}/MOM6
cd ../..
CESM_ROOT=`pwd -P`
SHR_ROOT=${CESM_ROOT}/share
FMS_ROOT=${CESM_ROOT}/libraries/FMS

# Default compiler
COMPILER="intel"
MACHINE="ncar"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --compiler) 
            COMPILER="$2"
            shift ;;
        --machine) 
            MACHINE="$2"
            shift ;;
        *) 
            echo "Unknown parameter passed: $1"
            echo "Usage: $0 [--compiler <compiler>] [--machine <machine>]"
            exit 1 ;;
    esac
    shift
done
echo "Using compiler: $COMPILER"
echo "Using machine: $MACHINE"

TEMPLATE=${TEMPLATE_DIR}/${MACHINE}-${COMPILER}.mk

# Throw error if template does not exist:
if [ ! -f $TEMPLATE ]; then
  echo "ERROR: Template file $TEMPLATE does not exist."
    echo "Templates are based on the machine and compiler arguments: machine-compiler.mk. Available templates are:"
    ls ${TEMPLATE_DIR}/*.mk
    echo "Exiting."
  exit 1
fi

# Set -j option based on the MACHINE argument
case $MACHINE in
    "homebrew" | "ubuntu")
        jNUM=2
        ;;
    "ncar")
        jNUM=36
        ;;
    *)
        echo "Invalid machine type for make -j option: $MACHINE"
        exit 1
        ;;
esac

if [ -e $1 ]; then
  BLD_ROOT=${COMPILER}
else
  BLD_ROOT=$1
fi

# 1) Build FMS
cd ${INTERFACE_ROOT}/standalone/build
mkdir -p ${BLD_ROOT}/FMS
cd ${BLD_ROOT}/FMS
${MKMF_ROOT}/list_paths ${FMS_ROOT}/src
# We need shr_const_mod.F90 and shr_kind_mod.F90 from ${SHR_ROOT}/src
# to build FMS
echo "${SHR_ROOT}/src/shr_kind_mod.F90" >> path_names
echo "${SHR_ROOT}/src/shr_const_mod.F90" >> path_names
${MKMF_ROOT}/mkmf -t ${TEMPLATE} -p libfms.a -c "-Duse_libMPI -Duse_netCDF -DSPMD" path_names
make -j${jNUM} NETCDF=3 REPRO=1 libfms.a

# 2) Build MOM6
cd ${INTERFACE_ROOT}/standalone/build
mkdir -p ${BLD_ROOT}/MOM6
cd ${BLD_ROOT}/MOM6
${MKMF_ROOT}/list_paths -l ${MOM_ROOT}/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,../externals/MARBL/src,config_src/external,src/{*,*/*}}/
${MKMF_ROOT}/mkmf -t ${TEMPLATE} -o '-I../FMS' -p MOM6 -l '-L../FMS -lfms' -c '-Duse_libMPI -Duse_netCDF -DSPMD' path_names
make -j${jNUM}  NETCDF=3 REPRO=1 MOM6

echo "Finished build at `date`"
