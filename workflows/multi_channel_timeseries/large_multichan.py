from pathlib import Path

import numpy as np
import h5py
import dask.array as da
import xarray as xr
from xarray.backends.api import open_datatree  # until API stabilizes

import panel as pn
import holoviews as hv

from ndpyramid import pyramid_create
from tsdownsample import MinMaxLTTBDownsampler

from IPython.display import display

hv.extension("bokeh")
pn.extension()

DATA_URL = 'https://datasets.holoviz.org/lfp/v1/sub-719828686_ses-754312389_probe-756781563_ecephys.nwb'
DATA_DIR = Path('./data')
DATA_FILENAME = Path(DATA_URL).name
DATA_PATH = DATA_DIR / DATA_FILENAME
PYRAMID_FILE = f"{DATA_PATH.stem}.zarr"
PYRAMID_PATH = DATA_DIR / PYRAMID_FILE
print(f'Local Original Data Path: {DATA_PATH}')
print(f'Pyramid Path: {PYRAMID_PATH}')

DATA_DIR.mkdir(parents=True, exist_ok=True)
if not DATA_PATH.exists():
    import wget
    print(f'Data downloading to: {DATA_PATH}')
    wget.download(DATA_URL, out=str(DATA_PATH))
else:
    print(f'Data exists at: {DATA_PATH}')

def print_hdf5_keys(filename, path='/'):
    """Prints all keys (paths) in an HDF5 file."""
    with h5py.File(filename, 'r') as f:
        for key in f[path].keys():
            full_path = f"{path}/{key}" if path != '/' else key
            print(full_path)
            if isinstance(f[full_path], h5py.Group):
                print_hdf5_keys(filename, full_path)

print_hdf5_keys(DATA_PATH, path='/processing')
print_hdf5_keys(DATA_PATH, path='/acquisition')

DATA_KEY = "acquisition/probe_756781563_lfp_data/data"
DATA_DIMS = {"time": "acquisition/probe_756781563_lfp_data/timestamps",
             "channel": "acquisition/probe_756781563_lfp_data/electrodes",
            }

def serialize_to_xarray(f, data_key, dims):
    """Serialize HDF5 data into an xarray Dataset with lazy loading."""
    # Extract coordinates for the specified dimensions
    coords = {dim: f[coord_key][:] for dim, coord_key in dims.items()}
    
    # Load the dataset lazily using Dask
    data = f[data_key]
    dask_data = da.from_array(data, chunks=(data.shape[0], 1))
    
    # Create the xarray DataArray and convert it to a Dataset
    data_array = xr.DataArray(
        dask_data,
        dims=list(dims.keys()),
        coords=coords,
        name=data_key.split("/")[-1]
    )
    ds = data_array.to_dataset(name='data')  # data_key.split("/")[-1]
    return ds

f = h5py.File(DATA_PATH, "r")
ts_ds = serialize_to_xarray(f, DATA_KEY, DATA_DIMS)

# The FACTORS will depend on the size of your dataset, available disk size, and the resolution needed
# For this demo, we are arbitrarily choosing 8 levels and scaling by quadrupling each preceding factor.
FACTORS = [4**i for i in range(8)]

def _help_downsample(data, time, n_out):
    """
    Helper function for downsampling and returning as a specific format.
    """
    indices = MinMaxLTTBDownsampler().downsample(time, data, n_out=n_out)
    return data[indices], indices


def apply_downsample(ts_ds, factor, dims):
    """
    Apply downsampling to a time series dataset.
    """
    dim = dims[0]
    n_out = len(ts_ds["data"]) // factor
    print(f"Downsampling by factor {factor} for a size of {n_out}.")
    ts_ds_downsampled, indices = xr.apply_ufunc(
        _help_downsample,
        ts_ds["data"],
        ts_ds[dim],
        kwargs=dict(n_out=n_out),
        input_core_dims=[[dim], [dim]],
        output_core_dims=[[dim], ["indices"]],
        exclude_dims=set((dim,)),
        vectorize=True,
        dask="parallelized",
        dask_gufunc_kwargs=dict(output_sizes={dim: n_out, "indices": n_out}),
    )
    # Update the dimension coordinates with the downsampled indices
    ts_ds_downsampled[dim] = ts_ds[dim].isel(time=indices.values[0])
    return ts_ds_downsampled.rename("data")


if not PYRAMID_PATH.exists():
    print(f'Creating Pyramid: {PYRAMID_PATH}')
    ts_dt = pyramid_create(
        ts_ds,
        factors=FACTORS,
        dims=["time"],
        func=apply_downsample,
        type_label="pick",
        method_label="pyramid_downsample",
    )
    display(ts_dt)
else:
    print(f'Pyramid Already Exists: {PYRAMID_PATH}')

if not PYRAMID_PATH.exists():
    PYRAMID_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts_dt.to_zarr(PYRAMID_PATH, mode="w")

ts_dt = open_datatree(PYRAMID_PATH, engine="zarr")
ts_dt

def _extract_ds(ts_dt, level, channels=None):
    """Extract a dataset at a specific level."""
    ds = ts_dt[str(level)].ds
    return ds if channels is None else ds.sel(channel=channels)

# Grab the timestamps from the coarsest level of the datatree for initialization
num_levels = len(ts_dt)
coarsest_level = str(num_levels - 1)
time_da = _extract_ds(ts_dt, coarsest_level)["time"]
channels = ts_dt[coarsest_level].ds["channel"].values
num_channels = len(channels)

from holoviews import streams

# Define a stream to hold the pyramid level
pyramid_level_stream = streams.Stream.define('PyramidLevel', pyramid_level=0)()

