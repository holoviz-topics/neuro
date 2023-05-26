# HoloViz+Bokeh for Neuroscience Workflows

> :warning: This work is in early development and changing rapidly. It is not ready for general public use. :warning:

### What is this repo?

TODO: Short description of project, repo purpose, goals, etc

### What are workflows?

This repo contains the development versions of workflows at two levels - element and community. Element workflows are combined and adapted to become the building blocks for specialized scientific community workflows. The goal of an element workflow is to be generalizable while the goal of a community workflow is to be well-contextualized; both are directly useful to scientists.

*(TODO: add short descriptions, previews, links, badges, etc)*

**Element Workflows**:

<table align="center">
  <tr>
  <td>
      <!-- Title -->
      <h3>Ephys Viewer</h3>
      <h4>(in progress)</h4>
      <!-- Thumbnail link to demo -->
      <a href="./ephys-viewer/workflow_ephys-viewer.ipynb">
        <img src="./ephys-viewer/assets/230524_ephys-viewer.png" alt="eeg-viewer" width="125"/>
      </a>
      <!-- Badges, etc -->
      <!-- Additional content -->
      <p>
      [<a href="./ephys-viewer/readme_ephys-viewer.md">readme</a>,
      <a href="./ephys-viewer/workflow_ephys-viewer.ipynb"> workflow</a>]
    </td>

  <td>
      <!-- Title -->
      <h3>Waveform</h3>
      <h4>(in progress)</h4>
      <!-- Thumbnail link to demo -->
      <a href="./waveform/workflow_waveform.ipynb">
        <img src="./waveform/assets/230524_waveform.png" alt="waveform" width="125"/>
      </a>
      <!-- Badges, etc -->
      <!-- Additional content -->
      <p>
      [<a href="./waveform/readme_waveform.md">readme</a>,
      <a href="./waveform/workflow_waveform.ipynb"> workflow</a>]
    </td>
  <td>
      <!-- Title -->
      <h3>Spike Raster</h3>
      <h4>(in progress)</h4>
      <!-- Thumbnail link to demo -->
      <a href="./spike-raster/workflow_spike-raster.ipynb">
        <img src="./spike-raster/assets/230524_spike-raster.png" alt="spike-raster" width="125"/>
      </a>
      <!-- Badges, etc -->
      <!-- Additional content -->
      <p>
      [<a href="./spike-raster/readme_spike-raster.md">readme</a>,
      <a href="./spike-raster/workflow_spike-raster.ipynb"> workflow</a>]
    </td>
  <!-- </tr>
  <tr> -->
    <td>
      <!-- Title -->
      <h3>EEG Viewer</h3>
      <h4>(in progress)</h4>
      <!-- Thumbnail link to demo -->
      <a href="./eeg-viewer/workflow_eeg-viewer.ipynb">
        <img src="./eeg-viewer/assets/230524_eeg-viewer.png" 
        alt="eeg-viewer" width="125"/>
      </a>
      <!-- Badges, etc -->
      <!-- Additional content -->
      <p>
      [<a href="./eeg-viewer/readme_eeg-viewer.md">readme</a>,
      <a href="./eeg-viewer/workflow_eeg-viewer.ipynb"> workflow</a>]
    </td>
    <td>
      <!-- Title -->
      <h3>Video Viewer</h3>
      <h4>(in progress)</h4>
      <!-- Thumbnail link to demo -->
      <a href="./video-viewer/workflow_video-viewer.ipynb">
        <img src="./video-viewer/assets/230526_video-viewer.png" alt="video-viewer" width="125"/>
      </a>
      <!-- Badges, etc -->
      <!-- Additional content -->
      <p>
      [<a href="./video-viewer/readme_video-viewer.md">readme</a>,
      <a href="./video-viewer/workflow_video-viewer.ipynb"> workflow</a>]
    </td>
  </tr>
</table>

**Community Workflows**:

1. Spike Motif Viewer (planned, info, workflow, real data, simulated data)
2. MNE EEG App (planned, info, workflow, real data, simulated data)
3. Minian CNMF App (planned, info, workflow, real data, simulated data)

Eventually, polished workflow examples will be published to [examples.holoviz.org](https://examples.pyviz.org/).

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
        workflow_example-workflow.ipynb
        readme_example-workflow.md
        /assets
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
  - Use the `dev` dir in each workflow as shared scratch space within the `main` branch. There is no expectation that anything here is maintained.
  - Maintain `workflow_<workflow>.ipynb` as the latest (stable) version of the workflow.
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
- 2023 - 2024: Chan Zuckerberg Initiative. Learn more in the [grant announcement](https://blog.bokeh.org/announcing-czi-funding-for-bokeh-for-bioscience-5f74426c011a).


---

### Why Neuroscience?

Multiple (probably all) HoloViz+Bokeh developers believe that helping people through the furthering of clinically impactful science is a worthy pursuit and in need of a data visualization boost.

### Why HoloViz+Bokeh?

We hypothesize that the visualization (perception through the eyes) within the process of working always benefits from having the option to suddenly become interactive and shareable - allowing for the poking or plucking, pushing or pulling, drilling in or out, grouping or separating, and sending or receiving of what would otherwise be a static snapshot of the data. The combined use of HoloViz and Bokeh tools provides the interactivity and shareability needed to support research as a collective action rather than a collection of solitary observations.
