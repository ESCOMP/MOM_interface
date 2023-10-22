#!/usr/bin/env python3

import os
import xarray as xr
import numpy as np

"""MOM6 land block elimination preprocessor module
"""

def MOM_define_layout(isz, jsz, ndivs):
    """ This function is a Python implementation of MOM_define_layout subroutine from 
    MOM_domains.F90, and is used here for guiding the land block elimination functions.
    Given a global array size (isz x jsz) and a number of (logical) processors (ndivs)
    , provide a layout of the processors in the two directions where the total number
    of processors is the product of the two layouts and number of points in the 
    partitioned arrays are as close as possible to an aspect ratio of 1. """

    # First try to divide ndivs to match the domain aspect ratio.  If this is not an even
    # divisor of ndivs, reduce idiv until a factor is found.
    idiv = max(np.rint(np.sqrt( (ndivs*isz)/jsz) ), 1)
    while ndivs%idiv != 0:
        idiv -= 1
    jdiv = ndivs // idiv

    return int(idiv), int(jdiv) 

def mpp_compute_extent(isg, ieg, ndivs):
    """ This function is a Python implementation of mpp_compute_extent from FMS 
    mpp_domains_define.inc and is used by builnml for generating mask tables for
    land block elimination.
    Computes extents for a grid decomposition with the given indices and divisions"""

    def even(x):
        assert isinstance(x,int)
        return x%2==0
    def odd(x):
        return not even(x)
    
    ibegin = [None for i in range(ndivs)]
    iend = [None for i in range(ndivs)]
    
    is_ = isg

    symmetrize = ( even(ndivs) and even(ieg-isg+1) ) or \
        ( odd(ndivs) and odd(ieg-isg+1) ) or \
        ( odd(ndivs) and even(ieg-isg+1) and ndivs<(ieg-isg+1)/2 )
        
    imax = ieg
    ndmax = ndivs
    
    for ndiv in range(ndivs):

        # do bottom half of decomposition, going over the midpoint for odd ndivs
        if ndiv<(ndivs-1)//2+1:
            ie = is_ + int(np.ceil( (imax-is_+1)/(ndmax-ndiv) )) - 1
            ndmirror = (ndivs-1) - ndiv # mirror domain
            if ndmirror > ndiv and symmetrize:
                # mirror extents, the max(,) is to eliminate overlaps
                ibegin[ndmirror] = max(isg+ieg-ie, ie+1)
                iend[ndmirror] = max(isg+ieg-is_, ie+1)
                imax = ibegin[ndmirror] - 1
                ndmax -= 1
        else:
            if symmetrize:
                # do top half of decomposition by retrieving saved values
                is_ = ibegin[ndiv]
                ie = iend[ndiv]
            else:
                ie = is_ + int(np.ceil( (imax-is_+1)/(ndmax-ndiv) )) - 1
        
        ibegin[ndiv] = is_
        iend[ndiv] = ie
        
        assert ie>=is_, "domain extents must be positive definite.'"
        assert not(ndiv==ndivs-1 and iend[ndiv]!=ieg), "domain extents do not span space completely"
        
        is_ = ie+1

    assert None not in ibegin, "Error in mpp_compute_extent"
    assert None not in iend, "Error in mpp_compute_extent"
    return ibegin, iend

def find_land_blocks(da_mask, idiv, jdiv, nihalo=4, njhalo=4):
    ''' Given a mask data array (da_mask), number of partitions in x and y dir (idiv, jdiv, and 
    halo widths, finds the list of blocks (partitions) that are all land cells.)'''
    
    ny, nx = da_mask.shape
    
    ibegin, iend = mpp_compute_extent(1,nx,idiv)
    jbegin, jend = mpp_compute_extent(1,ny,jdiv)
    
    masktable = []
    
    for i in range(idiv):
        i0,i1 = ibegin[i], iend[i]
        i0,i1 = max(i0-nihalo,0),min(i1+nihalo, nx)
        for j in range(jdiv):
            j0,j1 = jbegin[j], jend[j]
            j0,j1 = max(j0-njhalo,0),min(j1+njhalo, ny)
            
            if (da_mask.data[j0:j1, i0:i1] == 1.0).any():
                continue
            masktable.append((i+1,j+1))
    
    return masktable


def gen_mask_table(topo_file_path, ntasks_ocn, rundir):
    
    ds_topog = xr.open_dataset(topo_file_path)
    da_mask = ds_topog.mask 
    ocn_ny, ocn_nx = da_mask.shape

    # percentage of ocean cells:
    ro = (da_mask.sum() / da_mask.size).item()

    # best possible number of new ntasks_ocn
    ntasks_ocn_optimistic = int(ntasks_ocn/ro)

    for p in range(ntasks_ocn_optimistic, ntasks_ocn, -1):
        idiv, jdiv = MOM_define_layout(ocn_nx, ocn_ny, p)

        try:
            mt = find_land_blocks(ds_topog.mask, idiv, jdiv)
        except AssertionError:
            mt = []
        if p - len(mt) <= ntasks_ocn:
            print('DONE:',p, len(mt), p-ntasks_ocn)
            break
    
    # make sure that exactly ntasks_ocn tasks are active:
    len_mt = p - ntasks_ocn

    with open(os.path.join(rundir, 'MOM_auto_mask_table'), 'w') as f:
        f.write(f'{len_mt}\n')          # nmask
        f.write(f'{idiv},{jdiv}\n')    # layout
        # mask list
        for block in mt[:len_mt]:
            f.write(f'{block[0]},{block[1]}\n')

    return idiv, jdiv
