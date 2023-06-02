import os
import shutil
from pathlib import Path
from typing import Callable, Optional, Union

import dask as da
import dask.array as darr
import ffmpeg
import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage.measurements import center_of_mass


def shift_perframe(fm, sh, fill=np.nan):
    if np.isnan(fm).all():
        return fm
    sh = np.around(sh).astype(int)
    fm = np.roll(fm, sh, axis=np.arange(fm.ndim))
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


def save_minian(
    var: xr.DataArray,
    dpath: str,
    meta_dict: Optional[dict] = None,
    overwrite=False,
    compute=True,
) -> xr.DataArray:
    dpath = os.path.normpath(dpath)
    Path(dpath).mkdir(parents=True, exist_ok=True)
    ds = var.to_dataset()
    if meta_dict is not None:
        pathlist = os.path.split(os.path.abspath(dpath))[0].split(os.sep)
        ds = ds.assign_coords(
            **dict([(dn, pathlist[di]) for dn, di in meta_dict.items()])
        )
    md = {True: "a", False: "w-"}[overwrite]
    fp = os.path.join(dpath, var.name + ".zarr")
    if overwrite:
        try:
            shutil.rmtree(fp)
        except FileNotFoundError:
            pass
    arr = ds.to_zarr(fp, compute=compute, mode=md)
    if compute:
        arr = xr.open_zarr(fp)[var.name]
        arr.data = darr.from_zarr(os.path.join(fp, var.name), inline_array=True)
    return arr


def write_vid_blk(arr, fname, options, process):
    process = (
        process.output(fname, **options).overwrite_output().run_async(pipe_stdin=True)
    )
    arr = arr.tobytes()
    process.stdin.write(arr)
    process.stdin.close()
    process.wait()
    return fname


def write_video(
    arr: xr.DataArray,
    vname: Optional[str] = None,
    vpath: Optional[str] = ".",
    vext: Optional[str] = "mp4",
    norm=True,
    options={
        "r": "30",
        "pix_fmt": "yuv420p",
        "vcodec": "libx264",
        "crf": "18",
        "preset": "ultrafast",
    },
    chunked=True,
) -> str:
    """
    Write a video from a movie array using `python-ffmpeg`.
    Parameters
    ----------
    arr : xr.DataArray
        Input movie array. Should have dimensions: ("frame", "height", "width")
        and should only be chunked along the "frame" dimension.
    vname : str, optional
        The name of output video. If `None` then a random one will be generated
        using :func:`uuid4.uuid`. By default `None`.
    vpath : str, optional
        The path to the folder containing the video. By default `"."`.
    norm : bool, optional
        Whether to normalize the values of the input array such that they span
        the full pixel depth range (0, 255). By default `True`.
    options : dict, optional
        Optional output arguments passed to `ffmpeg`. By default `{"crf": "18",
        "preset": "ultrafast"}`.
    Returns
    -------
    fname : str
        The absolute path to the video file.
    See Also
    --------
    ffmpeg.output
    """
    # if not vname:
    #     vname = uuid4()
    # if norm:
    #     arr_opt = fct.partial(
    #         custom_arr_optimize, rename_dict={"rechunk": "merge_restricted"}
    #     )
    #     with dask.config.set(array_optimize=arr_opt):
    #         arr = arr.astype(np.float32)
    #         arr_max = arr.max().compute().values
    #         arr_min = arr.min().compute().values
    #     den = arr_max - arr_min
    #     arr -= arr_min
    #     arr /= den
    #     arr *= 255
    # arr = arr.clip(0, 255)
    # arr = arr.astype(np.uint8)
    w, h = arr.sizes["width"], arr.sizes["height"]
    process = ffmpeg.input(
        "pipe:",
        format="rawvideo",
        pix_fmt="gray",
        s="{}x{}".format(w, h),
        r=options["r"],
    ).filter("pad", int(np.ceil(w / 2) * 2), int(np.ceil(h / 2) * 2))
    if chunked:
        fname = [
            da.delayed(write_vid_blk)(
                a,
                os.path.join(vpath, ".".join([vname, str(i), vext])),
                options,
                process,
            )
            for i, a in enumerate(arr.data.to_delayed().squeeze())
        ]
        fname = da.compute(fname)[0]
    else:
        fname = os.path.join(vpath, ".".join([vname, vext]))
        process = (
            process.output(fname, **options)
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )
        for blk in arr.data.blocks:
            process.stdin.write(np.array(blk).tobytes())
        process.stdin.close()
        process.wait()
    return fname


def open_minian(
    dpath: str, post_process: Optional[Callable] = None, return_dict=False
) -> Union[dict, xr.Dataset]:
    if os.path.isfile(dpath):
        ds = xr.open_dataset(dpath).chunk()
    elif os.path.isdir(dpath):
        dslist = []
        for d in os.listdir(dpath):
            arr_path = os.path.join(dpath, d)
            if os.path.isdir(arr_path):
                arr = list(xr.open_zarr(arr_path, consolidated=False).values())[0]
                arr.data = darr.from_zarr(
                    os.path.join(arr_path, arr.name), inline_array=True
                )
                dslist.append(arr)
        if return_dict:
            ds = {d.name: d for d in dslist}
        else:
            ds = xr.merge(dslist, compat="no_conflicts")
    if (not return_dict) and post_process:
        ds = post_process(ds, dpath)
    return ds


def centroid(A: xr.DataArray) -> pd.DataFrame:
    def rel_cent(im):
        im_nan = np.isnan(im)
        if im_nan.all():
            return np.array([np.nan, np.nan])
        if im_nan.any():
            im = np.nan_to_num(im)
        cent = np.array(center_of_mass(im))
        return cent / im.shape

    gu_rel_cent = darr.gufunc(
        rel_cent,
        signature="(h,w)->(d)",
        output_dtypes=float,
        output_sizes=dict(d=2),
        vectorize=True,
    )
    cents = xr.apply_ufunc(
        gu_rel_cent,
        A.chunk(dict(height=-1, width=-1)),
        input_core_dims=[["height", "width"]],
        output_core_dims=[["dim"]],
        dask="allowed",
    ).assign_coords(dim=["height", "width"])
    cents_df = (
        cents.rename("cents")
        .to_series()
        .dropna()
        .unstack("dim")
        .rename_axis(None, axis="columns")
        .reset_index()
    )
    h_rg = (A.coords["height"].min().values, A.coords["height"].max().values)
    w_rg = (A.coords["width"].min().values, A.coords["width"].max().values)
    cents_df["height"] = cents_df["height"] * (h_rg[1] - h_rg[0]) + h_rg[0]
    cents_df["width"] = cents_df["width"] * (w_rg[1] - w_rg[0]) + w_rg[0]
    return cents_df
