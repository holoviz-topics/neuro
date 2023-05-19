# HoloViz+Bokeh for Neuroscience Workflows

> :warning: This work is in early development and changing rapidly. It is not ready for general public use. :warning:

### What is this repo?

TODO: Short description of project and repo purpose

### What are workflows?

This repo contains the development versions of workflows at two levels - element and community. Element workflows are combined and adapted to become the building blocks for specialized scientific community workflows. The goal of an element workflow is to be generalizable while the goal of a community workflow is to be well-contextualized; both are directly useful to scientists.

*(TODO: add short descriptions, previews, links, badges, etc)*

**Element Workflows**:

1. Ephys Viewer (in progress, info, demo, real data, simulated data)
2. Waveform Viewer (in progress, info, demo, real data, simulated data)
3. Spike Raster (in progress, info, demo, real data, simulated data)
4. EEG Viewer (in progress, info, demo, real data, simulated data)
5. Video Viewer (in progress, info, demo, real data, simulated data)

**Community Workflows**:

1. Spike Motif Viewer (planned, info, demo, real data, simulated data)
2. MNE EEG App (planned, info, demo, real data, simulated data)
3. Minian CNMF App (planned, info, demo, real data, simulated data)

Eventually, the polished version of these workflows will likely be published to [examples.holoviz.org](https://examples.pyviz.org/).

---
## Contributing

- **Task Management:** As workflows are developed and honed, performance and UI bottlenecks will be identified and addressed. Some improvements for the workflows themselves will be within this repo, but many improvements will be in the appropriate underlying libraries within the [HoloViz](https://github.com/holoviz/), [Bokeh](https://github.com/bokeh), or other GitHub Organizations. We will do our best to track the disparate tasks related to these efforts into this [project board](https://github.com/orgs/holoviz-topics/projects/1).
- **Meeting minutes:** Logged in the [Wiki](https://github.com/holoviz-topics/neuro/wiki) whenever possible.
- **Specifications:** The [Wiki](https://github.com/holoviz-topics/neuro/wiki) has some data specifications and modality notes (in progress).
- **Data:** To assist the development using real data (TODO: add link), some workflows utilize simple data simulators (in progress TODO: add link) to help benchmark across data and parameter space.
- **Repo Structure and dev patterns:** 
  - As the data generators can be useful to multiple workflows, they are kept as a separate and importable module:
    ```
    /_neurodatagen
        pyproject.toml
        /neurodatagen
            __init__.py
    /example_workflow
        environment.yml
        demo_example-workflow.ipynb
        readme_example-workflow.md
        /dev
            date_example-workflow_task.ipynb
    ```
  - Each workflow should have an `environment.yml` with which to create a conda env that will install the neurodatagen module in dev mode:
    ```
    name: neuro-example-workflow
    channels:
    - conda-forge
    dependencies:
    - python=3.9
    - pip
    - pip:
        - -e ../_neurodatagen
    ```
  - Use the `dev` dir in each workflow as shared scratch space. There is no expectation that anything here is maintained.
  - Maintain `demo_<workflow>.ipynb` as the latest (stable) version of the workflow.
  - Use `readme_<workflow>.md` for any essential workflow-specific info or links.

---
## Who is behind this?

This work is a collaboration between developers and scientists. While some contributions are visible through the GitHub repo, many other contributions are less visible yet equally important. Here is a (hopefully) complete list of contributors in no particular order, as of early 2023:

- James Bednar
- Demetris Roumis
- Ian Thomas
- Mateusz Paprocki
- Bryan Van de Ven
- Jean-Luc Stevens
- Philipp Rudiger
- Laurent Perrinet
- Denise Cai
- Clemens Brunner
- Andrew Davison
- Jan Antolik

Sponsors:
- 2023 - 2024: Chan Zuckerberg Initiative. Learn more in the [grant announcement]([url](https://blog.bokeh.org/announcing-czi-funding-for-bokeh-for-bioscience-5f74426c011a)).


---

### Why Neuroscience?

Multiple (probably all) HoloViz+Bokeh developers believe that helping people through the furthering of clinically impactful science is a worthy pursuit and in need of a data visualization boost.

### Why HoloViz+Bokeh?

We hypothesize that the visualization (perception through the eyes) within the process of working always benefits from having the option to suddenly become interactive and shareable - allowing for the poking or plucking, pushing or pulling, drilling in or out, grouping or separating, and sending or receiving of what would otherwise be a static snapshot of the data. The combined use of HoloViz and Bokeh tools provides the interactivity and shareability needed to support research as a collective action rather than a collection of solitary observations.
