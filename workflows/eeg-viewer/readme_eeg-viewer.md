# EEG Viewer

![Status](https://img.shields.io/badge/status-in%20progress-orange)

## Summary
---
This EEG-Viewer workflow will involve a series of stacked time-series subplots with a
shared X-axis representing time. Each subplot is intended to correspond to a distinct
EEG channel, with the goal of facilitating simultaneous, synchronized examination of the
activity recorded from different regions of the human brain. Key proposed features:

- **Handling large datasets:** Benchmarking and providing solutions for large data handling challenges to ensure smooth performance.

- **Stacked traces on the same canvas:** For a time-aligned view of EEG channels, we plan to render each as a separate trace on a shared canvas, each with its own Y axis. Current limitations of Bokeh/HoloViews make this challenging, as it requires manual offsetting of the data, affecting interactive features like hover, selection, and cross-linking. Thus, improving subplotting capabilities for more natural handling of such cases will be prioritized.
- **Scale bar:** A visual reference for signal amplitude, aiding in the interpretation of the EEG signals.
- **1D Annotation:** Marking and categorizing significant events or epochs.
- **Minimap for visual navigation:** To facilitate easy navigation through large time series data, we propose to include a minimap feature. This should provide an overview of the data and enable quick navigation to specific time intervals and channels.
- **Signal grouping:** This will allow users to view and compare various types of signals commonly recorded alongside EEG, such as MEG, EOG, and accelerometers. The intention is to handle signals with varied sampling and amplitude ranges. Part of the handling will include group-wise y-axis manual scaling of the signal.

## Links:
---
- [Workflow demo](./workflow_eeg-viewer.ipynb)

- [EEG notes](https://github.com/holoviz-topics/neuro/wiki/EEG-notes)

- [All EEG-viewer workflow Issues/PRs](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*eeg-viewer*%22). *(Bulleted links below for feature-specific tasks)*
## Prioritized Tasks (Features/Bottlenecks)
---
- [`large-data-handling`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*large-data-handling*%22)) (lead: `@ianthomas23`): Benchmark and solve large data handling
  - This is high priority because there are already feature-rich browser-based EEG viewers, but they cannot handle large datasets very well.
  - [Large data handling meeting notes](https://github.com/holoviz-topics/neuro/wiki/Meeting-Notes#230515-large-data-handling)
  - Note: Handling larger-than-memory data is more relevant for ca-imaging and ephys, where the typical data sizes are much larger than EEG.
- [`subcoordinates`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*subcoordinates*%22)) (lead: `@mattpap`): Stacked traces on Y axis sub-coordinates
  - Avoid having to add an offset to the data values in order plot stacked on the same canvas
- [`scale-bar`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*scale-bar*%22)) (lead: `@mattpap`)
- [`annotation`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*annotation*%22)) (lead: `@hoxbro` and/or `@jlstevens`)
  - potential extension: Bokeh toolbar UI
- [`minimap`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*minimap*%22) (lead: `@droumis`, helped by `@ianthomas23`)
- [`channel-type-grouping`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*signal-grouping*%22)) Channel-type grouping with different sampling and amplitude range
- [`grouped-y-scaling`]((https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*grouped-y-scaling*%22)): Manual scaling of Y axis per channel or per channel group
  - channel scroll-scaling of hovered channel
  - channel scroll-scaling of hovered channel Y-axis channel group

**Wishlist/Ideas:**
- Toggle between unstacked and overlaid (butterfly mode) channels
- Button to load from file
- DC removal
- drag to rearrange channel display order

## Primary Plot Specifications
---

**Axis specs:**

- x
  - type, label: continuous, `time`
  - typical resolution: 2 ms/sample (500 Hz)
  - typical extent: hours
- y
  - type, label: subcoordinate continuous, `channel(microvolt)`
  - typical resolution: ± 100 µV / channel
  - typical extent: ~ 64 channels

## Data
---

### Format, size and other specs
- See Wiki > [EEG notes > Data](https://github.com/holoviz-topics/neuro/wiki/EEG-notes#data)

### Generated Data
- `neurodatagen.eeg`
  - `generate_eeg_powerlaw`: Generate synthetic EEG data (np.ndarray) as power law time series.
    ```python
    # Example usage:
    from neurodatagen.eeg import generate_eeg_powerlaw

    n_channels = 20
    n_seconds = 10
    fs = 512

    data, time, channels = generate_eeg_powerlaw(n_channels, n_seconds, fs)
    ```

### Real Data
- See Wiki > [EEG notes > Real Data](https://github.com/holoviz-topics/neuro/wiki/EEG-notes#listssources-of-real-data)

## Future Directions
---
- The work with the EEG-viewer will lead into development of the MNE-Raw workflow, which is essentially the EEG-viewer but integrated into the MNE stack.
- Demonstrate biomedical/translational use-case
- Try streaming