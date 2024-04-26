
# First, download a dataset, e.g.:
# (3GB) datasets.holoviz.org/ephys_sim/v1/ephys_sim_neuropixels_10s_384ch.h5

from pathlib import Path
import h5py
import numpy as np
import xarray as xr
import dask.array as da
import datatree as dt
from tsdownsample import MinMaxLTTBDownsampler


def _help_downsample(data, time, n_out):
    print(f"{len(time)} -> {n_out} samples")
    indices = MinMaxLTTBDownsampler().downsample(time, data, n_out=n_out)
    return data[indices], indices


def apply_downsample(ts_da, n_out):
    times = ts_da["time"]
    if n_out != len(ts_da["time"]):
        print("Downsampling")
        ts_ds_downsampled, time_indices = xr.apply_ufunc(
            _help_downsample,
            ts_da,
            times,
            kwargs=dict(n_out=n_out),
            input_core_dims=[["time"], ["time"]],
            output_core_dims=[["time"], ["indices"]],
            exclude_dims=set(("time",)),
            vectorize=False,
            dask="parallelized",
            dask_gufunc_kwargs=dict(output_sizes={"time": n_out, "indices": n_out}),
        )
        ts_da_downsampled = ts_ds_downsampled.to_dataarray("channel")
        times_subset = times.values[time_indices.to_array().values]
    else:
        print("No downsampling")
        ts_da_downsampled = ts_da.to_dataarray("channel")
        times_subset = np.vstack(
            [times.values for _ in range(ts_da_downsampled["channel"].size)]
        )
    return xr.DataArray(
        ts_da_downsampled.values,
        dims=["channel", "time"],
        coords={"multi_time": (("channel", "time"), times_subset)},
        name="data",
    )


def build_dataset(f, data_key, dims, use_dask=True):
    if data_key not in f:
        raise KeyError(f"{data_key} not found in file.")
    
    for key, value in dims.items():
        if value not in f:
            raise KeyError(f"Dimension '{value}' for key '{key}' not found in file.")
    
    coords = {key: f[value] for key, value in dims.items()}
    data = f[data_key]
    if "channel" not in dims:
        dims["channel"] = np.arange(data.shape[1])
    if use_dask:
        array = da.from_array(data, name="data", chunks=(data.shape[0], 5))
    else:
        array = data
    ds = xr.DataArray(
        array,
        dims=dims,
        coords=coords,
        name="data"
    ).to_dataset()
    return ds


# adapted from https://github.com/carbonplan/ndpyramid/blob/main/ndpyramid/core.py
def multiscales_template(
    *,
    datasets: list = None,
    type: str = "",
    method: str = "",
    version: str = "",
    args: list = None,
    kwargs: dict = None,
):
    if datasets is None:
        datasets = []
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    # https://forum.image.sc/t/multiscale-arrays-v0-1/37930
    return [
        {
            "datasets": datasets,
            "type": type,
            "metadata": {
                "method": method,
                "version": version,
                "args": args,
                "kwargs": kwargs,
            },
        }
    ]


