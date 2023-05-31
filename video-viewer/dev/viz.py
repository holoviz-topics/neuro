from typing import Union, List, Optional
import numpy as np
import xarray as xr
import holoviews as hv
import panel as pn
import param
import functools as fct
import itertools as itt
from collections import OrderedDict
from datashader import count_cat
from holoviews.streams import Stream, BoxEdit, RangeXY
from holoviews.operation.datashader import datashade
import holoviews as hv
hv.extension('bokeh')
import panel.widgets as pnwgt
from bokeh.palettes import Category10_10, Viridis256


class VArrayViewer:
    """
    Interactive visualization for movie data arrays.
    
    Parameters
    ----------
    varr : Union[xr.DataArray, List[xr.DataArray], xr.Dataset]
        Input array, list of arrays, or dataset to be visualized. Each array
        should contain dimensions "height", "width" and "frame". If a
        dataset, then the dimensions specified in `meta_dims` will be used
        as metadata dimensions that can uniquely identify each array. If a
        list, then a dimension "data_var" will be constructed and used as
        metadata dimension, and the `.name` attribute of each array will be
        used to identify each array.
    framerate : int, optional
        The framerate of playback when using the toolbar. By default `30`.
    summary : list, optional
        List of summary statistics to plot. The statistics should be one of
        `{"mean", "max", "min", "diff"}`. By default `["mean", "max"]`.
    meta_dims : List[str], optional
        List of dimension names that can uniquely identify each input array
        in `varr`. Only used if `varr` is a `xr.Dataset`. By default `None`.
    datashading : bool, optional
        Whether to use datashading on the summary statistics. By default
        `True`.
    layout : bool, optional
        Whether to visualize all arrays together as layout. If `False` then
        only one array will be visualized and user can switch array using
        drop-down lists below the *Play Toolbar*. By default `False`.

    Raises
    ------
    NotImplementedError
        if `varr` is not a `xr.DataArray`, a `xr.Dataset` or a list of `xr.DataArray`
    
    More:
    ------
    The visualization contains following panels from top to bottom:

    Play Toolbar
        A toolbar that controls playback of the video. Additionally, when the
        button "Update Mask" is clicked, the coordinates of the box drawn in
        *Current Frame* panel will be used to update the `mask` attribute of the
        `VArrayViewer` instance, which can be later used to subset the data. If
        multiple arrays are visualized and `layout` is `False`, then drop-down
        lists corresponding to each metadata dimensions will show up so the user
        can select which array to visualize.
    Current Frame
        Images of the current frame. If multiple movie array are passed in,
        multiple frames will be labeled and shown. To the side of each frame
        there is a histogram of intensity values. The "Box Select" tool can be
        used on the histogram to limit the range of intensity used for
        color-mapping. Additionally, the "Box Edit Tool" is available for use on
        the frame image, where you can hold "Shift" and draw a box, whose
        coordinates can be used to update the `mask` attribute of the
        `VarrayViewer` instance (remember to click "Update Mask" after drawing).
    Summary
        Summary statistics of each frame across time. Only shown if `summary` is
        not empty. The red vertical line indicate current frame.

    Attributes
    ----------
    mask : dict
        Instance attribute that can be retrieved and used to subset data later.
        Keys are `tuple` with values corresponding to each `meta_dims` and
        uniquely identify each input array. If `meta_dims` is empty then keys
        will be empty `tuple` as well. Values are `dict` mapping dimension names
        (of the arrays) to subsetting slices. The slices are in the plotting
        coorandinates and can be directly passed to `xr.DataArray.sel` method to
        subset data.
    """

    def __init__(
        self,
        varr: Union[xr.DataArray, List[xr.DataArray], xr.Dataset],
        framerate=30,
        summary=["mean", "max"],
        meta_dims: List[str] = None,
        datashading=True,
        layout=False,
    ):
        # Handling different types of `varr` input
        if isinstance(varr, list):
            # If `varr` is a list, assign a new coordinate `data_var` using 
            # the name of each array and concatenate them along the `data_var` dimension
            for iv, v in enumerate(varr):
                varr[iv] = v.assign_coords(data_var=v.name)
            self.ds = xr.concat(varr, dim="data_var")
            meta_dims = ["data_var"]
        elif isinstance(varr, xr.DataArray):
            # If `varr` is a DataArray, convert it into a Dataset
            self.ds = varr.to_dataset()
        elif isinstance(varr, xr.Dataset):
            # If `varr` is a Dataset, keep it as it is
            self.ds = varr
        else:
            # If `varr` is not a list, DataArray, or Dataset, raise an error
            raise NotImplementedError(
                "video array of type {} not supported".format(type(varr))
            )

        # Initialize metadata based on the specified metadata dimensions
        try:
            self.meta_dicts = OrderedDict(
                [(d, list(self.ds.coords[d].values)) for d in meta_dims]
            )
            self.cur_metas = OrderedDict(
                [(d, v[0]) for d, v in self.meta_dicts.items()]
            )
        except TypeError:
            self.meta_dicts = dict()
            self.cur_metas = dict()

        # Initialize some attributes
        self._datashade = datashading
        self._layout = layout
        self.framerate = framerate
        self._f = self.ds.coords["frame"].values
        self._h = self.ds.sizes["height"]
        self._w = self.ds.sizes["width"]
        self.mask = dict()

        # Define streams for interaction
        CStream = Stream.define(
            "CStream",
            f=param.Integer(
                default=int(self._f.min()), bounds=(self._f.min(), self._f.max())
            ),
        )
        self.strm_f = CStream()
        self.str_box = BoxEdit()
        self.widgets = self._widgets()

        # Compute and store summary statistics
        if type(summary) is list:
            summ_all = {
                "mean": self.ds.mean(["height", "width"]),
                "max": self.ds.max(["height", "width"]),
                "min": self.ds.min(["height", "width"]),
                "diff": self.ds.diff("frame").mean(["height", "width"]),
            }
            try:
                summ = {k: summ_all[k] for k in summary}
            except KeyError:
                print("{} Not understood for specifying summary".format(summary))
            if summ:
                # print("computing summary")
                sum_list = []
                for k, v in summ.items():
                    sum_list.append(v.compute().assign_coords(sum_var=k))
                summary = xr.concat(sum_list, dim="sum_var")
        self.summary = summary

        # Initialize subsets of data and summary statistics based on layout option
        if layout:
            self.ds_sub = self.ds
            self.sum_sub = self.summary
        else:
            self.ds_sub = self.ds.sel(**self.cur_metas)
            try:
                self.sum_sub = self.summary.sel(**self.cur_metas)
            except AttributeError:
                self.sum_sub = self.summary

        # Generate the panel plot
        self.pnplot = pn.panel(self.get_hvobj())

    def get_hvobj(self):
        """
        Generates a holoviews Layout object of the image stack
        """
        def get_im_ovly(meta):  # Function to generate overlay of image and box
            def img(f, ds):  # Function to generate HoloViews image object for a given frame
                return hv.Image(ds.sel(frame=f).compute(), kdims=["width", "height"])

            # Select a sub-dataset based on metadata; if not possible, use the original dataset
            try:
                curds = self.ds_sub.sel(**meta).rename("_".join(meta.values()))
            except ValueError:
                curds = self.ds_sub

            fim = fct.partial(img, ds=curds)  # Partial function for image generation with current dataset

            # Create a dynamic map for images with the given partial function and frame stream
            im = hv.DynamicMap(fim, streams=[self.strm_f]).opts(
                frame_width=500, aspect=self._w / self._h, cmap="Viridis"
            )

            # Define a range of x and y coordinates for the image
            self.xyrange = RangeXY(source=im).rename(x_range="w", y_range="h")

            # Create a box if layout is not yet defined
            if not self._layout:
                hv_box = hv.Polygons([]).opts(
                    fill_alpha= 0.3, line_color= "white"
                )
                self.str_box = BoxEdit(source=hv_box)
                im_ovly = im * hv_box  # Create an overlay of the image and the box
            else:
                im_ovly = im  # If layout already defined, use the image as is

            def hist(f, w, h, ds):  # Function to generate histogram for given frame, width, height and dataset
                if w and h:
                    cur_im = hv.Image(
                        ds.sel(frame=f).compute(), kdims=["width", "height"]
                    ).select(height=h, width=w)
                else:
                    cur_im = hv.Image(
                        ds.sel(frame=f).compute(), kdims=["width", "height"]
                    )
                return hv.operation.histogram(cur_im, num_bins=50).opts(
                    xlabel="fluorescence", ylabel="freq"
                )

            fhist = fct.partial(hist, ds=curds)  # Partial function for histogram generation with current dataset

            # Create a dynamic map for histograms with the given partial function and frame & xy range streams
            his = hv.DynamicMap(fhist, streams=[self.strm_f, self.xyrange]).opts(
                frame_height=int(500 * self._h / self._w), width=150, cmap="Viridis"
            )

            # add the histogram as an adjoint subfig
            im_ovly = im_ovly << his

            return im_ovly  # Return the overlay object

        # If layout is defined and metadata is available
        if self._layout and self.meta_dicts:
            im_dict = OrderedDict()  # Initialize an ordered dictionary to store the images
            for meta in itt.product(*list(self.meta_dicts.values())):  # For each combination of metadata values
                mdict = {k: v for k, v in zip(list(self.meta_dicts.keys()), meta)}  # Map each metadata key to its value
                im_dict[meta] = get_im_ovly(mdict)  # Add the generated overlay to the dictionary

            # Generate a HoloViews NdLayout object from the image dictionary
            ims = hv.NdLayout(im_dict, kdims=list(self.meta_dicts.keys()))
        else:
            # If no layout or metadata, generate an overlay for the current metadata
            ims = get_im_ovly(self.cur_metas)

        if self.summary is not None:  # If summary data is available
            # Generate a HoloViews Curve object from the summary data
            hvsum = (
                hv.Dataset(self.sum_sub)
                .to(hv.Curve, kdims=["frame"])
                .overlay("sum_var")
            )

            # Apply data shading if required
            if self._datashade:
                hvsum = datashade_ndcurve(hvsum, kdim="sum_var")

            try:
                hvsum = hvsum.layout(list(self.meta_dicts.keys()))  # Arrange the summary layout based on metadata
            except:
                pass

            # Generate a vertical line to indicate the current frame
            vl = hv.DynamicMap(lambda f: hv.VLine(f), streams=[self.strm_f]).opts(
                color="red")

            # Combine the summary curves and the vertical line, and apply dimensions and a colormap
            summ = (hvsum * vl).map(
                lambda p: p.opts(frame_width=500, aspect=3), [hv.RGB, hv.Curve]
            )

            # Combine the images and the summary into a single layout, arranged in columns
            hvobj = (ims + summ).cols(1)
        else:
            hvobj = ims  # If no summary data, the layout is just the images

        return hvobj  # Return the layout object


    def show(self) -> pn.layout.Column:
        # Return widgets and plots in a layout
        return pn.layout.Column(self.widgets, self.pnplot)

    def _widgets(self):
        w_play = pnwgt.Player(
            length=len(self._f), interval=10, value=0, width=650, height=90
        )

        def play(f):
            if not f.old == f.new:
                self.strm_f.event(f=int(self._f[f.new]))

        w_play.param.watch(play, "value")
        w_box = pnwgt.Button(
            name="Update Mask", button_type="primary", width=100, height=30
        )
        w_box.param.watch(self._update_box, "clicks")
        if not self._layout:
            wgt_meta = {
                d: pnwgt.Select(name=d, options=v, height=45, width=120)
                for d, v in self.meta_dicts.items()
            }

            def make_update_func(meta_name):
                def _update(x):
                    self.cur_metas[meta_name] = x.new
                    self._update_subs()

                return _update

            for d, wgt in wgt_meta.items():
                cur_update = make_update_func(d)
                wgt.param.watch(cur_update, "value")
            wgts = pn.layout.WidgetBox(w_box, w_play, *list(wgt_meta.values()))
        else:
            wgts = pn.layout.WidgetBox(w_box, w_play)
        return wgts

    def _update_subs(self):
        self.ds_sub = self.ds.sel(**self.cur_metas)
        if self.sum_sub is not None:
            self.sum_sub = self.summary.sel(**self.cur_metas)
        self.pnplot.objects[0].object = self.get_hvobj()

    def _update_box(self, click):
        box = self.str_box.data
        self.mask.update(
            {
                tuple(self.cur_metas.values()): {
                    "height": slice(box["y0"][0], box["y1"][0]),
                    "width": slice(box["x0"][0], box["x1"][0]),
                }
            }
        )

