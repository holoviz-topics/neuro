from __future__ import annotations

from typing import TYPE_CHECKING

from bokeh.models import Plot
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
        self._figure_id = None  # Unique ID of the figure to grab the console messages of.

    def _console_callback(self, msg: ConsoleMessage) -> None:
        if self._figure_id is None or len(msg.args) != 4:
            return

        args = [arg.json_value() for arg in msg.args]

        if args[0] == "PlotView._actual_paint" and args[1] == self._figure_id:
            if args[3] == "start":
                # TODO: need to handle start of render if want to time a single render.
                pass
            elif args[3] == "end":
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

        # Assume Bokeh document contains a single figure, and obtain its ID.
        sessions = self._server.get_sessions()
        if len(sessions) != 1:
            raise RuntimeError(f"Expected a single session but have {len(sessions)}")
        doc = sessions[0].document
        # This raises an error if there is more than one figure in the Bokeh document.
        self._figure_id = doc.select_one(dict(type=Plot)).id

        if catch_console:
            self.page.on("console", self._console_callback)

    def _playwright_teardown(self):
        self._figure_id = None
        self._browser.close()
        self._server.stop()
        self._playwright_context_manager.__exit__(None, None, None)
