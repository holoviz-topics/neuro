# Spike Raster

![Status](https://img.shields.io/badge/status-in%20progress-orange)

## Summary
---

This proposed spike raster viewer workflow is designed to facilitate the exploration of
large-scale neuronal spike time data with the following features and tasks:

- **Handling large datasets:** Benchmarking and providing solutions for large data
  handling challenges to ensure smooth performance.

- **Efficient API:** Scatter-plot-like API while maintaining utility of interactive features like
  zooming.

- **Aggregation:** Linked aggregate views of spike counts over time and over channels, facilitating high-level data comprehension.

- **Versatility in Input Formats:** The raster will be designed to accept spike train data in a variety of common formats, offering flexibility to accommodate different data structures.

- **Spike Metadata Management:** The workflow will incorporates the handling of additional spike-level metadata, such as the color-coding of spikes by motif-group, to provide a rich and detailed data presentation.

## Links:
---

- [Workflow demo](./workflow_ephys-viewer.ipynb)

- [Electrophysiology notes](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes)

- [All spike-raster workflow Issues/PRs](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*spike-raster*%22). *(Bulleted links below for feature-specific tasks)*


## Prioritized Tasks (Features/Bottlenecks)
---
- [`large-data-handling`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*large-data-handling*%22) (lead: `@ianthomas23`): Benchmark and solve large data handling
  - This is much more forgiving with a spike-raster compared to e.g. a raw ephys viewer
    because the spike raster data can be represented as a sparse or ragged array (many
    more bins are without any spikes) and there is rarely any good reason to have a
    resolution beyond 1 ms/bin due to the [neural refractory
    period](https://en.wikipedia.org/wiki/Refractory_period_(physiology)#:~:text=of%20atrial%20fibrillation.-,Neuronal%20refractory%20period,-%5Bedit%5D).
  - [Large data handling meeting notes](https://github.com/holoviz-topics/neuro/wiki/

- [`zoom-marker-scaling`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*zoom-marker-scaling*%22) : (lead: `@droumis`)
  - This is a tension between APIs.. we can use hv.Spikes but then have to use a loop to
    set the `position` property on individual spike trains - this produces the intended
    plot but is an inconvenient implementation. Alternatively, using a scatter plot with
    vertical dashes is the ideal API (IMHO) but here the markers don't scale when zooming.

- [`raster-hist`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*raster-hist*%22): (lead: `@droumis`): spike count aggregation against y or x axis

- [`spike-format`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*spike-format*%22): (lead: `@droumis`): Create util to convert between binned, ragged,
  tabular form of spike times

- [`motif-grouping`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*motif-grouping*%22): (lead: `@droumis`): Simulate spike time grouping based on motifs

**Wishlist/Ideas:**


## Primary Plot Specifications
---

**Axis specs:**
- x
  - type, label: continuous, `time`
  - typical resolution: 1 ms
  - typical extent: hours
- y
  - type, label: categorical, `neuron` or `unit`
  - typical resolution: NA
  - typical extent: hundreds of units

## Data
---

### Format, size and other specs
- See Wiki > [Electrophysiology notes >
  Data](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes)

### Generated Data
- `neurodatagen.ephys`
  - `sim_spikes`: Simulates spike times for a given number of neurons, firing rate, and duration.
  - `assign_groups`: Bin an array of spike times into a specified number of groups.
    ```python
    # Example usage:
    from neurodatagen.ephys import sim_spikes, assign_groups


    ```
### Real Data
- See Wiki > [Electrophysiology notes > Real
  Data](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes#listssources-of-real-data)

## Future Directions
---

- Optimize for NWB 2.0 format
- Demonstrate biomedical/translational use-case
- Try streaming