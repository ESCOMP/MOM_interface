#!/usr/bin/env python3

import os
import xarray as xr
import numpy as np
import argparse
from utils import MOM_define_layout, mpp_compute_extent

descr = """
MOM6 land block elimination preprocessor module
NOTE: this preprocessing module is no longer needed in practice (see AUTO_MASKTABLE option),
      but kept in MOM_interface for prototyping and diagnostics purposes. Must have the
      numpy and xarray packages installed.
"""


def determine_land_blocks(mask, nx, ny, idiv, jdiv, ibuf, jbuf):
    """Given a mask array, number of partitions in x and y dir (idiv, jdiv, and
    buffer widths, finds the list of blocks (partitions) that are all land cells.)

    Parameters:
    mask: 2D numpy array
        Mask array with 1s for land cells and 0s for ocean cells.
    nx: int
        Number of cells in x direction.
    ny: int
        Number of cells in y direction.
    idiv: int
        Number of partitions in x direction.
    jdiv: int
        Number of partitions in y direction.
    ibuf: int
        Buffer width in x direction.
    jbuf: int
        Buffer width in y direction.

    Returns:
    --------
    masktable: list of tuples
        List of tuples containing the indices of the blocks that are all land cells.
    """

    # 1-based begin and end indices
    ibegin, iend = mpp_compute_extent(1, nx, idiv)
    jbegin, jend = mpp_compute_extent(1, ny, jdiv)

    masktable = []

    for i in range(idiv):
        # NOTE: convert begin indices to zero-based indexing
        # (no need to convert end indices due to the way slicing works in Python)
        ib = ibegin[i] - 1
        ie = iend[i] + 2 * ibuf
        for j in range(jdiv):
            jb = jbegin[j] - 1
            je = jend[j] + 2 * jbuf

            if (mask[jb:je, ib:ie] == 1.0).any():
                continue
            masktable.append((i + 1, j + 1))

    return masktable


def gen_auto_mask_table(
    topo_file_path, npes, reentrant_x, reentrant_y, tripolar_n, output_dir
):
    """Generates the auto mask table for MOM6 based on the topography file and the number of PEs.

    Parameters:
    -----------
    topo_file_path: str
        Path to the topography file.
    npes: int
        Number of PEs.
    reentrant_x: bool
        Is the domain reentrant in x-dir?
    reentrant_y: bool
        Is the domain reentrant in y-dir?
    tripolar_n: bool
        Is the domain tripolar?
    output_dir: str
        Output directory to write the mask table.
    """

    ds_topog = xr.open_dataset(topo_file_path)
    ny, nx = ds_topog.mask.shape

    ibuf = 2
    jbuf = 2
    num_masked_blocks = 0

    mask = np.zeros((ny + 2 * jbuf, nx + 2 * ibuf))

    mask[jbuf : ny + jbuf, ibuf : nx + ibuf] = ds_topog.mask.data

    # fill in buffer cells
    if reentrant_x:
        mask[:, :ibuf] = mask[:, nx : nx + ibuf]
        mask[:, ibuf + nx :] = mask[:, ibuf : 2 * ibuf]

    if reentrant_y:
        mask[:jbuf, :] = mask[ny : ny + jbuf, :]
        mask[jbuf + ny :, :] = mask[jbuf : 2 * jbuf, :]

    if tripolar_n:
        for j in range(jbuf):
            for i in range(nx + 2 * ibuf):
                mask[jbuf + ny + j, i] = mask[jbuf + ny - 1 - j, nx + 2 * ibuf - 1 - i]

    # Tripolar Stitch Fix: In cases where masking is asymmetrical across the tripolar stitch, there's a possibility
    # that certain unmasked blocks won't be able to obtain grid metrics from the halo points. This occurs when the
    # neighboring block on the opposite side of the tripolar stitch is masked. As a consequence, certain metrics like
    # dxT and dyT may be calculated through extrapolation (refer to extrapolate_metric), potentially leading to the
    # generation of non-positive values. This can result in divide-by-zero errors elsewhere, e.g., in MOM_hor_visc.F90.
    # Currently, the safest and most general solution is to prohibit masking along the tripolar stitch:
    if tripolar_n:
        mask[jbuf + ny - 1, :] = 1

    # aspect ratio limit (>1) for a layout to be considered
    r_extreme = 4.0

    # ratio of ocean cells to total number of cells
    glob_ocn_frac = mask[jbuf : ny + jbuf, ibuf : nx + ibuf].sum() / (ny * nx)

    # Iteratively check for all possible division counts starting from the upper bound of npes/glob_ocn_frac,
    # which is over-optimistic for realistic domains, but may be satisfied with idealized domains.
    for p in range(int(np.ceil(npes / glob_ocn_frac)), npes, -1):

        # compute the layout for the current division count, p
        idiv, jdiv = MOM_define_layout(nx, ny, p)

        # don't bother checking this p if the aspect ratio is extreme
        r_p = (nx / idiv) / (ny / jdiv)
        if r_p * r_extreme < 1.0 or r_extreme < r_p:
            continue

        # Get the number of masked_blocks for this particular division count
        mask_table = determine_land_blocks(mask, nx, ny, idiv, jdiv, ibuf, jbuf)

        # If we can eliminate enough blocks to reach the target npes, adopt
        # this p (and the associated layout) and terminate the iteration.
        num_masked_blocks = len(mask_table)
        if p - num_masked_blocks <= npes:
            print("Found the optimum layout for auto-masking. Terminating iteration...")
            print(f"\t new ndivs: {p}, num_masked_blocks: {p-npes}")
            break

    if num_masked_blocks == 0:
        raise RuntimeError(
            "Couldn't auto-eliminate any land blocks. Try to increase the number"
        )

    # Call determine_land_blocks once again, this time to retrieve and write out the mask_table.
    mask_table = determine_land_blocks(mask, nx, ny, idiv, jdiv, ibuf, jbuf)
    write_auto_mask_file(mask_table, idiv, jdiv, npes, output_dir)


