#%% import and definitions
from typing import Tuple, Optional, Dict, List
import os
import warnings

import dask.array as darr
import numpy as np
from numpy import random

import sparse
import xarray as xr
from scipy.stats import multivariate_normal
from scipy.ndimage import gaussian_filter1d


def shift_perframe(fm: np.ndarray, sh: np.ndarray, fill=np.nan) -> np.ndarray:
    """
    Shifts all pixels in a frame by the specified amount.

    Args:
        fm: Input frame to be shifted.
        sh: Shifts for each dimension.
        fill: Value to fill in the places left vacant by the shift.

    Returns:
        fm: Shifted frame.
    """
    # If all values are NaN, return the original frame
    if np.isnan(fm).all():
        return fm
    
    # Round shifts to nearest integer
    sh = np.around(sh).astype(int)

    # Shift the frame
    fm = np.roll(fm, sh, axis=np.arange(fm.ndim))

    # Fill in the gaps left by the shift
    index = [slice(None) for _ in range(fm.ndim)]
    for ish, s in enumerate(sh):
        index = [slice(None) for _ in range(fm.ndim)]
        if s > 0:
            index[ish] = slice(None, s)
            fm[tuple(index)] = fill
        elif s == 0:
            continue
        elif s < 0:
            index[ish] = slice(s, None)
            fm[tuple(index)] = fill

    return fm


def gauss_cell(height: int, width: int, sz_mean: float, sz_sigma: float, sz_min: float, cent=None, norm=True) -> np.ndarray:
    """
    Generates a cell with a Gaussian distribution of pixel intensities.

    Parameters
    ----------
    height: int
        The height of the cell.
    width: int
        The width of the cell.
    sz_mean: float
        The mean size of the cell.
    sz_sigma: float
        The standard deviation of the cell size.
    sz_min: float
        The minimum size of the cell.
    cent: list, optional
        The centroid of the cell. If not specified, a random centroid will be generated.
    norm: bool, optional
        Whether or not to normalize the cell.

    Returns
    -------
    A: np.ndarray
        The generated Gaussian cell.
    """

    # Generate centroid if not provided
    if cent is None:
        cent = np.atleast_2d([random.randint(height), random.randint(width)])

    # Generate sizes (height and width) for the Gaussian cell using a normal distribution
    sz_h = np.clip(random.normal(loc=sz_mean, scale=sz_sigma, size=cent.shape[0]), sz_min, None)
    sz_w = np.clip(random.normal(loc=sz_mean, scale=sz_sigma, size=cent.shape[0]), sz_min, None)

    # Generate grid to be used for calculating Gaussian PDF
    grid = np.moveaxis(np.mgrid[:height, :width], 0, -1)
    A = np.zeros((cent.shape[0], height, width))

    # Calculate Gaussian PDF for each cell and assign it to the corresponding position in the array
    for idx, (c, hs, ws) in enumerate(zip(cent, sz_h, sz_w)):
        pdf = multivariate_normal.pdf(grid, mean=c, cov=np.array([[hs, 0], [0, ws]]))

        # Normalize the PDF if the 'norm' parameter is True
        if norm:
            pmin, pmax = pdf.min(), pdf.max()
            pdf = (pdf - pmin) / (pmax - pmin)

        A[idx] = pdf

    return A


