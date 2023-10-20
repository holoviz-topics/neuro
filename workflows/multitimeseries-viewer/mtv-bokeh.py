import numpy as np; np.random.seed(0)
from scipy.stats import zscore

from bokeh.core.properties import field
from bokeh.io import show, output_notebook
from bokeh.layouts import column, row
from bokeh.models import (ColumnDataSource, CustomJS, Div, FactorRange, HoverTool,
                          Range1d, Switch, WheelZoomTool, ZoomInTool, ZoomOutTool, 
                          RangeTool)
from bokeh.palettes import Category10
from bokeh.plotting import figure
from bokeh.models import FixedTicker

n_channels = 20
n_seconds = 10
max_ch_disp = n_channels/2  # max channels to initially display
max_t_disp = n_seconds/2 # max time in seconds to initially display
fs = 512 # Hz
total_samples = fs*n_seconds
time = np.linspace(0, n_seconds, total_samples)
data = np.random.randn(n_channels, total_samples).cumsum(axis=1)
channels = [f"EEG {i}" for i in range(n_channels)]

hover = HoverTool(tooltips=[
    ("Channel", "$name"),
    ("Time", "$x s"),
    ("Amplitude", "$y µV"),
])

x_range = Range1d(start=time.min(), end=time.max())
y_range = Range1d(start=-0.5, end=len(channels) - 1 + 0.5)
p = figure(x_range=x_range, y_range=y_range, height=500, width=800,
           x_axis_label='Time (s)',
           lod_threshold=None, tools="pan,reset")

source = ColumnDataSource(data=dict(time=time))
renderers = []

for i, channel in enumerate(channels):
    
    xy = p.subplot(
        x_source=p.x_range,
        y_source=Range1d(start=data[i].min(), end=data[i].max()),
        x_target=p.x_range,
        y_target=Range1d(start=i - 0.5, end=i + 0.5),
    )

    source.data[channel] = data[i]
    line = xy.line(field("time"), field(channel), color='black', source=source, name=channel)
    renderers.append(line)

ticks = list(range(len(channels)))
p.yaxis.ticker = FixedTicker(ticks=ticks)
p.yaxis.major_label_overrides = {i: f"EEG {i}" for i in ticks}

level = 1

ywheel_zoom = WheelZoomTool(renderers=renderers, level=level, dimensions="height")
xwheel_zoom = WheelZoomTool(renderers=renderers, level=level, dimensions="width")
yzoom_in = ZoomInTool(renderers=renderers, level=level, dimensions="height")
yzoom_out = ZoomOutTool(renderers=renderers, level=level, dimensions="height")

p.add_tools(ywheel_zoom, xwheel_zoom, yzoom_in, yzoom_out, hover)
p.toolbar.active_scroll = ywheel_zoom

z_data = zscore(data, axis=1)

range_tool = RangeTool(x_range=p.x_range, y_range=p.y_range)
range_tool.x_range.update(start=0, end=max_t_disp)
range_tool.y_range.update(start=0, end=max_ch_disp)
range_tool.overlay.fill_alpha = .8

select = figure(height=120, width=800, tools="", toolbar_location=None, y_axis_type=None,
                x_range=(time.min(), time.max()),
                y_range=(-0.5, len(channels) - 1 + 0.5))
select.image(image=[z_data], x=0, y=0, dw=n_seconds, dh=n_channels, palette="Sunset11")
select.add_tools(range_tool)

show(column(p, select))