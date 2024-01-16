from __future__ import annotations

if __name__ == "__main__":

    import bokeh
    bokeh.settings.settings.log_level = "trace"

    import sys
    from pathlib import Path
    script_directory = Path(__file__).parent
    sys.path.append(str(script_directory))
    from base import Base

else:
    from .base import Base

from functools import partial
from typing import TYPE_CHECKING

import holoviews as hv
import numpy as np
import panel as pn

if TYPE_CHECKING:
    from bokeh.document import Document

import holoviews as hv
import panel as pn

def app(doc: Document, n: int, output_backend: str):
    hv.renderer('bokeh').webgl = (output_backend == "webgl")

    # %% workflow code
    import numpy as np; np.random.seed(0)
    import pandas as pd
    from scipy.stats import zscore
    from holoviews.plotting.links import RangeToolLink
    from holoviews.operation.datashader import rasterize
    from holoviews import Dataset
    from bokeh.models import HoverTool

    # Generate data
    n_channels = 25
    n_seconds = n #15
    fs = 250  # Sampling frequency
    init_freq = 1  # Initial sine wave frequency in Hz
    freq_inc = 20/n_channels  # Frequency increment
    amplitude = 1
    total_samples = n_seconds * fs
    time = np.linspace(0, n_seconds, total_samples)
    channels = [f'EEG {i}' for i in range(n_channels)]
    data = np.array([amplitude * np.sin(2 * np.pi * (init_freq + i * freq_inc) * time)
                    for i in range(n_channels)])
    
    xzoom_out_extent = 2
    start_t_disp = 4.5 # start time of initially displayed window 
    max_t_disp = xzoom_out_extent # max time in seconds to initially display
    max_ch_disp = 20  # max channels to initially display
    max_y_disp = np.min((max_ch_disp - 1.5, n_channels - 1.5))
    subcoord_btm = -0.5 # auto lower xlim of first subcoord
    clim_mul = 1 # color limit multiplier.. adjusts the levels on the minimap

    hover = HoverTool(tooltips=[
        ("Channel", "@channel"),
        ("Time", "$x s"),
        ("Amplitude", "$y µV")])

    channel_curves = []
    for channel, channel_data in zip(channels, data):
        ds = Dataset((time, channel_data, channel), ["Time", "Amplitude", "channel"])
        curve = hv.Curve(ds, "Time", ["Amplitude", "channel"], label=f'{channel}')
        curve.opts(color="black", line_width=1, subcoordinate_y=True, tools=[hover])
        channel_curves.append(curve)

    curves = hv.Overlay(channel_curves, kdims="Channel")
    eeg_viewer = curves
    eeg_viewer = eeg_viewer.opts(
        xlabel="Time (s)", ylabel="Channel", show_legend=False,
        padding=0, aspect=1.5, responsive=True, shared_axes=False, framewise=False,
        #ylim does not work with subcoordinate_y
        # xlim=(start_t_disp, start_t_disp+max_t_disp), ylim=(subcoord_btm, subcoord_btm+max_y_disp),
        backend_opts={
            "y_range.start": subcoord_btm, # required as long as ylim doesn't work
            "y_range.end": subcoord_btm + max_y_disp, # required as long as ylim doesn't work
            "x_range.start": start_t_disp,
            "x_range.end": start_t_disp + max_t_disp,
            "x_range.bounds": (time.min(), time.max()), # absolute outer limits on pan/zoom
            "y_range.bounds": (0, len(channels)),
            "x_range.max_interval": xzoom_out_extent
        })

    y_positions = range(len(channels))
    yticks = [(i, ich) for i, ich in enumerate(channels)]
    z_data = zscore(data, axis=1)
    
    minimap = rasterize(hv.Image((time, y_positions, z_data), ["Time (s)", "Channel"], "Amplitude (uV)"))
    minimap = minimap.opts(
        cmap="RdBu_r", colorbar=False, xlabel='',
        alpha=.3, yticks=[yticks[0], yticks[-1]],
        toolbar='disable', # needed to prevent zoom and pan on image
        height=120, responsive=True, default_tools=[],
        clim=(-z_data.std()*clim_mul, z_data.std()*clim_mul))

    RangeToolLink(minimap, curves, axes=["x", "y"],
                boundsx=(start_t_disp, start_t_disp + max_t_disp), #required for reset behavior
                boundsy=(subcoord_btm, subcoord_btm + max_y_disp) #required for reset behavior
                )

    full_app = pn.Column((eeg_viewer + minimap).cols(1), min_height=650)

    # %% Trigger sending of the full_app
    def run_callback(run):
        if not run: # runs once at the beginning if using pn.bind
            # Initialize with an empty plot to trigger the initial paint and unblock the latency test
            # Make responsive so as not to limit the subsequent app dimensions
            return hv.Curve([]).opts(responsive=True)
        return full_app
    
    run_button = pn.widgets.Button(name='run')
    doc.add_root(pn.Column(pn.bind(run_callback, run=run_button), run_button).get_root(doc))


class multitimeseriesBase(Base):
    repeat = 1 # Force a single benchmark timing for each setup-teardown call.
    number = 1 # Force a single benchmark timing for each setup-teardown call.
    rounds = 2
    await_n_figs = 2 # IMPORTANT!! MAKE SURE THIS MATCHES NUMBER OF FIGURES IN APP

    params: tuple[list[int], list[str]] = (
        [15, 30, 60],
        ["canvas", "webgl"],
    )
    param_names: tuple[str] = ("n", "output_backend")

    def setup(self, n: int, output_backend: str) -> None:
        app_n = partial(app, n=n, output_backend=output_backend)
        self.playwright_setup(app_n)
        self.init_figure_id = self.current_figure_id()
        # drop the empty initialization figure_id from the dict
        self._render_counts_start.pop(self.current_figure_id())
        self._render_counts_end.pop(self.current_figure_id())
        if len(self._render_counts_start) != 0:
            raise RuntimeError("Expected empty render counts dict")
        self.page.wait_for_timeout(10)  # warmup

    def teardown(self, n: int, output_backend: str) -> None:
        self.figure_id = None
        self.playwright_teardown()

class multitimeseriesLatency(multitimeseriesBase):
    """measure latency which is the time taken to transfer data to the browser and render it. The browser and
    server are already running before the benchmark starts.
    """

    def time_latency(self, n: int, output_backend: str) -> None:
        self.multi_fig_click_button_and_wait_for_render("run", self.await_n_figs)

# class multitimeseriesZoom(multitimeseriesBase):
#     """measure the time taken for an
#     interactive render which is achieved here using by zooming the figure.
#     """
#     def setup(self, n: int, output_backend: str) -> None:
#         super().setup(n, output_backend)

#         # Render initial data set.
#         self.multi_fig_click_button_and_wait_for_render("run", self.await_n_figs)

#     def time_zoom(self, n: int, output_backend: str) -> None:
#         self.multi_fig_click_button_and_wait_for_render("zoom", self.figure_id)

if __name__ == "__main__":

    n = 15 # seconds of data
    backend = "webgl"

    init_latency = multitimeseriesLatency()
    init_latency.setup(n, backend)
    init_latency.time_latency(n, backend)
    init_latency.teardown(n, backend)

    # zoom_latency = multitimeseriesZoom()
    # zoom_latency.setup(n, backend)
    # zoom_latency.time_zoom(n, backend)
    # zoom_latency.teardown(n, backend)