def write_auto_mask_file(
    mask_table, idiv, jdiv, npes, output_dir, filename="MOM_auto_mask_table"
):
    """Writes the auto mask table to a file.

    Parameters:
    -----------
    mask_table: list of tuples
        List of tuples containing the indices of the blocks that are all land cells.
    idiv: int
        Number of partitions in x direction.
    jdiv: int
        Number of partitions in y direction.
    npes: int
        Number of PEs.
    output_dir: str
        Output directory to write the mask table.
    filename: str
        Name of the mask table file.
    """
    # make sure that exactly npes tasks are active:
    true_num_masked_blocks = idiv * jdiv - npes

    mask_file_path = os.path.join(output_dir, filename)
    with open(mask_file_path, "w") as f:
        f.write(f"{true_num_masked_blocks}\n")  # nmask
        f.write(f"{idiv},{jdiv}\n")  # layout
        # mask list
        for block in mask_table[:true_num_masked_blocks]:
            f.write(f"{block[0]},{block[1]}\n")

    print(f"\t mask_table written to: {mask_file_path}")

    return idiv, jdiv


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument(
        "-t",
        metavar="topofile",
        type=str,
        required=True,
        help="MOM6 topography file path (TOPO_FILE)",
    )
    parser.add_argument(
        "-n",
        metavar="npes",
        type=int,
        required=True,
        help="Number of MOM6 PEs (NTASKS_OCN)",
    )
    parser.add_argument(
        "-rx",
        default=False,
        action="store_true",
        help="Is the domain reentrant in x-dir?",
    )
    parser.add_argument(
        "-ry",
        default=False,
        action="store_true",
        help="Is the domain reentrant in y-dir?",
    )
    parser.add_argument(
        "-tn", default=False, action="store_true", help="Is the domain tripolar?"
    )
    parser.add_argument(
        "-o", metavar="output_dir", type=str, required=False, help="Output directory"
    )
    args = parser.parse_args()

    output_dir = args.o or os.getcwd()
    gen_auto_mask_table(args.t, args.n, args.rx, args.ry, args.tn, output_dir)