def datashade_ndcurve(
    ovly: hv.NdOverlay, kdim: Optional[Union[str, List[str]]] = None, spread=False
) -> hv.Overlay:
    """
    Apply datashading to an overlay of curves with legends.

    Parameters
    ----------
    ovly : hv.NdOverlay
        The input overlay of curves.
    kdim : Union[str, List[str]], optional
        Key dimensions of the overlay. If `None` then the first key dimension of
        `ovly` will be used. By default `None`.
    spread : bool, optional
        Whether to apply :func:`holoviews.operation.datashader.dynspread` to the
        result. By default `False`.

    Returns
    -------
    hvres : hv.Overlay
        Resulting overlay of datashaded curves and points (for legends).
    """
    if not kdim:
        kdim = ovly.kdims[0].name
    var = np.unique(ovly.dimension_values(kdim)).tolist()
    color_key = [(v, Category10_10[iv]) for iv, v in enumerate(var)]
    color_pts = hv.NdOverlay(
        {
            k: hv.Points([0, 0], label=str(k)).opts(color=v)
            for k, v in color_key
        }
    )
    ds_ovly = datashade(
        ovly,
        aggregator=count_cat(kdim),
        color_key=dict(color_key),
        min_alpha=200,
        normalization="linear",
    )
    if spread:
        ds_ovly = dynspread(ds_ovly)
    return ds_ovly * color_pts