from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import holoviews as hv
import numpy as np
import panel as pn

from .base import Base

if TYPE_CHECKING:
    from bokeh.document import Document

def pnapp(doc: Document, n: int, output_backend: str):
    hv.renderer('bokeh').webgl = (output_backend == "webgl")
    x = np.linspace(0, 1, n)
    y = np.random.default_rng(8343).uniform(size=n)

    # Get ranges to set initial viewport to 1/10th of the data's range
    x_start = x[0]
    x_end = x_start + (x[-1] - x_start) / 10
    maxy = max(y)
    y_start = min(y)
    y_end = y_start + (maxy - y_start) / 10

    def run_zoom_callback(run, zoom):
        if not zoom:
            # start at 1/10th of the range
            return hv.Curve((x, y) if run else []).opts(
                xlim=(x_start, x_end), ylim=(y_start, y_end),
                framewise=True)
        
        return hv.Curve((x, y)).opts( # zoom out to full data range
            xlim=(x_start, x[-1]), ylim=(y_start, maxy), framewise=True)

    run_button = pn.widgets.Button(name='run') # always clicked first
    zoom_button = pn.widgets.Button(name='zoom')

    dynmap = hv.DynamicMap(pn.bind(run_zoom_callback,
                                   run=run_button,
                                   zoom=zoom_button))

    app = pn.Column(dynmap, pn.Row(run_button, zoom_button))

    doc.add_root(app.get_root())

class PanelHoloviewsExampleBase(Base):
    repeat = 1 # Force a single benchmark timing for each setup-teardown call.
    rounds = 5

    params: tuple[list[int], list[str]] = (
        [1_000, 10_000, 100_000, 1_000_000],
        ["canvas", "webgl"],
    )
    param_names: tuple[str] = ("n", "output_backend")

    def setup(self, n: int, output_backend: str) -> None:
        pnapp_n = partial(pnapp, n=n, output_backend=output_backend)
        self.playwright_setup(pnapp_n)

        # There is only a single Bokeh figure in each benchmark so store its ID here rather than
        # in the benchmark itself.
        self.figure_id = self.current_figure_id()
        self.page.wait_for_timeout(10) # warmup

    def teardown(self, n: int, output_backend: str) -> None:
        self.figure_id = None
        self.playwright_teardown()

class PanelHoloviewsExampleLatency(PanelHoloviewsExampleBase):
    """Example benchmark using Panel and HoloViews, measuring the latency which is the
    time taken to transfer data to the browser and render it. The browser and
    Bokeh server are already running before the benchmark starts.
    """
    def time_latency(self, n: int, output_backend: str) -> None:
        self.click_button_and_wait_for_render("run", self.figure_id)

class PanelHoloviewsExampleZoom(PanelHoloviewsExampleBase):
    """Example benchmark using Panel and HoloViews, measuring the time taken for an
    interactive render which is achieved here using by zooming the figure.
    """
    def setup(self, n: int, output_backend: str) -> None:
        super().setup(n, output_backend)

        # Render initial data set.
        self.click_button_and_wait_for_render("run", self.figure_id)

    def time_zoom(self, n: int, output_backend: str) -> None:
        self.click_button_and_wait_for_render("zoom", self.figure_id)