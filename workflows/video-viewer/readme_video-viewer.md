# Video Viewer

> Status: :warning: in progress

## Summary
---
The Video Viewer workflow will provide an efficient tool for visualizing Miniscope calcium imaging movies. It will incorporate the following key features:

- **Handling large datasets:** Benchmarking and providing solutions for large data handling challenges to ensure smooth performance.
- **Playback controls:** Utilizing the HoloViz Panel Player widget for easy navigation through the image stack.
- **2D Annotation:** Marking and categorizing spatial regions of interest (e.g. neurons).
- **Scale bar:** A visual reference for spatial scale.
- **Intensity histogram:** Enabling examination and manipulation of image histograms for identifying patterns or characteristics.
- **Summary statistics:** Providing timeseries of summary statistics (e.g., mean, max, min) linked to playback.

## Links:
---
- [Workflow demo](./workflow_video-viewer.ipynb)

- [Calcium Imaging notes](https://github.com/holoviz-topics/neuro/wiki/Calcium-Imaging-notes)

- [All video-viewer workflow issues/PRs](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*video-viewer*%22). *(Bulleted links below for feature-specific tasks)*

## Prioritized Tasks (Features/Bottlenecks)
---
- [`large-data-handling`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*large-data-handling*%22)) (lead: `@ianthomas23`): Benchmark and solve large data handling
  - This has been communicated as the primary pain point for miniscope users
  - The combined raw movies from a single recording can easily exceed available memory for typical laptops.
  - [Large data handling meeting notes](https://github.com/holoviz-topics/neuro/wiki/Meeting-Notes#230515-large-data-handling)
- [`player-widget`]:
  - Utilize the Panel player widget for easy playback controls
- [`2D-annotation`]:
  - Try to use holonote for roi management
  - Potential extension: 2D annotated (region of interest) spatial aggregation to linked timeseries
  - Potential extension: UI integration into the Bokeh toolbar.
- [`scale-bar`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*scale-bar*%22)) (lead: `@mattpap`)
- [`intensity-hist`]:
  - By examining and manipulating the histogram of an image, users can observe and manipulate the distribution of pixel intensities and identify patterns or characteristics in different tonal ranges.
  - It is common to overexpose calcium imaging data to reveal detail.
- [`summary-stats`]: Timeseries of summary statistics (e.g. mean, max, min) linked to playback

**Wishlist/Ideas:**
- slice viewer + colormapped transparency

## Data
---
### Key Specifications

### Generated Data
- `neurodatagen.ca-imaging`
  - `simulate_miniscope_data`: Generates a simulated miniscope dataset that mimics the key properties of real miniscope data.

Example usage:
```python

from neurodatagen.ca_imaging import simulate_miniscope_data

ncell = 15
dims = {'height': 256, 'width': 256, 'frame': 300}

data = simulate_miniscope_data(ncell=ncell, dims=dims).compute()
```

### Real Data
- TODO
## Future Directions
---
- Explore extensions into 2P Ca imaging, potentially with `CaImAn` integration
- Demonstrate biomedical/translational use-case
- Try streaming