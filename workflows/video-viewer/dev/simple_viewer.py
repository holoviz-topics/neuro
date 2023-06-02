from typing import Union, List, Optional
import numpy as np
import xarray as xr
import holoviews as hv
import panel as pn
import param
import functools as fct
import itertools as itt
from collections import OrderedDict
from datashader import count_cat
from holoviews.streams import Stream, BoxEdit, RangeXY
from holoviews.operation.datashader import datashade
import holoviews as hv
hv.extension('bokeh')
import panel.widgets as pnwgt
from bokeh.palettes import Category10_10, Viridis256



_f = ds.coords["frame"].values
_h = ds.sizes["height"]
_w = ds.sizes["width"]

def img(f, ds):  # Function to generate HoloViews image object for a given frame
    return hv.Image(ds.sel(frame=f).compute(), kdims=["width", "height"])

# Define frame stream
CStream = Stream.define(
    "CStream",
    f=param.Integer(default=int(_f.min()), bounds=(_f.min(), _f.max())),
)
strm_f = CStream()

# Partial function for image generation
fim = fct.partial(img, ds=ds)

# Create a dynamic map for images with the given partial function and frame stream
im = hv.DynamicMap(fim, streams=[strm_f]).opts(
    frame_width=500, aspect=_w / _h, cmap="Viridis"
).opts(style=dict(cmap="Viridis"))