


from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from bokeh.models import Button, ColumnDataSource
from bokeh.plotting import column, figure, row
import numpy as np

from .base import Base

if TYPE_CHECKING:
    from bokeh.document import Document


def bkapp(doc: Document, n: int, output_backend: str):
    cds = ColumnDataSource(data=dict(x=[], y=[]))

    p = figure(width=600, height=400, output_backend=output_backend)
    p.line(source=cds, x="x", y="y")

    # Prepare data but do not send it to browser yet.
    x = np.arange(n)
    y = np.random.default_rng(8343).uniform(size=n)

    def run_callback(event):
        # Latency benchmark times the sending and rendering of this data.
        cds.data = dict(x=x, y=y)

    run_button = Button(label="run")
    run_button.on_click(run_callback)

    def zoom_callback(event):
        # Zoom benchmark times the render caused by this zoom.
        p.x_range.start = 500

    zoom_button = Button(label="zoom")
    zoom_button.on_click(zoom_callback)

    doc.add_root(column(p, row(run_button, zoom_button)))


class TimeseriesBase(Base):
    params: tuple[list[int], list[str]] = (
        [1_000, 10_000, 100_000, 1_000_000],
        ["canvas", "webgl"],
    )
    param_names: tuple[str] = ("n", "output_backend")

    def setup(self, n: int, output_backend: str) -> None:
        bkapp_n = partial(bkapp, n=n, output_backend=output_backend)
        self.playwright_setup(bkapp_n)

        # There is only a single Bokeh figure in each benchmark so store its ID here rather than
        # in the benchmark itself.
        self.figure_id = self.current_figure_id()

    def teardown(self, n: int, output_backend: str) -> None:
        self.figure_id = None
        self.playwright_teardown()


class TimeseriesLatency(TimeseriesBase):
    """Example benchmark using Bokeh only, measuring the latency which is the
    time taken to transfer data to the browser and render it. The browser and
    Bokeh server are already running before the benchmark starts.
    """
    def time_latency(self, n: int, output_backend: str) -> None:
        self.click_button_and_wait_for_render("run", self.figure_id)


class TimeseriesZoom(TimeseriesBase):
    """Example benchmark using Bokeh only, measuring the time taken for an
    interactive render which is achieved here using by zooming the figure.
    """
    def setup(self, n: int, output_backend: str) -> None:
        super().setup(n, output_backend)

        # Render initial data set.
        self.click_button_and_wait_for_render("run", self.figure_id)

    def time_zoom(self, n: int, output_backend: str) -> None:
        self.click_button_and_wait_for_render("zoom", self.figure_id)