def exp_trace(frame: int, pfire: float, tau_d: float, tau_r: float, trunc_thres: float = 1e-6) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates an exponential trace for a cell, simulating the calcium indicator dynamics modulated by a Poisson spike train.

    Parameters
    ----------
    frame : int
        Total number of frames (i.e., time points) in the trace.
    pfire : float
        Probability of a cell firing at each frame, used to generate the Poisson spike train.
    tau_d : float
        Decay constant for the exponential trace, representing the decay time of the calcium indicator.
    tau_r : float
        Rise constant for the exponential trace, representing the rise time of the calcium indicator.
    trunc_thres : float, optional
        Truncation threshold for the generated exponential trace. Values below this threshold are omitted. Default is 1e-6.

    Returns
    -------
    C : np.ndarray
        Generated calcium trace for the cell.
    S : np.ndarray
        Generated Poisson spike train for the cell.
    """

    # Generate a Poisson spike train, which is a sequence of binary values (0 or 1) 
    # indicating whether a cell fires at each frame.
    S = random.binomial(n=1, p=pfire, size=frame).astype(float)

    # Generate a time array that goes from 0 to the total number of frames.
    t = np.arange(frame)

    # Calculate an exponential trace using the decay constant (tau_d) and the rise constant (tau_r)
    # This represents the temporal dynamics of the calcium indicator.
    v = np.exp(-t / tau_d) - np.exp(-t / tau_r)

    # Truncate the exponential trace at the specified threshold. 
    # This is to avoid very small values that can cause numerical instability.
    v = v[v > trunc_thres]

    # Convolve the exponential trace with the spike train to generate the calcium trace for the cell.
    # The convolution operation essentially models the effect of each spike on the calcium concentration.
    C = np.convolve(v, S, mode="full")[:frame]

    # Return the generated calcium trace and the spike train
    return C, S

def random_walk(n_stp: int,
                stp_var: float = 1,
                constrain_factor: float = 0,
                ndim: int = 1,
                norm: bool = False,
                integer: bool = True,
                nn: bool = False,
                smooth_var: Optional[float] = None) -> np.ndarray:
    """
    Generates a random walk in ndim dimensions.

    Parameters
    ----------
    n_stp : int
        Number of steps in the walk.
    stp_var : float, optional
        Variance of the steps. Default is 1.
    constrain_factor : float, optional
        Factor to constrain the walk towards the origin. Default is 0 (no constraint).
    ndim : int, optional
        Number of dimensions of the walk. Default is 1.
    norm : bool, optional
        If True, the walk is normalized to the range [0, 1]. Default is False.
    integer : bool, optional
        If True, the steps are rounded to the nearest integer. Default is True.
    nn : bool, optional
        If True, the walk is clipped to non-negative values. Default is False.
    smooth_var : float, optional
        If provided, the walk is smoothed with a Gaussian filter of this variance. Default is None.

    Returns
    -------
    walk : np.ndarray
        The generated random walk.

    More:
    -------
    This function creates a random walk, a type of stochastic process where each step is randomly determined.
    The function can generate both a simple random walk and a constrained random walk, where each step is 
    influenced by the previous one to encourage movement back towards the origin. The generated walk can be 
    in multiple dimensions, and additional options allow for normalization of the walk, rounding steps to the
    nearest integer, and smoothing of the walk using a Gaussian filter.

    """

    # Initialize the walk as an array of zeros
    walk = np.zeros(shape=(n_stp, ndim))

    # If a constrain factor is provided, we generate a constrained random walk
    if constrain_factor > 0:
        for i in range(n_stp):
            # Get the last step of the walk, or 0 if this is the first step
            last = walk[i - 1] if i > 0 else 0
            # Generate a new step as a Gaussian random value, with mean as a function of the last step
            walk[i] = last + random.normal(loc=-constrain_factor * last, scale=stp_var, size=ndim)
        
        # If integer is True, round the walk to the nearest integers
        if integer:
            walk = np.around(walk).astype(int)

    # If no constrain factor is provided, we generate a simple random walk
    else:
        # Generate the steps of the walk as Gaussian random values
        stps = random.normal(loc=0, scale=stp_var, size=(n_stp, ndim))
        
        # If integer is True, round the steps to the nearest integers
        if integer:
            stps = np.around(stps).astype(int)
        
        # Calculate the cumulative sum of the steps to generate the walk
        walk = np.cumsum(stps, axis=0)

    # If a smooth variance is provided, smooth the walk with a Gaussian filter
    if smooth_var is not None:
        for iw in range(ndim):
            walk[:, iw] = gaussian_filter1d(walk[:, iw], smooth_var)

    # If norm is True, normalize the walk to the range [0, 1]
    if norm:
        walk = (walk - walk.min(axis=0)) / (walk.max(axis=0) - walk.min(axis=0))
    # If nn is True, clip the walk to non-negative values
    elif nn:
        walk = np.clip(walk, 0, None)

    # Return the generated random walk
    return walk


def simulate_miniscope_data(
    ncell: int = 40,
    dims: Dict[str, int] = {"height": 256, "width": 256, "frame": 150},
    sig_scale: float = 1.0,
    sz_mean: float = 3.0,
    sz_sigma: float = 0.6,
    sz_min: float = 0.1,
    tmp_pfire: float = 0.01,
    tmp_tau_d: float = 6.0,
    tmp_tau_r: float = 1.0,
    post_offset: float = 1.0,
    post_gain: float = 50.0,
    bg_nsrc: int = 100,
    bg_tmp_var: float = 2.0,
    bg_cons_fac: float = 0.1,
    bg_smth_var: float = 60.0,
    mo_stp_var: float = 1.0,
    mo_cons_fac: float = 0.2,
    cent: Optional[np.ndarray] = None,
    zero_thres: float = 1e-8,
    chk_size: int = 1000,
) -> xr.DataArray:

    """
    Generates a simulated miniscope dataset that mimics the key properties of real miniscope data.

    This function simulates the spatiotemporal fluorescence signals of neurons and background components 
    by generating and then combining spatial footprints (Gaussian) and temporal traces (exponential) using
    user-defined parameters. It then adds spatial shifts to simulate motion artifacts, injects Gaussian noise, applies a linear
    transformation to adjust the signal and noise levels, and clips pixel values to an 8-bit range.

    Parameters
    ----------
    ncell : int
        Number of cells to simulate.
    dims : dict
        Dictionary specifying the dimensions (frame, height, width) of the data.
    sig_scale : float
        Signal scaling factor.
    sz_mean : float
        Mean size of the Gaussian cell.
    sz_sigma : float
        Standard deviation of the Gaussian cell size.
    sz_min : float
        Minimum size of the Gaussian cell.
    tmp_pfire : float
        Temporal probability of fire.
    tmp_tau_d : float
        Temporal decay constant.
    tmp_tau_r : float
        Temporal rise constant.
    post_offset : float
        Post-processing offset.
    post_gain : float
        Post-processing gain.
    bg_nsrc : int
        Number of background noise sources.
    bg_tmp_var : float
        Variance of the background temporal noise.
    bg_cons_fac : float
        Background noise constraint factor.
    bg_smth_var : float
        Variance of the background noise smoothing.
    mo_stp_var : float
        Variance of the motion step.
    mo_cons_fac : float
        Motion constraint factor.
    cent : np.ndarray, optional
        Centroid of the Gaussian cell. If not specified, a random centroid is generated.
    zero_thres : float, optional
        Threshold for zeroing out elements in the sparse matrix representation. Default is 1e-8.
    chk_size : int, optional
        Chunk size for data array computations. Default is 1000.

    Returns
    -------
    xr.DataArray
        Simulated data
    """

    # Extract frame, height and width from dimensions
    ff, hh, ww = dims["frame"], dims["height"], dims["width"]

    # Generate random shifts for simulating motion in the video. This is done using a random walk model.
    shifts = xr.DataArray(
        darr.from_array(
            random_walk(ff, ndim=2, stp_var=mo_stp_var, constrain_factor=mo_cons_fac),
            chunks=(chk_size, -1),
        ),
        dims=["frame", "shift_dim"],
        coords={"frame": np.arange(ff), "shift_dim": ["height", "width"]},
        name="shifts",
    )

    # Pad the shifts if they exceed a certain limit, i.e. if the shifts are too large, they are clipped to prevent artifacts in the simulated data.
    pad = np.absolute(shifts).max().values.item()
    if pad > 20:
        warnings.warn("maximum shift is {}, clipping".format(pad))
        shifts = shifts.clip(-20, 20)
    
    # If no cell centroid positions are provided, randomly generate them within the frame, leaving some padding around the edges.
    if cent is None:
        cent = np.stack(
            [
                np.random.randint(pad * 2, hh, size=ncell),
                np.random.randint(pad * 2, ww, size=ncell),
            ],
            axis=1,
        )
        
    # Generate spatial footprints for each cell using a Gaussian model.
    A = gauss_cell(
        2 * pad + hh,
        2 * pad + ww,
        sz_mean=sz_mean,
        sz_sigma=sz_sigma,
        sz_min=sz_min,
        cent=cent,
    )
    
    # Convert the footprints into a sparse matrix representation for efficient computation.
    A = darr.from_array(
        sparse.COO.from_numpy(np.where(A > zero_thres, A, 0)), chunks=-1
    )
    
    # Generate calcium traces for each cell. The temporal dynamics are modeled as an exponential decay (due to calcium indicator) modulated by a Poisson spike train.
    traces = [exp_trace(ff, tmp_pfire, tmp_tau_d, tmp_tau_r) for _ in range(len(cent))]
    
    # Convert the calcium traces and spike trains into Dask arrays for efficient computation.
    C = darr.from_array(np.stack([t[0] for t in traces]).T, chunks=(chk_size, -1))
    S = darr.from_array(np.stack([t[1] for t in traces]).T, chunks=(chk_size, -1))
    
    # Generate centroids for background noise
    
    cent_bg = np.stack(
        [
            np.random.randint(pad, pad + hh, size=bg_nsrc),
            np.random.randint(pad, pad + ww, size=bg_nsrc),
        ],
        axis=1,
    )
    
    # Generate spatial footprints for the background noise sources using a Gaussian model.
    A_bg = gauss_cell(
        2 * pad + hh,
        2 * pad + ww,
        sz_mean=sz_mean * 60,
        sz_sigma=sz_sigma * 10,
        sz_min=sz_min,
        cent=cent_bg,
    )
    
    # Convert the footprints for the background noise sources into a sparse matrix representation for efficient computation.
    A_bg = darr.from_array(
        sparse.COO.from_numpy(np.where(A_bg > zero_thres, A_bg, 0)), chunks=-1
    )
    
    # Generate temporal dynamics for the background noise sources using a random walk model.
    C_bg = darr.from_array(
        random_walk(
            ff,
            ndim=bg_nsrc,
            stp_var=bg_tmp_var,
            norm=False,
            integer=False,
            nn=True,
            constrain_factor=bg_cons_fac,
            smooth_var=bg_smth_var,
        ),
        chunks=(chk_size, -1),
    )
    
    # Compute the simulated calcium imaging video by multiplying the spatial footprints with the temporal dynamics and adding the result for all cells and background noise sources.
    Y = darr.blockwise(computeY, "fhw", A, "uhw", C, "fu", A_bg, "bhw", C_bg, "fb", shifts.data, "fs",
        dtype=np.uint8, sig_scale=sig_scale, noise_scale=0.1, post_offset=post_offset, post_gain=post_gain)
    
    # Remove the padding around the edges of the video if it was added before.
    if pad == 0:
        pad = None
    Y = Y[:, pad:-pad, pad:-pad]

    # Convert the simulated calcium imaging video and other variables into Xarray DataArrays for easy manipulation and indexing.
    uids, hs, ws, fs = np.arange(ncell), np.arange(hh), np.arange(ww), np.arange(ff)

    Y = xr.DataArray(
        Y,
        dims=["frame", "height", "width"],
        coords={"frame": fs, "height": hs, "width": ws},
        name="Simulated Miniscope Data",
    )
    
    # time = fs / sampling_rate
    # Y = Y.expand_dims(time=time, axis=0) # is this the correct way to add a redundant dim?

    # Return simulated data
    return Y #, A, C, S, shifts, time


def computeY(A: List[np.ndarray], C: np.ndarray, A_bg: List[np.ndarray], C_bg: np.ndarray, 
              shifts: List[np.ndarray], sig_scale: float, noise_scale: float, 
              post_offset: float, post_gain: float) -> np.ndarray:
    """
    Computes a simulated imaging data array.

    Parameters
    ----------
    A : list of np.ndarray
        List of spatial footprints for each cell.
    C : np.ndarray
        Array of calcium traces for each cell.
    A_bg : list of np.ndarray
        List of spatial footprints for each background noise source.
    C_bg : np.ndarray
        Array of temporal dynamics for each background noise source.
    shifts : list of np.ndarray
        List of shift values for each frame, simulating motion artifacts.
    sig_scale : float
        Scaling factor for the signal strength.
    noise_scale : float
        Scaling factor for the noise.
    post_offset : float
        Constant offset added to the data after noise addition.
    post_gain : float
        Gain factor applied to the data after the offset.

    Returns
    -------
    np.ndarray
        The resulting simulated imaging data array.
    """

    # Select the first element from each of the input lists
    A, C, A_bg, C_bg, shifts = A[0], C[0], A_bg[0], C_bg[0], shifts[0]

    # Compute the product of the calcium traces and spatial footprints for each cell
    # This gives the signal contribution from each cell
    Y = sparse.tensordot(C, A, axes=1)

    # Scale the signal contribution from each cell
    Y *= sig_scale

    # Compute the product of the temporal dynamics and spatial footprints for each background noise source
    # This gives the signal contribution from the background noise
    Y_bg = sparse.tensordot(C_bg, A_bg, axes=1)

    # Add the signal contribution from the background noise to the cell signal contribution
    Y += Y_bg

    # Delete the background noise contribution array to free memory
    del Y_bg

    # Apply shifts to each frame of the data to simulate motion artifacts
    for i, sh in enumerate(shifts):
        Y[i, :, :] = shift_perframe(Y[i, :, :], sh, fill=0)

    # Generate a noise array and add it to the data
    noise = np.random.normal(scale=noise_scale, size=Y.shape)
    Y += noise

    # Delete the noise array to free memory
    del noise

    # Add a constant offset to the data
    Y += post_offset

    # Scale the data by a gain factor
    Y *= post_gain

    # Clip the values in the data to the range 0-255
    np.clip(Y, 0, 255, out=Y)

    # Return the data as an 8-bit unsigned integer array
    return Y.astype(np.uint8)

