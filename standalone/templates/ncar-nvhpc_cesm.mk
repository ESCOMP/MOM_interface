# Template for the PGI Compilers

############
# commands #
############
FC = ftn
CC = cc
CXX = cc
LD = ftn $(MAIN_PROGRAM)

############
#  flags   #
############

DEBUG =

MAKEFLAGS += --jobs=8

INCLUDES := $(shell pkg-config --cflags yaml-0.1)

# Need to use at least GNU Make version 3.81
need := 3.81
ok := $(filter $(need),$(firstword $(sort $(MAKE_VERSION) $(need))))
ifneq ($(need),$(ok))
$(error Need at least make version $(need).  Load module gmake/3.81)
endif


# Check version of PGI for use of -nofma option
has_nofma := $(shell $(FC) -dryrun -nofma foo.f90 > /dev/null 2>&1; echo $$?)
ifneq ($(has_nofma),0)
NOFMA :=
else
NOFMA := -nofma
endif

# Required Preprocessor Macros:
CPPDEFS += -Duse_netCDF

# Additional Preprocessor Macros needed due to  Autotools and CMake
CPPDEFS += -DHAVE_SCHED_GETAFFINITY -DHAVE_GETTID

# Macro for Fortran preprocessor
FPPFLAGS := $(INCLUDES)


# Base set of Fortran compiler flags
FC_AUTO_R8 = -r8
FFLAGS = $(FC_AUTO_R8) -Mnofma -i4 -gopt  -time -Mextend -byteswapio -Mflushz -Kieee

# Flags based on perforance target (production (OPT), reproduction (REPRO), or debug (DEBUG)
FFLAGS_REPRO = -O -tp=zen3
FFLAGS_DEBUG = -O0 -g -Ktrap=fp -Mbounds -Kieee

# Macro for C preprocessor
CPPFLAGS := $(INCLUDES)


# Base set of C compiler flags
CFLAGS = -gopt -time -Mnofma

# Flags based on perforance target (production (OPT), reproduction (REPRO), or debug (DEBUG)
CFLAGS_REPRO = -O 
CFLAGS_DEBUG = -O0 -g -traceback -Ktrap=fp

# Linking flags
LDFLAGS := -byteswapio

# List of -L library directories to be added to the compile and linking commands
LIBS :=

# Get compile flags based on target macros.
ifeq ($(DEBUG),1)
CFLAGS += $(CFLAGS_DEBUG)
FFLAGS += $(FFLAGS_DEBUG)
else
CFLAGS += $(CFLAGS_REPRO)
FFLAGS += $(FFLAGS_REPRO)
endif


# NetCDF Flags
# Fortran Compiler flags for the NetCDF library
FPPFLAGS += $(shell nf-config --fflags)
# C Compiler flags for the NetCDF library
CPPFLAGS += $(shell nc-config --cflags)
  # add the use_LARGEFILE cppdef
  ifneq ($(findstring -Duse_netCDF,$(CPPDEFS)),)
    CPPDEFS += -Duse_LARGEFILE
  endif
  # Add netcdf linking
  LIBS += $(shell nc-config --libs) $(shell nf-config --flibs)

# Additional CPPDEFS Flags
CPPDEFS += -DCNL -DFORTRANUNDERSCORE -DNO_SHR_VMATH -DNO_R16  -DCPRPGI -DLINUX -DHAVE_GETTID  -DFORTRANUNDERSCORE -DNO_SHR_VMATH -DNO_R16  -DCPRPGI -DLINUX -DHAVE_GETTID -DNDEBUG -DUSE_ESMF_LIB -DHAVE_MPI -DNUOPC_INTERFACE -DPIO2 -DHAVE_SLASHPROC -D_PNETCDF -DESMF_VERSION_MAJOR=8 -DESMF_VERSION_MINOR=6 -DATM_PRESENT -DICE_PRESENT -DLND_PRESENT -DOCN_PRESENT -DROF_PRESENT -DGLC_PRESENT -DWAV_PRESENT -DESP_PRESENT -DMED_PRESENT


