from __future__ import annotations

from typing import TYPE_CHECKING

from bokeh.models import Plot
from bokeh.server.server import Server
from playwright.sync_api import sync_playwright

import time

import re
pattern = re.compile(r".*PlotView\._actual_paint (\w+) (\d+) (start|end)")

LOG_TIMING = False # For validation. Set to True to print individual paint timings. Doesn't seem to be working yet.

# import logging
# logging.basicConfig(filename='benchmark.log', level=logging.INFO)
# logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Callable
    from bokeh.document import Document
    from playwright.sync_api import ConsoleMessage

class Base:
    number = 1
    warmup_time = 0

    def __init__(self, catch_console: bool = True):
        self._catch_console = catch_console
        self._port = 5007

        # Dictionary of Bokeh figure ID to current render count.  Updated in _console_callback.
        # Do not read it directly, use render_count() function instead.
        self._render_counts: dict[str, int] = {}

    def _console_callback(self, msg: ConsoleMessage) -> None:       
        match = pattern.search(msg.text)
        if not match:
            return
        
        figure_id, count, state = match.groups()
        if state == "start":
            if not LOG_TIMING:
                pass
            self.start_time = time.perf_counter()
            self.start_count = f'{figure_id}:{count}'
        elif state == "end":
            expected_render_count = self.render_count(figure_id) + 1
            count = int(count)
            if count != expected_render_count:
                raise RuntimeError(f"Mismatch in render count: {count} != {expected_render_count}")
            self._render_counts[figure_id] = count

            if LOG_TIMING:
                end_time = time.perf_counter()
                end_count = f'{figure_id}:{count}'
                timing = f"START {self.start_count} ||| END {end_count}: {end_time - self.start_time}s"
                print(timing) # TODO mismatch between what ASV reports and this timing.
                # logger.info(timing) # logging doesn't seem to work with ASV

    def click_button_and_wait_for_render(self, button_name: str, figure_id: str) -> None:
        button = self.page.get_by_role("button", name=button_name)
        last_render_count = self.render_count(figure_id)
        # self.page.wait_for_timeout(self.warm_up_time)
        button.click()
        while self.render_count(figure_id) == last_render_count:
            self.page.wait_for_timeout(1)

    def current_figure_id(self) -> str:
        """Return the id of the currently displayed Bokeh figure.

        Assumes the current bokeh document contains a single figure.
        """
        sessions = self._server.get_sessions()
        if len(sessions) != 1:
            raise RuntimeError(f"Expected a single session but have {len(sessions)}")
        doc = sessions[0].document
        # This raises an error if more or fewer than one figure in the Bokeh document.
        figure = doc.select_one(dict(type=Plot))
        return figure.id

    def render_count(self, figure_id) -> int:
        return self._render_counts.get(figure_id, -1)

    def playwright_setup(self, bokeh_doc: Callable[[Document], None]) -> None:
        # Playwright context manager needs to span multiple functions,
        # so manually call __enter__ and __exit__ methods.
        self._playwright_context_manager = sync_playwright()
        playwright = self._playwright_context_manager.__enter__()

        self._server = Server({'/': bokeh_doc}, port=self._port)
        self._server.start()

        self._browser = playwright.chromium.launch(headless=False)

        self.page = self._browser.new_page()
        self.page.goto(f"http://localhost:{self._port}/")

        if self._catch_console:
            self.page.on("console", self._console_callback)

        # Wait for first render regardless of figure_id.
        while len(self._render_counts) == 0:
            self.page.wait_for_timeout(1)

    def playwright_teardown(self):
        # self.page.wait_for_timeout(1) # debugging
        if self._catch_console:
            self.page.remove_listener("console", self._console_callback)
            # Wait a few milliseconds for emitted console messages to be handled before closing
            # browser. May need to increase this if Playwright complains that browser is closed.
            self.page.wait_for_timeout(10)
            self._render_counts.clear()

        self._browser.close()
        self._server.stop()
        self._playwright_context_manager.__exit__(None, None, None)
