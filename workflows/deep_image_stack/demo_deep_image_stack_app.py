# -----------------------------------------------------------------------------
# Imports and Extensions
# -----------------------------------------------------------------------------

from pathlib import Path
import numpy as np
import xarray as xr
import holoviews as hv
from holoviews.operation.datashader import rasterize
import panel as pn
import fsspec

from holonote.annotate import Annotator
from holonote.app import PanelWidgets
from holonote.app.tabulator import AnnotatorTable

pn.extension('tabulator')
hv.extension('bokeh')

# -----------------------------------------------------------------------------
# Data Loading and Preparation
# -----------------------------------------------------------------------------

DATA_URL = 'https://datasets.holoviz.org/miniscope/v1/real_miniscope_uint8.zarr/'
DATA_DIR = Path('./data')
DATA_FILENAME = Path(DATA_URL).name
DATA_PATH = DATA_DIR / DATA_FILENAME
print(f'Local Original Data Path: {DATA_PATH}')

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Check if local directory exists
if not DATA_PATH.exists():
    print(f'Downloading data to: {DATA_PATH}')
    # Open the remote dataset and save it locally
    ds_remote = xr.open_dataset(
        fsspec.get_mapper(DATA_URL), engine='zarr', chunks={}
    )
    ds_remote.to_zarr(str(DATA_PATH))  # Save locally
    print(f'Dataset downloaded to: {DATA_PATH}')
else:
    print(f'Data already exists locally at: {DATA_PATH}')

# Open the dataset from the local copy
ds = xr.open_dataset(
    DATA_PATH.as_posix(),
    engine='zarr',
    chunks={'frame': 400, 'height': -1, 'width': -1}
)

# Access the variable 'varr_ref'
da = ds['varr_ref']

# -----------------------------------------------------------------------------
# Image Visualization Functions
# -----------------------------------------------------------------------------

def plot_image(value):
    """Creates a HoloViews Image object for a single frame with custom styling and interactions"""
    return hv.Image(
        da.sel(frame=value),
        kdims=["width", "height"],
    ).opts(
        title=f"frame = {value}",
        frame_height=da.sizes["height"],
        frame_width=da.sizes["width"],
        cmap="Viridis",
        clim=(0, 20),
        colorbar=True,
        tools=["hover", "crosshair"],
        toolbar="right",
        apply_hard_bounds=True,
        scalebar=True,
        scalebar_unit=("µm", "m"),
        scalebar_opts={
            "background_fill_alpha": 0.5,
            "border_line_color": None,
            "bar_length": 0.10,
        },
    )

# -----------------------------------------------------------------------------
# Maximum Projection Overlay
# -----------------------------------------------------------------------------

max_proj_time = da.max("frame").compute().astype(np.float32)
img_max_proj_time = hv.Image(
    max_proj_time, ["width", "height"], label="Max Over Time"
).opts(cmap="magma")

# -----------------------------------------------------------------------------
# Interactive Controls
# -----------------------------------------------------------------------------

video_player = pn.widgets.Player(
    length=len(da.coords["frame"]),
    interval=100,
    value=250,
    show_loop_controls=False,
    align="center",
    scale_buttons=0.9,
    sizing_mode="stretch_width",
    show_value=True,
    value_align="center",
    visible_buttons=["slower", "previous", "pause", "play", "next", "faster"],
)

alpha_slider = pn.widgets.FloatSlider(
    start=0, end=1, step=0.1, value=0.3, name="Opacity", align="center", sizing_mode="stretch_width"
)

frame_dmap = hv.DynamicMap(pn.bind(plot_image, video_player.param.value_throttled))
alpha_slider.jslink(img_max_proj_time, value="glyph.global_alpha")

# -----------------------------------------------------------------------------
# Layout Components
# -----------------------------------------------------------------------------

player_layout = pn.Card(video_player, title="Playback", sizing_mode="stretch_width", margin=(0, 0, 20, 0))
alpha_slider_layout = pn.Card(alpha_slider, title="Max Projection Overlay", sizing_mode="stretch_width", margin=(0, 0, 20, 0))

main_view = frame_dmap * img_max_proj_time
widgets = pn.Column(player_layout, alpha_slider_layout, align="center", width=350)

side_view_opts = dict(cmap="greys_r", tools=['crosshair', 'hover'], axiswise=True, apply_hard_bounds=True, colorbar=False, toolbar=None)
top_data = da.mean(["height"]).persist()
top_view = rasterize(hv.Image(top_data, kdims=["width", "frame"]).opts(frame_height=175, frame_width=da.sizes['width'], title="Top Side View", xaxis='top', **side_view_opts))
right_data = da.mean(["width"]).persist()
right_view = rasterize(hv.Image(right_data, kdims=["frame", "height"]).opts(frame_height=da.sizes['height'], title="Right Side View", yaxis='right', **side_view_opts))