# These Algebra libraries Add solution to more complex vector matrix model equations
LIBS += -llapack -lblas
LDFLAGS += $(LIBS) -time -Wl,--allow-multiple-definition

#---------------------------------------------------------------------------
# you should never need to change any lines below.

# see the MIPSPro F90 manual for more details on some of the file extensions
# discussed here.
# this makefile template recognizes fortran sourcefiles with extensions
# .f, .f90, .F, .F90. Given a sourcefile <file>.<ext>, where <ext> is one of
# the above, this provides a number of default actions:

# make <file>.opt       create an optimization report
# make <file>.o         create an object file
# make <file>.s         create an assembly listing
# make <file>.x         create an executable file, assuming standalone
#                       source
# make <file>.i         create a preprocessed file (for .F)
# make <file>.i90       create a preprocessed file (for .F90)

# The macro TMPFILES is provided to slate files like the above for removal.

RM = rm -f
TMPFILES = .*.m *.B *.L *.i *.i90 *.l *.s *.mod *.opt

.SUFFIXES: .F .F90 .H .L .T .f .f90 .h .i .i90 .l .o .s .opt .x

.f.L:
	$(FC) $(FFLAGS) -c -listing $*.f
.f.opt:
	$(FC) $(FFLAGS) -c -opt_report_level max -opt_report_phase all -opt_report_file $*.opt $*.f
.f.l:
	$(FC) $(FFLAGS) -c $(LIST) $*.f
.f.T:
	$(FC) $(FFLAGS) -c -cif $*.f
.f.o:
	$(FC) $(FFLAGS) -c $*.f
.f.s:
	$(FC) $(FFLAGS) -S $*.f
.f.x:
	$(FC) $(FFLAGS) -o $*.x $*.f *.o $(LDFLAGS)
.f90.L:
	$(FC) $(FFLAGS) -c -listing $*.f90
.f90.opt:
	$(FC) $(FFLAGS) -c -opt_report_level max -opt_report_phase all -opt_report_file $*.opt $*.f90
.f90.l:
	$(FC) $(FFLAGS) -c $(LIST) $*.f90
.f90.T:
	$(FC) $(FFLAGS) -c -cif $*.f90
.f90.o:
	$(FC) $(FFLAGS) -c $*.f90
.f90.s:
	$(FC) $(FFLAGS) -c -S $*.f90
.f90.x:
	$(FC) $(FFLAGS) -o $*.x $*.f90 *.o $(LDFLAGS)
.F.L:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -listing $*.F
.F.opt:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -opt_report_level max -opt_report_phase all -opt_report_file $*.opt $*.F
.F.l:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c $(LIST) $*.F
.F.T:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -cif $*.F
.F.f:
	$(FC) $(CPPDEFS) $(FPPFLAGS) -EP $*.F > $*.f
.F.i:
	$(FC) $(CPPDEFS) $(FPPFLAGS) -P $*.F
.F.o:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c $*.F
.F.s:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -S $*.F
.F.x:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -o $*.x $*.F *.o $(LDFLAGS)
.F90.L:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -listing $*.F90
.F90.opt:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -opt_report_level max -opt_report_phase all -opt_report_file $*.opt $*.F90
.F90.l:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c $(LIST) $*.F90
.F90.T:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -cif $*.F90
.F90.f90:
	$(FC) $(CPPDEFS) $(FPPFLAGS) -EP $*.F90 > $*.f90
.F90.i90:
	$(FC) $(CPPDEFS) $(FPPFLAGS) -P $*.F90
.F90.o:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c $*.F90
.F90.s:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -c -S $*.F90
.F90.x:
	$(FC) $(CPPDEFS) $(FPPFLAGS) $(FFLAGS) -o $*.x $*.F90 *.o $(LDFLAGS)
