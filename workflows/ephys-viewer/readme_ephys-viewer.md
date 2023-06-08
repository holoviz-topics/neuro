# Ephys Viewer

![Status](https://img.shields.io/badge/status-in%20progress-orange)

## Summary
This ephys-viewer workflow will involve a series of stacked time-series subplots with a
shared X-axis representing time. Each subplot is intended to correspond to a distinct
channel, with the goal of facilitating simultaneous, synchronized examination of neural
activity. Key proposed features:

- **Handling large datasets:** Benchmarking and providing solutions for large data handling challenges to ensure smooth performance.

- **Stacked traces on the same canvas:** For a time-aligned view of ephys channels, we plan to render each as a separate trace on a shared canvas, each with its own Y axis. Current limitations of Bokeh/HoloViews make this challenging, as it requires manual offsetting of the data, affecting interactive features like hover, selection, and cross-linking. Thus, improving subplotting capabilities for more natural handling of such cases will be prioritized.
- **Scale bar:** A visual reference for signal amplitude, aiding in the interpretation of the ephys signals.
- **1D Annotation:** Marking and categorizing significant events or epochs.
- **Minimap for visual navigation:** To facilitate easy navigation through large time series data, we propose to include a minimap feature. This should provide an overview of the data and enable quick navigation to specific time intervals and channels.
- **Signal grouping:** This feature will enable users to observe and contrast various
  types of signals routinely recorded in tandem with ephys, or different derivations of
  the raw ephys data (e.g. LFP or spike range band-passed traces). The intention is to
  also handle
  signals with varied sampling and amplitude ranges like accelerometers or linearized
  spatial position (of the subject). Part of the handling will include
  group-wise y-axis manual scaling of the signal.

## Links:
---

- [Workflow demo](./workflow_ephys-viewer.ipynb)

- [Electrophysiology notes](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes)

- [All ephys-viewer workflow Issues/PRs](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*ephys-viewer*%22). *(Bulleted links below for feature-specific tasks)*

## Prioritized Tasks (Features/Bottlenecks)
---

- [`large-data-handling`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*large-data-handling*%22)) (lead: `@ianthomas23`): Benchmark and solve large data handling
  - This is high priority because almost all ephys data has a very high sampling rate
    (30KHz) and (in the last few years) many channels (>100).
  - [Large data handling meeting notes](https://github.com/holoviz-topics/neuro/wiki/Meeting-Notes#230515-large-data-handling)
- [`subcoordinates`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*subcoordinates*%22)) (lead: `@mattpap`): Stacked traces on Y axis sub-coordinates
  - Avoid having to add an offset to the data values in order plot stacked on the same canvas
- [`scale-bar`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*scale-bar*%22)) (lead: `@mattpap`)
- [`annotation`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*annotation*%22)) (lead: `@hoxbro` and/or `@jlstevens`)
  - potential extension: Bokeh toolbar UI
- [`minimap`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*minimap*%22) (lead: `@droumis`, helped by `@ianthomas23`)
- [`channel-type-grouping`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*channel-type-grouping*%22)) Channel-type grouping with different sampling and amplitude range
- [`grouped-y-scaling`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*grouped-y-scaling*%22)): Manual scaling of Y axis per channel or per channel group
  - channel scroll-scaling of hovered channel
  - channel scroll-scaling of hovered channel Y-axis channel group

**Wishlist/Ideas:**
- Button to load from file
- DC removal
- drag to rearrange channel display order
- Toggle from raw (:30KHz) to LFP (1 - 500 Hz) to Spikes (500 - 5000 Hz)

## Primary Plot Specifications
---

**Axis specs:**

- x
  - type, label: continuous, `time`
  - typical resolution: 0.03 ms/sample (30 kHz)
  - typical extent: hours
- y
  - type, label: subcoordinate continuous, `channel(microvolt)`
  - typical resolution: ± 100 µV / channel
  - typical extent: < 512 channels

## Data
---

### Format, size and other specs
- See Wiki > [Electrophysiology notes > Data](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes)

### Generated Data
- `neurodatagen.ephys`
  - `generate_ephys_powerlaw`: Generate synthetic ephys data (np.ndarray) as power law time series at a specified exponent and poisson spikes.
    ```python
    # Example usage:
    from neurodatagen.ephys import generate_ephys_powerlaw

    n_channels: 4
    n_seconds: 0.5
    fs = 30000

    data, time, channels = generate_ephys_powerlaw(n_channels, n_seconds, fs)
    ```

### Real Data
- See Wiki > [Electrophysiology notes > Real
  Data](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes#listssources-of-real-data)

## Future Directions
---

- Optimize for NWB 2.0 format
- Demonstrate biomedical/translational use-case
- Try streaming