def pyramid_downsample(ds: xr.Dataset, *, factors: list[int], **kwargs) -> dt.DataTree:
    """Create a multiscale pyramid via coarsening of a dataset by given factors

    Parameters
    ----------
    ds : xarray.Dataset
        The dataset to coarsen.
    factors : list[int]
        The factors to coarsen by.
    kwargs : dict
        Additional keyword arguments to pass to xarray.Dataset.coarsen.
    """
    ds = ds["data"].to_dataset("channel")
    factors = np.array(factors).astype(int).tolist()

    # multiscales spec
    save_kwargs = locals()
    del save_kwargs["ds"]

    attrs = {
        "multiscales": multiscales_template(
            datasets=[{"path": str(i)} for i in range(len(factors))],
            type="pick",
            method="pyramid_downsample",
            version="0.1",
            kwargs=save_kwargs,
        )
    }

    # set up pyramid
    plevels = {}

    # pyramid data
    for key, factor in enumerate(factors):
        factor += 1
        result = apply_downsample(ds, len(ds["time"]) // factor)
        plevels[str(key)] = result

    plevels["/"] = xr.Dataset(attrs=attrs)
    return dt.DataTree.from_dict(plevels)


# %% Create time pyramid dataset

PYRAMID_FILE = 'pyramid_neuropix_10s.zarr'
CREATE_PYRAMID = True
if CREATE_PYRAMID:
    
    # f = h5py.File(Path.home() / Path("allensdk_cache/session_715093703/probe_810755797_lfp.nwb"), "r")

    # ts_ds = build_dataset(
    #     f,
    #     "acquisition/probe_810755797_lfp_data/data",
    #     {
    #         "time": "acquisition/probe_810755797_lfp_data/timestamps",
    #         "channel": "acquisition/probe_810755797_lfp_data/electrodes",
    #     },
    # ).isel(channel=list(np.arange(0,4)))

    f = h5py.File(Path.home() / Path("data/ephys_sim_neuropixels/ephys_sim_neuropixels_10s_384ch.h5"), "r")
    ts_ds = build_dataset(
        f,
        "/recordings",
        {
            "time": "timestamps",
            # channels don't have a name in this dataset, but they have other metadata like location on the probe
            # Just exclude the channel dim and have incrementing dummy labels be used instead
        },
    )

    data_length = ts_ds["time"].size
    screen_width = 1500 #(in px)
    num_factors = 4

    target_factor = data_length / screen_width
    max_zoom = int(np.log2(target_factor))
    all_factors = 2 ** np.arange(max_zoom + 1)
    sub_factors = all_factors[::max_zoom // (num_factors - 1)]
    if sub_factors[-1] != all_factors[-1]:
        sub_factors = np.append(sub_factors, all_factors[-1])
    ts_dt = pyramid_downsample(ts_ds, factors=sub_factors)
    ts_dt.to_zarr(PYRAMID_FILE, mode="w")
ts_dt = dt.open_datatree(PYRAMID_FILE, engine="zarr")


# %% Plot 
import numpy as np
import panel as pn
import datatree as dt
import holoviews as hv
from scipy.stats import zscore
from holoviews.plotting.links import RangeToolLink
from holoviews.operation.datashader import rasterize
from bokeh.models.tools import WheelZoomTool, HoverTool

hv.extension("bokeh")


CLIM_MUL = 0.5
MAX_CHANNELS = 20
X_PADDING = 0.2  # padding for the x_range


def _extract_ds(ts_dt, level, channel):
    ds = (
        ts_dt[str(level)]
        .sel(channel=channel)
        .ds.swap_dims({"time": "multi_time"})
        .rename({"multi_time": "time"})
    )
    return ds


def rescale(x_range, y_range, width, scale, height):
    import time

    s = time.perf_counter()
    print(f"- Update triggered! {width=} {x_range=}")
    if x_range is None:
        x_range = time_da.min().item(), time_da.max().item()
    if y_range is None:
        y_range = 0, num_channels
    x_padding = (x_range[1] - x_range[0]) * X_PADDING
    time_slice = slice(x_range[0] - x_padding, x_range[1] + x_padding)

    if width is None or height is None:
        zoom_level = num_levels - 1
        size = data.size
    else:
        sizes = [
            _extract_ds(ts_dt, zoom_level, 0)["time"].sel(time=time_slice).size
            for zoom_level in range(num_levels)
        ]
         # use width * [scalar] to alter the zoom level threshold
        zoom_level = np.argmin(np.abs(np.array(sizes) - width))
        size = sizes[zoom_level]
    e = time.perf_counter()
    print(f"Zoom level computation took {e-s:.2f}s")

    title = (
        f"level {zoom_level} ({x_range[0]:.2f}s - {x_range[1]:.2f}s) "
        f"(WxH: {width}x{height}) (length: {size})"
    )
    # if zoom_level == pn.state.cache.get("current_zoom_level") and pn.state.cache.get(
    #     "curves"
    # ):
    #     cached_x_range = pn.state.cache["x_range"]
    #     if x_range[0] >= cached_x_range[0] and x_range[1] <= cached_x_range[1]:
    #         print(f"Using cached curves! {zoom_level=}")
    #         if x_range != cached_x_range:
    #             print(f"Different x_range: {x_range} {cached_x_range}")
    #         return pn.state.cache["curves"].opts(title=title)

    curves = hv.Overlay(kdims="Channel")
    for channel in channels:
        hover = HoverTool(
            tooltips=[
                ("Channel", str(channel)),
                ("Time", "$x s"),
                ("Amplitude", "$y µV"),
            ]
        )
        sub_ds = _extract_ds(ts_dt, zoom_level, channel).sel(time=time_slice).load()
        curve = hv.Curve(sub_ds, ["time"], ["data"], label=f"ch{channel}").opts(
            color="black",
            line_width=1,
            subcoordinate_y=True,
            subcoordinate_scale=1,
            default_tools=["pan", "reset", WheelZoomTool(), hover],
        )
        curves *= curve
    print(f"Overlaying curves took {time.perf_counter()-e:.2f}s")

    curves = curves.opts(
        xlabel="Time (s)",
        ylabel="Channel",
        title=title,
        show_legend=False,
        padding=0,
        aspect=1.5,
        responsive=True,
        framewise=True,
        axiswise=True,
    )
    pn.state.cache["current_zoom_level"] = zoom_level
    pn.state.cache["x_range"] = x_range
    pn.state.cache["curves"] = curves
    print(f"Using updated curves! {x_range} {zoom_level}\n\n")
    return curves

ts_dt = dt.open_datatree(PYRAMID_FILE, engine="zarr").sel(
    channel=slice(0, MAX_CHANNELS)
)
num_levels = len(ts_dt)
time_da = _extract_ds(ts_dt, 0, 0)["time"]
channels = ts_dt["0"].ds["channel"].values
num_channels = len(channels)
data = ts_dt["0"].ds["data"].values.T
range_stream = hv.streams.RangeXY()
size_stream = hv.streams.PlotSize()
dmap = hv.DynamicMap(rescale, streams=[size_stream, range_stream])

y_positions = range(num_channels)
yticks = [(i, ich) for i, ich in enumerate(channels)]
z_data = zscore(data.T, axis=1)

minimap = rasterize(
    hv.Image((time_da, y_positions, z_data), ["Time (s)", "Channel"], "Amplitude (uV)")
)
minimap = minimap.opts(
    cmap="RdBu_r",
    xlabel="",
    yticks=[yticks[0], yticks[-1]],
    toolbar="disable",
    height=120,
    responsive=True,
    clim=(-z_data.std() * CLIM_MUL, z_data.std() * CLIM_MUL),
)
tool_link = RangeToolLink(
    minimap,
    dmap,
    axes=["x", "y"],
    boundsx=(0, time_da.max().item() // 2),
    boundsy=(0, len(channels)),
)
pn.template.FastListTemplate(main=[(dmap + minimap).cols(1)]).servable()
# %%