X_PADDING = 0.2  # buffer x-range to reduce update latency with pans and zoom-outs

amplitude_dim = hv.Dimension("amplitude", unit="µV")
time_dim = hv.Dimension("time", unit="s")  # match the index name in the df

def rescale(x_range, y_range, width, scale, height):

    # Handle case of stream initialization
    if x_range is None:
        x_range = time_da.min().item(), time_da.max().item()
    if y_range is None:
        y_range = 0, num_channels

    # define data range slice
    x_padding = (x_range[1] - x_range[0]) * X_PADDING
    time_slice = slice(x_range[0] - x_padding, x_range[1] + x_padding)
    channel_slice = slice(y_range[0], y_range[1])

    # calculate the appropriate pyramid level and size
    if width is None or height is None:
        pyramid_level = num_levels - 1
        size = time_da.size
    else:
        sizes = np.array([
            _extract_ds(ts_dt, pyramid_level)["time"].sel(time=time_slice).size
            for pyramid_level in range(num_levels)
        ])
        diffs = sizes - width
        pyramid_level = np.argmin(np.where(diffs >= 0, diffs, np.inf))  # nearest higher-resolution level
        size = sizes[pyramid_level]

    # Update the pyramid_level_stream
    pyramid_level_stream.event(pyramid_level=int(pyramid_level))

    title = (
        f"[Pyramid Level {pyramid_level} ({x_range[0]:.2f}s - {x_range[1]:.2f}s)]   "
        f"[Time Samples: {size}]  [Plot Size WxH: {width}x{height}]"
    )

    # extract new data and re-paint the plot
    ds = _extract_ds(ts_dt, pyramid_level, channels).sel(time=time_slice, channel=channel_slice).load()

    curves = {}
    for channel in ds["channel"].values.tolist():
        curves[str(channel)] = hv.Curve(ds.sel(channel=channel), [time_dim], ['data'], label=str(channel)).redim(
            data=amplitude_dim).opts(
            color="black",
            line_width=1,
            subcoordinate_y=True,
            subcoordinate_scale=4,
            hover_tooltips=[
                ("channel", "$label"),
                ("time"),
                ("amplitude")],
            tools=["xwheel_zoom"],
            active_tools=["box_zoom"],
        )

    curves_overlay = hv.NdOverlay(curves, kdims="Channel", sort=False).opts(
        xlabel="Time (s)",
        ylabel="Channel",
        title=title,
        show_legend=False,
        padding=0,
        min_height=600,
        responsive=True,
        framewise=True,
        axiswise=True,
    )
    return curves_overlay

range_stream = hv.streams.RangeXY()
size_stream = hv.streams.PlotSize()
dmap = hv.DynamicMap(rescale, streams=[size_stream, range_stream])

from scipy.stats import zscore
from holoviews.operation.datashader import rasterize
from holoviews.plotting.links import RangeToolLink

y_positions = range(num_channels)
yticks = [(i, ich) for i, ich in enumerate(channels)]

z_data = zscore(ts_dt[coarsest_level].ds["data"].values, axis=1)

minimap = rasterize(
    hv.QuadMesh((time_da, y_positions, z_data), ["Time", "Channel"], "Amplitude")
)

minimap = minimap.opts(
    cnorm='eq_hist',
    cmap="RdBu_r",
    alpha=0.5,
    xlabel="",
    yticks=[yticks[0], yticks[-1]],
    toolbar="disable",
    height=120,
    responsive=True,
)

tool_link = RangeToolLink(
    minimap,
    dmap,
    axes=["x", "y"],
    boundsy=(-0.5, len(channels) // 1.25),
)

def pyramid_plot(pyramid_level):
    num_levels = len(ts_dt)
    rectangles = []
    for level in range(num_levels):
        # Widest level is at the bottom
        width = 1.0 - (level / num_levels) * 0.7
        x0, y0 = (0.5 - width / 2), level
        x1, y1 = (0.5 + width / 2), level + 1
        color = 'lightgray' if level != pyramid_level else '#3CBAC8'
        
        # Rectangle for each pyramid level
        rect = hv.Rectangles([(x0, y0, x1, y1)]).opts(
            fill_color=color,
            line_color='black',
        )
        
        # Text label centered in each rectangle
        text = hv.Text(0.5, y0 + 0.5, f"L {level}").opts(
            text_align="center",
            text_baseline="middle",
            text_font_size="8pt",
            xaxis=None,
            yaxis=None,
            color="black",
        )
        
        rectangles.append(rect * text)
    
    # Combine all rectangles and labels into the pyramid shape
    pyramid = hv.Overlay(rectangles).opts(
        show_frame=False,
        xaxis=None,
        yaxis=None,
        width=150,
        height=200,
        ylim=(-.1, num_levels),
        xlim=(0, 1.1),
        toolbar=None,
        apply_hard_bounds=True,
        title="Pyramid Level",
    )
    return pyramid

pyramid_dmap = hv.DynamicMap(pyramid_plot, streams=[pyramid_level_stream])

dmap.event(x_range=(5140, 5190))  # Trigger an initial range event to get the appropriate pyramid layer

app = pn.Row(
    pyramid_dmap,
    pn.Column(dmap, minimap),
)

template = pn.template.FastListTemplate(
    main=[pn.Column(dmap, minimap)],
    sidebar=[pn.Column(pyramid_dmap,
                       align="center", 
                       sizing_mode="stretch_width")],
    title="Multichannel Timeseries with Large Datasets",
    accent="#3CBAC8",
    sidebar_width=150,
).servable()
