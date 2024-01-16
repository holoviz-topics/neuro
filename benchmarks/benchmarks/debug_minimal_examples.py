# To be used for isolating and debugging the playwright and minimal app 
# execution without the display callbacks or parsing the console log

from __future__ import annotations
from functools import partial
from typing import Callable
from bokeh.document import Document
from bokeh.server.server import Server
from bokeh.plotting import column, figure
from bokeh.models import ColumnDataSource
from playwright.sync_api import sync_playwright
import numpy as np
import panel as pn
import holoviews as hv; hv.extension('bokeh')

# Minimal Panel/HoloViews app
def pnapp(doc: Document, n: int):
    x = np.linspace(0, 1, n)
    y = np.random.default_rng(8343).uniform(size=n)
    doc.add_root(pn.Column(hv.Curve((x, y)).opts(width=400, height=400)).get_root(doc))

# Minimal Bokeh app
def bkapp(doc: Document, n: int):
    x = np.arange(n)
    y = np.random.default_rng(8343).uniform(size=n)
    cds = ColumnDataSource(data=dict(x=x, y=y))
    p = figure(width=400, height=400)
    p.line(source=cds, x="x", y="y")
    doc.add_root(column(p))

class PanelHoloviewsExampleBase:
    def __init__(self):
        self._port = 5012

    def setup(self, bokeh_doc: Callable[[Document], None]):
        self._playwright_context_manager = sync_playwright()
        self._playwright = self._playwright_context_manager.__enter__()

        self._server = Server({'/': bokeh_doc}, port=self._port)
        self._server.start()

        self._browser = self._playwright.chromium.launch(headless=False)
        self._page = self._browser.new_page()
        self._page.goto(f"http://localhost:{self._port}/")

    def teardown(self):
        self._page.wait_for_timeout(1000)
        self._server.stop()
        self._browser.close()
        self._playwright_context_manager.__exit__(None, None, None)

if __name__ == "__main__":
    ns = [100, 500]

    for app in [bkapp, pnapp]:
        for n in ns:
            benchmark = PanelHoloviewsExampleBase()
            benchmark.setup(partial(app, n=n))
            benchmark.teardown()
