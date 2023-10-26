import numpy as np

from bokeh.core.properties import field
from bokeh.io import show
from bokeh.models import (ColumnDataSource, DataRange1d, FactorRange, HoverTool,
                          Range1d, WheelZoomTool, ZoomInTool, ZoomOutTool)
from bokeh.palettes import Category10
from bokeh.plotting import figure

np.random.seed(0)

categorical = False

n_channels = 10
n_seconds = 15
fs = 512
max_ch_disp = 5  # max channels to initially display
max_t_disp = 3 # max time in seconds to initially display

total_samples = n_seconds * fs
time = np.linspace(0, n_seconds, total_samples)
data = np.random.randn(n_channels, total_samples).cumsum(axis=1)
channels = [f'EEG {i}' for i in range(n_channels)]

hover = HoverTool(tooltips=[
    ("Channel", "$name"),
    ("Time", "$x s"),
    ("Amplitude", "$y µV"),
])

x_range = Range1d(start=time.min(), end=time.max())
#x_range = DataRange1d()
#y_range = DataRange1d() # bug
if categorical:
    y_range = FactorRange(factors=channels)
else:
    y_range = Range1d(start=-0.5, end=len(channels) - 1 + 0.5)

p = figure(x_range=x_range, y_range=y_range, lod_threshold=None)

source = ColumnDataSource(data=dict(time=time))
renderers = []

for i, channel in enumerate(channels):
    if categorical:
        y_target=Range1d(start=i, end=i + 1)
    else:
        y_target=Range1d(start=i - 10.5, end=i + 10.5)

    xy = p.subplot(
        x_source=p.x_range,
        y_source=Range1d(start=data[i].min(), end=data[i].max()),
        #y_source=DataRange1d(),
        x_target=p.x_range,
        y_target=y_target,
    )

    source.data[channel] = data[i]
    line = xy.line(field("time"), field(channel), color=Category10[10][i], source=source, name=channel)
    renderers.append(line)

if not categorical:
    from bokeh.models import FixedTicker
    ticks = list(range(len(channels)))
    p.yaxis.ticker = FixedTicker(ticks=ticks)
    p.yaxis.major_label_overrides = {i: f"EEG {i}" for i in ticks}

wheel_zoom = WheelZoomTool()#renderers=renderers)
zoom_in = ZoomInTool(renderers=renderers)
zoom_out = ZoomOutTool(renderers=renderers)

p.add_tools(wheel_zoom, zoom_in, zoom_out, hover)
p.toolbar.active_scroll = wheel_zoom

show(p)