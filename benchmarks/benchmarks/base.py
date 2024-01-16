from __future__ import annotations

from typing import TYPE_CHECKING

from bokeh.models import Plot
from bokeh.server.server import Server
from playwright.sync_api import sync_playwright

import re

pattern = re.compile(r"FigureView\((\w+)\)._actual_paint (\d+) (start|end)")

# LOG_TIMING = False  # For validation. Set to True to print individual paint timings.

# import logging
# logging.basicConfig(filename='benchmark.log', level=logging.INFO)
# logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Callable
    from bokeh.document import Document
    from playwright.sync_api import ConsoleMessage

import socket
from contextlib import closing


class Base:
    repeat = 1  # Force a single benchmark timing for each setup-teardown call.
    number = 1  # Force a single benchmark timing for each setup-teardown call.
    warmup_time = 0

    def __init__(self, catch_console: bool = True):
        self._catch_console = catch_console
        self._port = self._find_free_port()

        # Dictionary of Bokeh figure ID to current render count.  Updated in _console_callback.
        # Do not read it directly, use render_count() function instead.
        self._render_counts_start: dict[str, int] = {}
        self._render_counts_end: dict[str, int] = {}

    def _find_free_port(self) -> int:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def _console_callback(self, msg: ConsoleMessage) -> None:
        match = pattern.search(msg.text)
        if not match:
            return
        figure_id, count, state = match.groups()
        count = int(count)
        if state == "start":
            self._render_counts_start[figure_id] = count
            # if LOG_TIMING:
            #     self.start_time = time.perf_counter()
            #     self.start_count = f'{figure_id}:{count}'
        if state == "end":
            # expected_render_count = self.render_count(figure_id) + 1
            # if count != expected_render_count:
            # raise RuntimeError(f"Mismatch in render count: {count} != {expected_render_count}")
            self._render_counts_end[figure_id] = count
            # if LOG_TIMING:
            #     end_time = time.perf_counter()
            #     end_count = f'{figure_id}:{count}'
            #     timing = f"START {self.start_count} ||| END {end_count}: {end_time - self.start_time}s"
            #     print(timing) # TODO: investigate mismatch between what ASV reports and this timing
            #     logger.info(timing) # logging not working with ASV

    def click_button_and_wait_for_render(
        self, button_name: str, figure_id: str
    ) -> None:
        # If benchmarking a single figure pure Bokeh plot and just adding data to the initialized plot
        # then it's fine to use this original approach of counting the renders of the identified figure.
        button = self.page.get_by_role("button", name=button_name)
        last_render_count = self.render_count("end", figure_id)
        # self.page.wait_for_timeout(self.warm_up_time)
        button.click()
        while self.render_count("end", figure_id) == last_render_count:
            self.page.wait_for_timeout(1)

    def multi_fig_click_button_and_wait_for_render(
        self, button_name: str, await_n_figs: int
    ) -> None:
        # Use this for multi figure benchmarks or in general when the figure IDs are not known ahead of time
        # for whatever reason (such as not using an initialized dynamicmap)
        if len(self._render_counts_end) > await_n_figs:
            raise RuntimeError(
                f"Too many figures rendered: {len(self._render_counts_end)} > {await_n_figs}"
            )

        initial_render_counts_end = self._render_counts_end.copy()
        incremented_items = set()
        button = self.page.get_by_role("button", name=button_name)
        button.click()

        while True:
            for fig_id, count in self._render_counts_end.items():
                # Skip if the fig_id is equal to init_figure_id
                if fig_id == self.init_figure_id:
                    continue
                # If the fig is new or its count has incremented, mark as incremented
                if (
                    fig_id not in initial_render_counts_end
                    or count > initial_render_counts_end.get(fig_id, -1)
                ):
                    incremented_items.add(fig_id)

            if len(incremented_items) == await_n_figs:
                break

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

        # alt approach, get multiple figure id's
        # figure = doc.select(dict(type=Plot))
        # figure = [f.id for f in figure]
        return figure.id

    def render_count(self, start_or_end, figure_id) -> int:
        if start_or_end == "start":
            return self._render_counts_start.get(figure_id, -1)
        elif start_or_end == "end":
            return self._render_counts_end.get(figure_id, -1)

    def playwright_setup(self, bokeh_doc: Callable[[Document], None]) -> None:
        # Playwright context manager needs to span multiple functions,
        # so manually call __enter__ and __exit__ methods.
        self._playwright_context_manager = sync_playwright()
        playwright = self._playwright_context_manager.__enter__()

        self._server = Server({"/": bokeh_doc}, port=self._port)
        self._server.start()

        self._browser = playwright.chromium.launch(headless=False)

        self.page = self._browser.new_page()

        if self._catch_console:
            self.page.on("console", self._console_callback)

        self.page.goto(f"http://localhost:{self._port}/")

        # await init render regardless of figure_id to confirm any data prep
        while len(self._render_counts_end) == 0:
            self.page.wait_for_timeout(1)

    def playwright_teardown(self):
        self.page.wait_for_timeout(1)  # debugging
        if self._catch_console:
            self.page.remove_listener("console", self._console_callback)
            # Wait a few milliseconds for emitted console messages to be handled before closing
            # browser. May need to increase this if Playwright complains that browser is closed.
            self.page.wait_for_timeout(100)
            self._render_counts_start.clear()
            self._render_counts_end.clear()

        self._browser.close()
        self._server.stop()
        self._playwright_context_manager.__exit__(None, None, None)
