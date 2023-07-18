from __future__ import annotations

from typing import TYPE_CHECKING

from bokeh.server.server import Server
from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from typing import Callable

    from bokeh.document import Document
    from playwright.sync_api import ConsoleMessage


class Base:
    def __init__(self):
        self._port = 5006
        self.render_count = -1

    def _console_callback(self, msg: ConsoleMessage) -> None:
        # Only supports a single Bokeh canvas so far.
        args = msg.args
        if len(args) == 3 and args[0].json_value() == "PlotView._actual_paint" and args[2].json_value() == "end":
            self.render_count += 1
            count = int(args[1].json_value())
            if count != self.render_count:
                raise RuntimeError(f"Mismatch in render count: {count} != {self.render_count}")

    def _playwright_setup(self, bokeh_doc: Callable[[Document], None], catch_console: bool) -> None:
        # Playwright context manager needs to span multiple functions,
        # so manually call __enter__ and __exit__ methods.
        self._playwright_context_manager = sync_playwright()
        playwright = self._playwright_context_manager.__enter__()

        self._server = Server({'/': bokeh_doc}, port=self._port)
        self._server.start()

        self._browser = playwright.chromium.launch(headless=True)

        self.page = self._browser.new_page()
        self.page.goto(f"http://localhost:{self._port}/")

        if catch_console:
            self.page.on("console", self._console_callback)

    def _playwright_teardown(self):
        self._browser.close()
        self._server.stop()
        self._playwright_context_manager.__exit__(None, None, None)
