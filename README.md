# Workflow Viz with HoloViz+Bokeh for Biomedical Research in Neuroscience

## Why?

### Why "Biomedical Research in Neuroscience"?

Multiple (probably all) HoloViz+Bokeh developers believe that helping people through the furthering of clinically impactful science is a worthy pursuit, and in need of a data visualization boost.

### OK, but why "Workflow Viz with HoloViz+Bokeh"?

We hypothesize that the visualization (perception through the eyes) within the process of working always benefits from having the option to suddenly become interactive and shareable - allowing for the poking or plucking, pushing or pulling, drilling in or out, grouping or separating, and sending or receiving of what would otherwise be a static snapshot of the data. The combined use of HoloViz and Bokeh tools provides the interactivity and shareability needed to support research as a collective action rather than a collection of solitary observations.

## What?

TODO: Short description of project

### What Workflows?

This repo contains the development versions of workflows at two blurry levels - element and community. Element workflows are combined and adapted to become the building blocks for specialized scientific community workflows. The goal of an element workflow is to be generalizable while the goal of a community workflow is to be well-contextualized.

*(TODO: add short descriptions, previews, links, badges, etc)*

**Element Workflows**:

1. Ephys Viewer (in progress, info, demo, real data, simulated data)
2. Waveform Viewer (in progress, info, demo, real data, simulated data)
3. Spike Raster (in progress, info, demo, real data, simulated data)
4. EEG Viewer (in progress, info, demo, real data, simulated data)
5. Video Viewer (in progress, info, demo, real data, simulated data)

**Community Workflows**:

1. Spike Motif Viewer (in progress, info, demo, real data, simulated data)
2. MNE EEG App (in progress, info, demo, real data, simulated data)
3. Minian CNFM App (in progress, info, demo, real data, simulated data)

Eventually, the polished version of these workflows will likely be published to [examples.holoviz.org](https://examples.pyviz.org/).

## How?

### How to make progress?

- **Task Management:** As workflows are developed and honed, performance and UI bottlenecks will be identified and addressed. Some improvements for the workflows themselves will be within this repo, but many improvements will be in the appropriate underlying libraries within the [HoloViz](https://github.com/holoviz/), [Bokeh](https://github.com/bokeh), or other GitHub Organizations. We will do our best to track the disparate tasks related to these efforts into this [project board](https://github.com/orgs/holoviz-topics/projects/1).
- **Meeting minutes:** Logged in the [Wiki](https://github.com/holoviz-topics/neuro/wiki) whenever possible.
- **Specifications:** The [Wiki](https://github.com/holoviz-topics/neuro/wiki) has some data specifications and modality notes (in progress).
- **Data:** To assist the development using real data (TODO: add link), some workflows utilize simple data simulators (in progress TODO: add link) to help benchmark across data and parameter space.
- **Development patterns:** 
  - "Every workflow, an island" *- probably no one* (But every workflow should have its own environment file).


### How did this come about?

The efforts in this repository are made possible through funding from the kind folks at the Chan Zuckerberg Initiative. Learn more from the [grant announcement]([url](https://blog.bokeh.org/announcing-czi-funding-for-bokeh-for-bioscience-5f74426c011a)).

## Who?

This work is a collaboration between developers and scientists. While some contributions are visible through the GitHub repo, many other contributions are less visible yet equally important. Here is a (hopefully) complete list of contributors in no particular order, as of early 2023:

- James Bednar
- Demetris Roumis
- Ian Thomas
- Mateusz Paprocki
- Bryan Van de Ven
- Jean-Luc Stevens
- Laurent Perrinet
- Denise Cai
- Clemens Brunner
- Andrew Davison
- Jan Antolik
