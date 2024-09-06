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
USE_CESM=""
DEBUG=0 # Set to False, or REPRO Mode!

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --compiler) 
            COMPILER="$2"
            shift ;;
        --machine) 
            MACHINE="$2"
            shift ;;
        --cesm) 
            USE_CESM="_cesm" ;;
        --debug)
            DEBUG=1 ;;
        *) 
            echo "Unknown parameter passed: $1"
            echo "Usage: $0 [--compiler <compiler>] [--machine <machine>]"
            exit 1 ;;
    esac
    shift
done
echo "Using compiler: $COMPILER"
echo "Using machine: $MACHINE"
echo "Using CESM: $USE_CESM"

TEMPLATE=${TEMPLATE_DIR}/${MACHINE}-${COMPILER}${USE_CESM}.mk

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
    "homebrew" )
        JOBS=2
        ;;
    "ubuntu" )
        JOBS=4
        ;;
    "ncar")
        JOBS=32
        ;;
    *)
        echo "Invalid machine type for make -j option: $MACHINE"
        exit 1
        ;;
esac

if [ "${DEBUG}" == 1 ]; then
  BLD_ROOT=${COMPILER}-debug
else
  BLD_ROOT=${COMPILER}
fi

if [ "${USE_CESM}" == "_cesm" ]; then
  BLD_ROOT=${BLD_ROOT}-cesm
fi


# Load modules for NCAR
if [ "$MACHINE" == "ncar" ]; then
  HOST=`hostname`
  # Load modules if on derecho
  if [ ! "${HOST:0:5}" == "crhtc" ] && [ ! "${HOST:0:6}" == "casper" ]; then
    module --force purge
    . /glade/u/apps/derecho/23.09/spack/opt/spack/lmod/8.7.24/gcc/7.5.0/c645/lmod/lmod/init/sh
    module load cesmdev/1.0 ncarenv/23.09
    case $COMPILER in
      "intel" )
        module load craype intel/2023.2.1 mkl ncarcompilers/1.0.0 cmake cray-mpich/8.1.27 netcdf-mpi/4.9.2 parallel-netcdf/1.12.3 parallelio/2.6.2 esmf/8.6.0
        ;;
      "gnu" )
        module load craype gcc/12.2.0 cray-libsci/23.02.1.1 ncarcompilers/1.0.0 cmake cray-mpich/8.1.27 netcdf-mpi/4.9.2 parallel-netcdf/1.12.3 parallelio/2.6.2-debug esmf/8.6.0-debug
        ;;
      "nvhpc" )
        module load craype nvhpc/24.3 ncarcompilers/1.0.0 cmake cray-mpich/8.1.27 netcdf-mpi/4.9.2 parallel-netcdf/1.12.3 parallelio/2.6.2 esmf/8.6.0
        ;;
      *)
        echo "Not loading any special modules for ${COMPILER}"
        ;;
    esac
  fi
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
make -j${JOBS} DEBUG=${DEBUG} libfms.a

# 2) Build MOM6
cd ${INTERFACE_ROOT}/standalone/build
mkdir -p ${BLD_ROOT}/MOM6
cd ${BLD_ROOT}/MOM6
${MKMF_ROOT}/list_paths -l ${MOM_ROOT}/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,../externals/MARBL/src,config_src/external,src/{*,*/*}}/
${MKMF_ROOT}/mkmf -t ${TEMPLATE} -o '-I../FMS' -p MOM6 -l '-L../FMS -lfms' -c '-Duse_libMPI -Duse_netCDF -DSPMD' path_names
make -j${JOBS} DEBUG=${DEBUG} MOM6

echo "Finished build at `date`"
