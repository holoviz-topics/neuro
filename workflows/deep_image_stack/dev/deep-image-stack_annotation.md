# Deep Image Stack Annotation

![](assets/20240725_deep_image_stack_annotation.png)


## Overview

This workflow is an exension of the primary [deep image stack workflow](./workflow_deep-image-stack.ipynb) that adds spatial annotation capabilities. We will also demonstrate the dynamic plotting of timeseries based on the annotated regions.

### Key Software
Alongside [HoloViz](https://github.com/holoviz), [Bokeh](https://holoviz.org/), and several other foundational packages, we make extensive use of key open source libraries to implement our solution, such as:

- **[HoloNote](https://github.com/pydata/xarray):** Provides for annotation capabilities on HoloViews elements.

## Prerequisites and Resources

| Topic | Type | Notes |
| --- | --- | --- |
| [Deep Image Stack Workflow](./workflow_deep-image-stack.ipynb) | Prerequisite | Primary workflow |

## Imports and Configuration


```python
from pathlib import Path
import numpy as np
import xarray as xr
import holoviews as hv
import panel as pn

pn.extension()
hv.extension('bokeh')
```

## Loading and Inspecting the Data


```python
DATA_PATH = "data/real_miniscope_uint8.zarr"

ds = xr.open_dataset(
    DATA_PATH,
    engine = 'zarr',
    chunks = {'frame': 400, 'height':-1, 'width':-1},  # chunk by sets of complete frames
)
da = ds['varr_ref']
da
```

## Data Visualization

Let's start with our simple HoloViews based app that is complementary to the other approches in the primary workflow. We will want to customize the positioning of the Here, for a straightforward way get a handle on the slider widget that controls the active frame, we'll use a DynamicMap that calls plot_image every time the slider value change.


```python
# Link function to create image from player widget frame value
def plot_image(value):
    return hv.Image(da.sel(frame=value), kdims=["width", "height"]).opts(
        title=f'frame = {value}',
        frame_height=da.sizes['height'],
        frame_width=da.sizes['width'],
        cmap = "Viridis",
        clim=(0,20),
        colorbar = True,
        tools=['hover', 'crosshair'],
        toolbar='right',
        scalebar=True,
        scalebar_unit=("µm", "m"), # each data bin is about 1 µm
        apply_hard_bounds=True,
        scalebar_opts={
        'background_fill_alpha': 0.5,
        'border_line_color': None,
        'bar_length': 0.10,
        }
    )

video_player = pn.widgets.Player(
    length =len(da.coords["frame"]),
    interval = 100,  # ms
    value = 250, # start frame
    height=90,
    loop_policy="loop",
    align='center',
)

main_view = hv.DynamicMap(pn.bind(plot_image, video_player.param.value_throttled))

# Frame Number Indicator
frame_reactive = pn.bind(lambda value: f'### frame: {value}', video_player.param.value)
frame_markdown = pn.pane.Markdown(object=frame_reactive)

# Max Over Time Overlay
max_proj_time = da.max('frame').compute().astype(np.float32)
img_max_proj_time = hv.Image(
    max_proj_time, ['width', 'height'], label='Max Over Time').opts(
    frame_height=da.sizes['height'],
    frame_width=da.sizes['width'],
    cmap='magma',
)
alpha_slider = pn.widgets.FloatSlider(start=0, end=1, step=.1, value=0.3, name='Alpha of Max Over Time', align='center')
alpha_slider.jslink(img_max_proj_time, value='glyph.global_alpha')

player_layout = pn.WidgetBox('## Playback', video_player, frame_markdown, horizontal=True, align='start')
alpha_slider_layout = pn.WidgetBox('## Max Overlay', alpha_slider, horizontal=True, align='start')
```

### Spatial Ranges Annotation Extension

We will now construct an annotator object that enables direct annotation of regions of spatial regions interest within the visual interface utilizing the HoloNote package.


```python
from holonote.annotate import Annotator
from holonote.app import PanelWidgets
from holonote.app.tabulator import AnnotatorTable

annotator = Annotator({"height": float, "width": float}, fields=["type"], groupby="type")
color_dim = hv.dim("type").categorize(
    categories={"A": "red", "B": "orange", "C": "cyan"}, default="grey"
)
annotator.style.color = color_dim
annotator.style.alpha=.5
panel_widgets = PanelWidgets(annotator)
table_widget = AnnotatorTable(annotator)
annotator_widgets = pn.WidgetBox('## Annotator', panel_widgets, table_widget, horizontal=True, align='start', scroll=True)
```

#### Link Annotations to Timeseries

Finally, we will display the mean timeseries of all the data in the annotated spatial regions.


```python
# Initialize the empty time series plot
curve_opts = dict(
    responsive=True,
    frame_height=da.sizes['height'],
    min_width=300,
    show_legend=False,
    xlabel='frame',
    tools=['hover'],
    line_alpha=.5,
    framewise=True,
    axiswise=True,
)

def plot_ts(event):
    curves = {}
    df = annotator.df
    for idx,row in df.iterrows():
        h1, h2, w1, w2 = row[["start[height]", "end[height]", "start[width]", "end[width]"]]
        da_sel = da.sel(height=slice(h1, h2), width=slice(w1, w2))
        group = f'G_{row['type']}'
        label = f'L_{idx[:6]}'
        curve = hv.Curve(da_sel.mean(["height", "width"]), group=group, label=label)
        curve = curve.opts(subcoordinate_y=True, color=panel_widgets.colormap[row['type']], **curve_opts)
        curves[(group, label)] = curve
    time_series.object = (vline * hv.Overlay(curves, kdims=['curve'])).opts(title='Annotated Mean Timeseries', xlim = (frames[0], frames[-1]))

annotator.on_event(plot_ts)

def plot_frame_indicator_line(value):
    if value:
        return hv.VSpans((value, value)).opts(axiswise=True, framewise=True)

vline_opts = dict(color="grey", line_width=4, fill_alpha=.5)
vline = hv.DynamicMap(pn.bind(plot_frame_indicator_line, video_player)).opts(**vline_opts)

frames = da.coords["frame"].values
time_series = pn.pane.HoloViews(vline * hv.Curve([]).opts(xlim = (frames[0], frames[-1]),
    title='Create an annotation in the image', **curve_opts))

cached_group_label = set([])

def highlight_last_selected(idx):
    if cached_group_label:
        last_group_label = cached_group_label.pop()
        reset_opts = hv.opts.Curve(last_group_label, line_alpha=0.5)
    else:
        reset_opts = hv.opts.Curve()
    
    # highlight alpha of selected curve
    if len(idx):
        idx = idx[-1]
        row = annotator.df.loc[idx]
        group = f'G_{row['type']}'
        label = f'L_{idx[:6]}'
        group_label = f"{group}.{label}"
        cached_group_label.add(group_label)
        time_series.object = time_series.object.opts(reset_opts, hv.opts.Curve(group_label, line_alpha=1))
    else:
        time_series.object = time_series.object.opts(reset_opts)

pn.bind(highlight_last_selected, annotator.param.selected_indices, watch=True)

main_view_overlay = main_view * img_max_proj_time * annotator
widgets = pn.WidgetBox(annotator_widgets, alpha_slider_layout, player_layout, align='center')

img_stack_app_annot = pn.Column(
    widgets,
    pn.Row(main_view_overlay, time_series)
)

img_stack_app_annot.servable()
```

### Future work: 
- Freehanddraw polygon annotation


```python

```
