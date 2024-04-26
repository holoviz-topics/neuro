# Image Stack Viewer (formerly video viewer)

![Status](https://img.shields.io/badge/status-in%20progress-orange)

## Summary
---
The Image Stack Viewer workflow will provide an efficient tool for visualizing Miniscope calcium imaging movies. It will incorporate the following key features:

- **Handling large datasets:** Benchmarking and providing solutions for large data handling challenges to ensure smooth performance.
- **Playback controls:** Utilizing the HoloViz Panel Player widget for easy navigation through the image stack.
- **2D Annotation:** Marking and categorizing spatial regions of interest (e.g. neurons).
- **Scale bar:** A visual reference for spatial scale.
- **Intensity histogram:** Enabling examination and manipulation of image histograms for identifying patterns or characteristics.
- **Summary statistics:** Providing timeseries of summary statistics (e.g., mean, max,
  min) linked to playback.
- **Sliced Dimension Viewers:** Providing linked views onto the frame-axis sides of the image stack

## Links:
---
- [Workflow demo](./workflow_image-stack.ipynb)

- [Calcium Imaging notes](https://github.com/holoviz-topics/neuro/wiki/Calcium-Imaging-notes)

- [All image-stack/video-viewer workflow issues/PRs](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*video-viewer*%22). *(Bulleted links below for feature-specific tasks)*

## Prioritized Tasks (Features/Bottlenecks)
---
- [`large-data-handling`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*large-data-handling*%22) (lead: `@ianthomas23`): Benchmark and solve large data handling
  - This has been communicated as the primary pain point for miniscope users
  - The combined raw movies from a single recording can easily exceed available memory for typical laptops.
  - [Large data handling meeting notes](https://github.com/holoviz-topics/neuro/wiki/Meeting-Notes#230515-large-data-handling)
  - [Minian tips & tricks](https://minian.readthedocs.io/en/stable/tips/index.html) has
    good info about their data model and performance pattern (.avi > xarray zarr > dask array)
- [`player-widget`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*player-widget*%22) (lead: `@droumis`)
  - Utilize Panel Player widget for xarray playback
- [`2D-annotation`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*2d-annotation*%22) (lead: `@hoxbro` and/or `@jlstevens`)
  - Try to use holonote for roi management
  - Potential extension: 2D annotated (region of interest) spatial aggregation to linked timeseries
  - Potential extension: UI integration into the Bokeh toolbar.
- [`scale-bar`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*scale-bar*%22) (lead: `@mattpap`):
- [`intensity-hist`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*intensity-hist*%22):
  - By examining and manipulating the histogram of an image, users can observe and manipulate the distribution of pixel intensities and identify patterns or characteristics in different tonal ranges.
- [`summary-stats`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*summary-stats*%22):
  Timeseries of summary statistics (e.g. mean, max, min) linked to playback
- ['slice-dim'](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*slice-dim-views*%22): linked views onto the frame-axis sides of the image stack

**Wishlist/Ideas:**
- Playback of large raw movies files like .avi (instead of from zarr/dask/xarray)
- slice viewer + colormapped transparency

## Primary Plot Specifications
---

**Axis specs:**

- x
  - type, label: continuous, `x`
  - typical resolution: 1 um (~1 um/px)
  - typical extent: <1k px (miniscope v4: 608 px)
- y
  - type, label: continuous, `y` 
  - typical resolution: 1 um (~1 um/px)
  - typical extent: <1k px (miniscope v4: 608 px)
- z
  - type, label: continuous, `time`
  - typical resolution: 30 Hz
  - typical extent: ~100k frames

## Data
---

### Format, size and other specs

- See Wiki > [Calcium Imaging notes > Data](https://github.com/holoviz-topics/neuro/wiki/Calcium-Imaging-notes#data)

### Generated Data
- `neurodatagen.ca-imaging`
  - `simulate_miniscope_data`
    - ```markdown
      # Docstring:
      Generates a simulated miniscope dataset (xarray.DataArray) that mimics the key properties of real miniscope data.

      This function simulates the spatiotemporal fluorescence signals of neurons and background components by generating and then combining spatial footprints (Gaussian) and temporal traces (exponential) using user-defined parameters. It then adds spatial shifts to simulate motion artifacts, injects Gaussian noise, applies a linear transformation to adjust the signal and noise levels, and clips pixel values to an 8-bit range.
      ```
    -   ```python
        # Example usage:
        from neurodatagen.ca_imaging import simulate_miniscope_data

        ncell = 15
        dims = {'height': 256, 'width': 256, 'frame': 300}

        data = simulate_miniscope_data(ncell=ncell, dims=dims).compute()
        ```

### Real Data
- See Wiki > [Calcium Imaging notes > Real Data](https://github.com/holoviz-topics/neuro/wiki/Calcium-Imaging-notes#listssources-of-real-data)

## Future Directions
---
- Explore extensions into 2P Ca imaging, potentially with `CaImAn` integration
- Demonstrate biomedical/translational use-case
- Try streaming data