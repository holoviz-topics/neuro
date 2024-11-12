# Deep Image Stack

<img src='./assets/2024-06-27_DeepImageStack.png' alt="Deep Image Stack App" align="right">

## Overview

This workflow is designed for processing and analyzing deep image stacks, which are sequences of images typically used in neuroscience for visualizing a two-dimensional slice of neural tissue over time. Each frame in the stack usually corresponds to a concurrent time sample, capturing dynamic processes. For example, a dynamic process of interest could be [neural action potentials](https://en.wikipedia.org/wiki/Action_potential), and the data might come from a [miniature microscope](http://miniscope.org/) that is capturing the change in fluouresence of special proteins caused by electrochemical fluctuations that are indicative of neuronal activity. This workflow provides a scalable solution for handling large and intricate datasets, enabling efficient navigation and analysis.

### What Defines a **'Deep Image Stack'**?
In this context, a deep image stack is a collection of images that represent different slices of a specimen at various time points, like a video (although this concept can be extended apply to image slices at different depths in a three-dimensional structure). These movie-datasets often contain many more frames in the 'Time' dimension compared to the number of pixels in the height or width of each individual image, necessitating specific handling techniques and motivating the 'Deep' moniker.

### Managing **'Large'** Deep Image Stacks
Although we will use a smaller dataset, we will demonstrate an approach that can be applied to larger stacks that exceed available memory or browser ability. Our scalable strategy involves dynamic loading of chunks of frames using the key software below.

### Key Software
Alongside [HoloViz](https://github.com/holoviz), [Bokeh](https://holoviz.org/), and several other foundational packages, we make extensive use of key open source libraries to implement our solution, such as:

- **[Xarray](https://github.com/pydata/xarray):** Manages labeled multi-dimensional data, facilitating complex data operations and enabling partial data loading for out-of-core computation.
- **[Dask](https://github.com/dask/dask):** Adds parallel computing capabilities, managing tasks that exceed memory limits.
- **[Zarr](https://github.com/zarr-developers/zarr-python):** Used behind the scenes for storing the large arrays of the data pyramid on disk in a compressed, chunked, and memory-mappable format, which is crucial for efficient data retrieval.


## Prerequisites and Resources

| Topic | Type | Notes |
| --- | --- | --- |
| [Xarray Tutorial](https://tutorial.xarray.dev/overview/xarray-in-45-min) | Prerequisite | Essential introduction to working with xarray data |
| [Minian Repository](https://github.com/denisecailab/minian?tab=readme-ov-file) | Resource | Analysis pipeline and visualization tool for Miniscope data |
| [Miniscope Wiki](http://miniscope.org/index.php/Main_Page) | Resource | Further context for the demo application |

## Imports and Configuration


```python
from pathlib import Path
import numpy as np
import xarray as xr
import holoviews as hv
from holoviews.streams import Stream
from holoviews.operation.datashader import rasterize
from hvplot import xarray
import panel as pn
import warnings
import re

pn.extension()
hv.extension('bokeh')

import warnings
warnings.filterwarnings("ignore", message=("Numba: Attempted to fork from a non-main thread*")) # using hv.output
```

## Loading and Inspecting the Data

Let's read the data in chunks, emulating a situation where a dataset is too large to fit into memory. Utilizing the `chunks` parameter in `xr.open_dataset` is crucial for efficient data handling with large datasets, as it enables Dask to process the data in manageable portions.


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

Visualizing calcium imaging data effectively is key to extracting meaningful insights. We introduce various visualization approaches to cater to different analysis needs.

We will start with one-liner viewer and then proceed to a more advanced application with enhanced interactive features and exposed controls, at the expense of code complexity.

### One-line hvPlot Application

We can use one line with `hvPlot` for a quick inspection of the deep image stack.


```python
hvPlot_app = da.hvplot.image(
    groupby="frame",
    title='hvPlot App',
    cmap='viridis',
    clim=(0,20),
    aspect=da.sizes['width'] / da.sizes['height'],
    widget_location='bottom'
)
hvPlot_app
```

To easily enrich and extend this one-line app, we do things like add a maximum-projection image so we can see the maximum fluorescence per pixel and visually locate the potential neurons in two-dimensions.


```python
max_proj = da.max('frame').compute().astype(np.float32)
img_max_proj = max_proj.hvplot.image(title='Max Over Time', cmap="magma", clim=(0,20), aspect=da.sizes['width'] / da.sizes['height'])

pn.Row(hvPlot_app, img_max_proj)
```

This was a quick way to see one frame at a time! But it looks like there are a lot of fluorescent blobs (candidate neurons) in the 'Max Over Time' image and now we want a quick way to visually locate and navigate to the relevant frames in the image stack.

### Enhanced HoloViews and Panel App

As our data array is a three-dimensional volume, let's create a more advanced application using `HoloViews` in place of `hvPlot` to handle the added complexity, and `Panel` for more control over the layout and interactive links.

This more advanced app builds on the previous one with added functionality, such as.

1. **Side Views**: Aggregated side views for display over 'deep' time dimension.
2. **Synchronized Frame Indicators**: Frame markers on the Side Views synchronized with the playback and x,y range of the main image stack view.
4. **Slider Overlay Alpha**: Slider widget to adjust transparency of max-over-time overlay for direct comparison and a tighter layout.
5. **Scale Bar**: A dynamic and customizable visual reference for spatial scale.
3. **Continuous Playback**: Player widget for continuous playback, along with controls for step-by-step examination of the image stack.

#### Main View

First, we define a function to create the main frame-wise view (height by width). Just as a demo, we'll call the function with a frame value. Here we'll also enable and configure a [dynamic scalebar](https://holoviews.org/reference/features/bokeh/Scalebar.html).


```python
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
plot_image(250)
```

#### Frame Player Widget

Next, we'll create a player widget to control the playback of our image stack:


```python
video_player = pn.widgets.Player(
    length =len(da.coords["frame"]),
    interval = 100,  # ms
    value = 250, # start frame
    height=90,
    loop_policy="loop",
    align='center',
)
```

We will `bind` (see [relevant Panel docs](https://panel.holoviz.org/explanation/api/reactivity.html)) the main frame-wise view to the player widget. Using [`DynamicMap`](https://holoviews.org/reference/containers/bokeh/DynamicMap.html), we ensure that only the plot contents are updated, maintaining the zoom level and other plot settings across updates. Additionally, by binding to [`value_throttled`](https://panel.holoviz.org/explanation/components/components_overview.html#throttling), we update the frame only when the user releases the slider, which improves performance by avoiding unnecessary updates:


```python
main_view = hv.DynamicMap(pn.bind(plot_image, video_player.param.value_throttled))
```

We'll also add a simple textual frame indicator that will be responsive to the player widget's value.


```python
frame_reactive = pn.bind(lambda value: f'### frame: {value}', video_player.param.value)
frame_markdown = pn.pane.Markdown(object=frame_reactive)
```

#### Max Over Time Overlay on the Main View

We now create a max time-projected image and a slider widget to adjust the transparency of this overlay. As before, the max projection helps in identifying areas of interest by showing the maximum value over time for each pixel. We'll use a fast [`jslink`](https://panel.holoviz.org/how_to/links/jslinks.html) approach to link to the slider to the opacity parameter of the image since this is a simple visual property update.


```python
max_proj_time = da.max('frame').compute().astype(np.float32)
img_max_proj_time = hv.Image(
    max_proj_time, ['width', 'height'], label='Max Over Time').opts(
    frame_height=da.sizes['height'],
    frame_width=da.sizes['width'],
    cmap='magma',
)
alpha_slider = pn.widgets.FloatSlider(start=0, end=1, step=.1, value=0.1, name='Alpha of Max Over Time', align='center')
alpha_slider.jslink(img_max_proj_time, value='glyph.global_alpha')
```

#### Side Views

We also need to create rasterized side views. The right-side view (as if looking at our 3D volume from the right side) will be a frame-by-height view, and the top-side view will be a width-by-frame view. Using `.persist()` (see [relevant Xarray docs](https://docs.xarray.dev/en/stable/user-guide/dask.html#using-dask-with-xarray) allows us to cache the results of the mean calculations, reducing recomputation and improving performance. `Rasterizing` these views helps to limit the amount of data sent to the browser, ensuring efficient rendering (see [relevant HoloView's docs](https://holoviews.org/user_guide/Large_Data.html)):


```python
side_view_opts = dict(
    cmap = "Viridis",
    tools=['crosshair', 'hover'],
    axiswise=True,
    apply_hard_bounds=True,
    colorbar=False,
    toolbar=None,
)

top_data = da.mean(["height"]).persist()
top_view = rasterize(
    hv.Image(top_data, kdims=["width", "frame"]).opts(
        frame_height=175,
        frame_width=da.sizes['width'],
        title= "Top Side View",
        xaxis='top',
        **side_view_opts
    )
)

right_data = da.mean(["width"]).persist()
right_view = rasterize(
    hv.Image(right_data, kdims=["frame", "height"]).opts(
        frame_height=da.sizes['height'],
        title="Right Side View",
        yaxis='right',
        **side_view_opts
    )
)
top_view + right_view
```

### Add Interactivity to the Side Views

We also add frame indicator lines on the side view plots that are synchronized with the main view in two ways. First, the position of these lines indicates the current frame and is linked to the video_player value. Instead of using throttled updates for the frame indicator lines, we `bind` directly to the unthrottled value of the video player since this is a computationally inexpensive operation. This decision ensures that the frame indicators follow the slider in real-time, providing a smooth and responsive user experience as the user scrubs through the frames. Second, the extents of the indicator lines adjust dynamically as the user interacts with the range (zoom, pan) in the main plot. To achieve this, we use a `streams.RangeXY` from HoloViews, which allows us to subscribe the indicator line extents to the range of the main view plot.


```python
def plot_hline(value, x_range, y_range):
    if x_range == None:
        x_range = [int(da.width[0].values), int(da.width[-1].values)]
    return hv.Segments((x_range[0], value, x_range[1], value)).opts(axiswise=True)

def plot_vline(value, x_range, y_range):
    if y_range == None:
        y_range = [int(da.height[0].values), int(da.height[-1].values)]
    return hv.Segments((value, y_range[0], value, y_range[1])).opts(axiswise=True)

line_opts = dict(color="red", line_width=5, line_alpha=.5, line_dash='dashed', line_cap='round')
xyrange_stream = hv.streams.RangeXY(source=main_view)
dmap_hline = hv.DynamicMap(pn.bind(plot_hline, video_player), streams=[xyrange_stream]).opts(**line_opts, **side_view_opts)
dmap_vline = hv.DynamicMap(pn.bind(plot_vline, video_player), streams=[xyrange_stream]).opts(**line_opts, **side_view_opts)
```

#### Layout
Finally, we lay out the components to create the complete application. This layout includes the top view, main view with overlay, side view, and control widgets. We set `axiswise=True` to prevent the side views from adjusting to the range of the main view, as we want them to be stable references of the full range on their respective axes.


```python
top_view_overlay = (top_view * dmap_hline).opts(axiswise=True)
right_view_overlay = (right_view * dmap_vline).opts(axiswise=True)
main_view_overlay = main_view * img_max_proj_time
main_and_right_layout = pn.Row(main_view_overlay, right_view_overlay)
player_layout = pn.WidgetBox(video_player, frame_markdown, horizontal=True, align='center')
alpha_slider_layout = pn.WidgetBox(alpha_slider, align='center')

img_stack_app = pn.Column(
    top_view_overlay,
    main_and_right_layout,
    alpha_slider_layout,
    player_layout,
)

img_stack_app.servable()
```


```python

```
