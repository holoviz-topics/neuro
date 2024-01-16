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
import panel as pn
from bokeh.models import Plot

if TYPE_CHECKING:
    from bokeh.document import Document

def app(doc: Document, n: int, output_backend: str):
    hv.renderer("bokeh").webgl = output_backend == "webgl"

    # %% workflow code
    import xarray as xr
    import hvplot.xarray
    import zarr

    print(f"n: {n}. running app code")
    DATA_PARENT_PATH = "~/data/image-stacks/miniscope/"
    DATA_ARRAY = n
    DATA_PATH = f"{DATA_PARENT_PATH}/miniscope_sim_{DATA_ARRAY}.zarr/"
    ds = xr.open_dataset(DATA_PATH, engine="zarr", chunks="auto")
    data = ds[DATA_ARRAY]

    FRAMES_PER_SECOND = 30
    FRAMES = data.coords["frame"].values

    video_player = pn.widgets.Player(
        length=len(data.coords["frame"]),
        interval=1000 // FRAMES_PER_SECOND,  # ms
        value=int(FRAMES.min()),
        max_width=400,
        max_height=90,
        loop_policy="loop",
        sizing_mode="stretch_width",
    )
    video_player.margin = (20, 20, 20, 70)  # center widget over main

    main_plot = data.hvplot.image(
        groupby="frame",
        cmap="Viridis",
        frame_height=400,
        frame_width=400,
        colorbar=False,
        widgets={"frame": video_player},
    )

    # frame indicator lines on side/bottom plots
    line_opts = dict(color="red", alpha=0.6, line_width=3)
    dmap_hline = hv.DynamicMap(
        pn.bind(lambda value: hv.HLine(value), video_player)
    ).opts(**line_opts)
    dmap_vline = hv.DynamicMap(
        pn.bind(lambda value: hv.VLine(value), video_player)
    ).opts(**line_opts)

    right_plot = (
        data.mean(["width"]).hvplot.image(
            x="frame",
            cmap="Viridis",
            frame_height=400,
            frame_width=200,
            colorbar=False,
            title="_",
        )
        * dmap_vline
    )

    bottom_plot = (
        data.mean(["height"]).hvplot.image(
            y="frame",
            cmap="Viridis",
            frame_height=200,
            frame_width=400,
            colorbar=False,
        )
        * dmap_hline
    )

    full_app = pn.Column(video_player, pn.Row(main_plot[0], right_plot), bottom_plot)

    # %% Trigger sending of the full_app
    def run_callback(run):
        if not run:  # runs once at the beginning if using pn.bind
            # Initialize with an empty plot to trigger the initial paint and unblock the latency test
            # Make responsive so as not to limit the subsequent app dimensions
            return hv.Curve([]).opts(responsive=True)
        figure = doc.select_one(dict(type=Plot))
        doc.remove_root(figure)
        return full_app

    run_button = pn.widgets.Button(name="run")
    doc.add_root(
        pn.Column(pn.bind(run_callback, run=run_button), run_button).get_root(doc)
    )


class imagestackBase(Base):
    repeat = 1  # Force a single benchmark timing for each setup-teardown call.
    number = 1  # Force a single benchmark timing for each setup-teardown call.
    rounds = 2
    await_n_figs = 3  # IMPORTANT!! MAKE SURE THIS MATCHES NUMBER OF FIGURES IN APP

    params: tuple[list[int], list[str]] = (
        ["10frames", "100frames", "1000frames", "10000frames"],
        ["canvas", "webgl"],
    )
    param_names: tuple[str] = ("n", "output_backend")

    def setup(self, n: int, output_backend: str) -> None:
        print('setting up')
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


class imagestackLatency(imagestackBase):
    """measure latency which is the time taken to transfer data to the browser and render it. The browser and
    server are already running before the benchmark starts.
    """

    def time_latency(self, n: int, output_backend: str) -> None:
        self.multi_fig_click_button_and_wait_for_render("run", self.await_n_figs)


# class imagestackScrub(imagestackBase):
#     """measure the time taken for an
#     interactive scrub which is achieved here using by scrubbing to another frame.
#     """
#     def setup(self, n: int, output_backend: str) -> None:
#         super().setup(n, output_backend)

#         # Render initial data set
#         self.multi_fig_click_button_and_wait_for_render("run", self.await_n_figs)

#     def time_scrub(self, n: int, output_backend: str) -> None:
#         self.multi_fig_click_button_and_wait_for_render("scrub", self.await_n_figs)

if __name__ == "__main__":
    n = "1000frames"
    backend = "webgl"

    init_latency = imagestackLatency()
    init_latency.setup(n, backend)
    init_latency.time_latency(n, backend)
    init_latency.teardown(n, backend)

    # scrub_latency = imagestackScrub()
    # scrub_latency.setup(n, backend)
    # scrub_latency.time_scrub(n, backend)
    # scrub_latency.teardown(n, backend)
