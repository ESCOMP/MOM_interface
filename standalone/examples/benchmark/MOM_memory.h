!********+*********+*********+*********+*********+*********+*********+*
!*   This include file determines the compile-time settings for the   *
!* benchmark configuration of the Modular Ocean Model (MOM),          *
!* versions 6 and later.                                              *
!********+*********+*********+*********+*********+*********+*********+*

!  Specify the numerical domain.
#define NIGLOBAL_ 360
#define NJGLOBAL_ 180
                               !    NIGLOBAL_ and NJGLOBAL_ are the number of thickness
                               !  grid points in the zonal and meridional
                               !  directions of the physical domain.
#define NK_ 22
                               !    The number of layers.

#undef  STATIC_MEMORY_
                               !    If STATIC_MEMORY_ is defined, the principle
                               !  variables will have sizes that are statically
                               !  determined at compile time.  Otherwise the
                               !  sizes are not determined until run time. The
                               !  STATIC option is substantially faster, but
                               !  does not allow the PE count to be changed at
                               !  run time.
#define SYMMETRIC_MEMORY_
                               !    If defined, the velocity point data domain
                               !  includes every face of the thickness points.
                               !  In other words, some arrays are larger than
                               !  others, depending on where they are on the 
                               !  staggered grid.

# define NIPROC_ 12
                               !    NIPROC_ is the number of processors in the
                               !  x-direction.
# define NJPROC_ 6
                               !    NJPROC_ is the number of processors in the
                               !  y-direction.

#define MAX_FIELDS_ 100
                               !    The maximum permitted number (each) of
                               !  restart variables, time derivatives, etc.
                               !  This is mostly used for the size of pointer
                               !  arrays, so it should be set generously.

#define NIHALO_ 4
#define NJHALO_ 4
                               !   NIHALO_ and NJHALO_ are the sizes of the
                               ! memory halos on each side.

#include <MOM_memory_macros.h>