# -----------------------------------------------------------------------------
# Cross-sectional Overlay Lines
# -----------------------------------------------------------------------------

def plot_hline(value, x_range, y_range):
    if x_range is None:
        x_range = [int(da.width[0].values), int(da.width[-1].values)]
    return hv.Segments((x_range[0], value, x_range[1], value)).opts(axiswise=True)

def plot_vline(value, x_range, y_range):
    if y_range is None:
        y_range = [int(da.height[0].values), int(da.height[-1].values)]
    return hv.Segments((value, y_range[0], value, y_range[1])).opts(axiswise=True)

line_opts = dict(color="red", line_width=3, line_alpha=0.4, line_dash='dashed')
xyrange_stream = hv.streams.RangeXY(source=main_view)
dmap_hline = hv.DynamicMap(pn.bind(plot_hline, video_player), streams=[xyrange_stream]).opts(**line_opts, **side_view_opts)
dmap_vline = hv.DynamicMap(pn.bind(plot_vline, video_player), streams=[xyrange_stream]).opts(**line_opts, **side_view_opts)

top_view_overlay = (top_view * dmap_hline).opts(axiswise=True)
right_view_overlay = (right_view * dmap_vline).opts(axiswise=True)

# -----------------------------------------------------------------------------
# Annotation Configuration
# -----------------------------------------------------------------------------

annotator = Annotator({"height": float, "width": float}, fields=["type"], groupby="type")
color_dim = hv.dim("type").categorize(categories={"A": "red", "B": "orange", "C": "cyan"}, default="grey")
annotator.style.color = color_dim
annotator.style.alpha = 0.3

# -----------------------------------------------------------------------------
# Annotation Interface Components
# -----------------------------------------------------------------------------

panel_widgets = PanelWidgets(annotator)
table_widget = AnnotatorTable(annotator, tabulator_kwargs={"sizing_mode": "stretch_width", "theme": "midnight", "layout": "fit_columns", "sortable": False, "stylesheets": [":host .tabulator {font-size: 9px;}"]})
annotator_widgets = pn.Card(pn.Column(panel_widgets, table_widget), title="Annotator", sizing_mode="stretch_width", margin=(0, 0, 20, 0), collapsed=False)

# -----------------------------------------------------------------------------
# Timeseries Visualization Options and Plotting Functions
# -----------------------------------------------------------------------------

curve_opts = dict(responsive=True, min_height=300, max_height=600, show_legend=False, xlabel="frame", tools=["hover"], line_alpha=0.5, framewise=True, axiswise=True)
vline_opts = dict(color="grey", line_width=4, alpha=0.5)

def plot_ts(event):
    """Creates timeseries plots for each annotated region, showing mean intensity over time"""
    curves = {}
    df = annotator.df

    for idx, row in df.iterrows():
        h1, h2, w1, w2 = row[["start[height]", "end[height]", "start[width]", "end[width]"]]
        da_sel = da.sel(height=slice(h1, h2), width=slice(w1, w2))
        mean_ts = da_sel.mean(["height", "width"])
        group = f"G_{row['type']}"
        label = f"L_{idx[:6]}"
        curve = hv.Curve(mean_ts, group=group, label=label).opts(subcoordinate_y=True, color=panel_widgets.colormap[row["type"]], **curve_opts)
        curves[(group, label)] = curve

    time_series.object = vline * hv.Overlay(curves, kdims=["curve"]).opts(hv.opts.Curve(xlim=(frames[0], frames[-1])))

def plot_frame_indicator_line(value):
    """Creates vertical line indicating current frame position"""
    if value:
        return hv.VSpans((value, value)).opts(axiswise=True, framewise=True, **vline_opts)

# -----------------------------------------------------------------------------
# Initialize Plot Components
# -----------------------------------------------------------------------------

frames = da.coords["frame"].values
vline = hv.DynamicMap(pn.bind(plot_frame_indicator_line, video_player)).opts(hv.opts.VLine(**vline_opts))
time_series = pn.pane.HoloViews(vline * hv.Curve([]).opts(xlim=(frames[0], frames[-1]), title="Create an annotation in the image", **curve_opts))

# Connect annotation events to plotting function
annotator.on_event(plot_ts)

# -----------------------------------------------------------------------------
# Layout Assembly
# -----------------------------------------------------------------------------

main_view_overlay = main_view * annotator
widgets.append(annotator_widgets)
main_layout = pn.Column(top_view_overlay * annotator, pn.Row(main_view_overlay, right_view_overlay * annotator), time_series)

img_stack_app_annot = pn.Row(widgets, main_layout, align='start')

# -----------------------------------------------------------------------------
# Standalone Application Configuration
# -----------------------------------------------------------------------------

standalone_app = pn.template.FastListTemplate(
    title="Deep Image Stack App with Timeseries of Spatial Annotation",
    sidebar=[widgets], sidebar_width=350,
    main=[main_layout], main_layout=None,
    theme="dark", accent="#30023f"
).servable()
