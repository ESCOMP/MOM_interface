#!/bin/bash -e
#PBS -N all_examples
#PBS -A P93300612
#PBS -l select=1:ncpus=36:mpiprocs=36
#PBS -l walltime=0:30:00
#PBS -q regular
#PBS -j oe
#PBS -k eod
#PBS -m abe

# run with
#
# $ qsub ./run_all.sh
#
# Takes ~3 minutes

EXAMPLES_ROOT=${PWD}
MOM6_EXE=${EXAMPLES_ROOT}/../build/intel/MOM6/MOM6

if [ ! -f ${MOM6_EXE} ]; then
  echo "You need to build MOM6 before running this script."
  echo "To build on cheyenne, run the following:"
  echo ""
  echo "$ cd ../build"
  echo "$ qcmd -- ./build_examples"
  exit 1
fi

for testdir in adjustment2d/layer       \
               adjustment2d/rho         \
               adjustment2d/z           \
               benchmark                \
               buoy_forced_basin        \
               circle_obcs              \
               CVmix_SCM_tests/cooling_only/BML       \
               CVmix_SCM_tests/cooling_only/EPBL      \
               CVmix_SCM_tests/cooling_only/KPP       \
               CVmix_SCM_tests/mech_only/BML          \
               CVmix_SCM_tests/mech_only/EPBL         \
               CVmix_SCM_tests/mech_only/KPP          \
               CVmix_SCM_tests/skin_warming_wind/BML  \
               CVmix_SCM_tests/skin_warming_wind/EPBL \
               CVmix_SCM_tests/skin_warming_wind/KPP  \
               CVmix_SCM_tests/wind_only/BML          \
               CVmix_SCM_tests/wind_only/EPBL         \
               CVmix_SCM_tests/wind_only/KPP          \
               DOME                     \
               double_gyre              \
               external_gwave           \
               flow_downslope/layer     \
               flow_downslope/rho       \
               flow_downslope/z         \
               idealized_hurricane      \
               lock_exchange            \
               mixed_layer_restrat_2d   \
               Phillips_2layer          \
               resting/layer            \
               resting/z                \
               SCM_idealized_hurricane  \
               seamount/layer           \
               seamount/rho             \
               seamount/sigma           \
               seamount/z               \
               single_column/BML        \
               single_column/EPBL       \
               single_column/KPP        \
               sloshing/layer           \
               sloshing/rho             \
               sloshing/z               \
               torus_advection_test     \
               tracer_mixing/rho        \
               tracer_mixing/z          \
               unit_tests
do
  cd ${EXAMPLES_ROOT}/${testdir}
  echo ""
  echo "--------------"
  echo "| ${testdir} |"
  echo "--------------"
  echo ""

  mkdir -p RESTART
  NP="-np 1"
  if [ "${testdir}" == "benchmark" ]; then
    NP=""
  elif [ "${testdir}" == "buoy_forced_basin" ]; then
    NP=""
  elif [ "${testdir}" == "DOME" ]; then
    NP=""
  elif [ "${testdir}" == "idealized_hurricane" ]; then
    NP=""
  fi
  mpiexec_mpt ${NP} dplace -s 1 ${MOM6_EXE}
done

