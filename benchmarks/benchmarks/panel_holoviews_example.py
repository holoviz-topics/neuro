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

    def run_callback(click):
        return hv.Curve((x, y) if click else [])

    button = pn.widgets.Button(name='run')
    app = pn.Row(button, hv.DynamicMap(pn.bind(run_callback, button)))

    doc.add_root(app.get_root())


class PanelHoloviewsExample(Base):
    # Force a single benchmark timing for each setup-teardown call.
    repeat = 1
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

    def teardown(self, n: int, output_backend: str) -> None:
        self.figure_id = None
        self.playwright_teardown()

    def time_latency(self, n: int, output_backend: str) -> None:
        self.click_button_and_wait_for_render("run", self.figure_id)
