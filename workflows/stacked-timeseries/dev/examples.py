from pathlib import Path
from scipy.stats import zscore
import h5py
import numpy as np

import holoviews as hv; hv.extension('bokeh')
from holoviews.plotting.links import RangeToolLink
from holoviews.operation.datashader import rasterize
from bokeh.models import HoverTool
import panel as pn; pn.extension()

# local_data_dir = Path.home() / "data" / "ephys_sim_neuropixels"
# filename = 'ephys_sim_neuropixels_10s_384ch.h5'
# full_path = local_data_dir / filename

# f = h5py.File(full_path, "r")
 
# n_sample_chans = 40
# n_sample_times = 25000 # sampling frequency is 25 kHz
# clim_mul = 2

# time = f['timestamps'][:n_sample_times]
# data = f['recordings'][:n_sample_times,:n_sample_chans].T

# f.close()

# channels = [f'ch{i}' for i in range(n_sample_chans)]
# channels = channels[:n_sample_chans]

# main plot
hover = HoverTool(tooltips=[
    ("Channel", "@channel"),
    ("Time", "$x s"),
    ("Amplitude", "$y µV")])

clim_mul = 2
n_channels = 10 
n_seconds = 15

total_samples = 512*n_seconds
time = np.linspace(0, n_seconds, total_samples)
data = np.random.randn(n_channels, total_samples).cumsum(axis=1)
channels = [f"EEG {i}" for i in range(n_channels)]

channel_curves = []
for i, channel in enumerate(channels):
    ds = hv.Dataset((time, data[i,:], channel), ["Time", "Amplitude", "channel"])
    curve = hv.Curve(ds, "Time", ["Amplitude", "channel"], label=f'{channel}')
    curve.opts(color="black", line_width=1, subcoordinate_y=True, subcoordinate_scale=3, tools=[hover])
    channel_curves.append(curve)

curves = hv.Overlay(channel_curves, kdims="Channel")

curves = curves.opts(
    xlabel="Time (s)", ylabel="Channel", show_legend=False,
    padding=0, aspect=1.5, responsive=True, shared_axes=False, framewise=False)

# minimap
y_positions = range(len(channels))
yticks = [(i, ich) for i, ich in enumerate(channels)]
z_data = zscore(data, axis=1)

minimap = rasterize(hv.Image((time, y_positions, z_data), ["Time (s)", "Channel"], "Amplitude (uV)"))
minimap = minimap.opts(
    cmap="RdBu_r", colorbar=False, xlabel='', yticks=[yticks[0], yticks[-1]], toolbar='disable',
    height=120, responsive=True, clim=(-z_data.std()*clim_mul, z_data.std()*clim_mul))

RangeToolLink(minimap, curves, axes=["x", "y"],
              boundsx=(.1, .3),
              boundsy=(10, 30))

pn.Column((curves + minimap).cols(1)).servable()