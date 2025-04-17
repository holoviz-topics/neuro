# [HoloViz+Bokeh for Neuroscience](https://github.com/holoviz-topics/neuro)

> [!WARNING]
> This repository is a development, ideation, and archival space.

> [!WARNING]
> Users, to run the latest workflow notebooks, please go [here](https://examples.holoviz.org/gallery/neuroscience), choose a workflow, download the project, and follow the [instructions](https://examples.holoviz.org/getting_started.html).


![https://blog.holoviz.org/posts/czi_r5/](https://github.com/holoviz-dev/blog/blob/main/posts/czi_r5/images/czi_r5.png)
Read about progress on our [Blog](https://github.com/holoviz-dev/blog/blob/main/posts/czi_r5/images/czi_r5.png)!

## Why does Neuroscience need HoloViz+Bokeh?

We hypothesize the process of science stands to benefit from having the option to suddenly become interactive and shareable - allowing for the poking or plucking, pushing or pulling, drilling in or out, grouping or separating, and sending or receiving of what would otherwise be a static snapshot of the data. The combined use of HoloViz and Bokeh tools could provide the interactivity, shareability, and scalability needed to support research as a collective action rather than a collection of solitary observations.

### What is the purpose of this GitHub repository?

One of our overall goals is to facilitate the creation of fully open, reproducible,
OS-independent, browser-based workflows for biomedical research primarily using
sustainable, domain-independent visualization tools. In support of this
goal, this repository is the **development ground for optimization of
[HoloViz](https://github.com/holoviz/) and [Bokeh](https://github.com/bokeh/bokeh) tools within the realm of neuroscience.**

**Specific Repo objectives:**
  
- **Workflow Development:** Host the development versions of workflows, facilitating consistency and code sharing across them.
- **Collaboration Hub:** Foster collaborative efforts between the developer teams and scientific collaborators outside these groups - aiming to effectively tailor development to specific requirements of the neuroscience community.
- **Project Management:** Track ideas, feedback, requirements, specifications, issues, requests, topic research, and progress.
- **Host Domain-Specific Scripts:** For instance, simulated data generators.
- **Temporarily Host Benchmark Tooling:** Eventually, to be be migrated to a dedicated, domain-independent repository.

## **Workflows**:

| Title | Example Modality | Thumbnail | Info & Links | Description |
| --- | --- | --- | --- | --- |
| Multi-Channel Timeseries | eeg, ephys | <a href="https://github.com/holoviz-topics/examples/blob/main/multichannel_timeseries/thumbnails/index.png"><img src="https://github.com/holoviz-topics/examples/blob/main/multichannel_timeseries/thumbnails/index.png" alt="Multi-Channel Timeseries" width="300"></a> | [website](https://examples.holoviz.org/gallery/multichannel_timeseries/0_multichan.html), [notebook](https://github.com/holoviz-topics/examples/blob/main/multichannel_timeseries/0_multichan.ipynb) | Synchronized examination of stacked time-series with large data handling, scale bar, annotations, minimap, and signal grouping.
| Multi-Channel Timeseries for Large Data | eeg, ephys | <a href="https://github.com/holoviz-topics/examples/blob/main/multichannel_timeseries/thumbnails/large_multichan.png"><img src="https://github.com/holoviz-topics/examples/blob/main/multichannel_timeseries/thumbnails/large_multichan.png" alt="Multi-Channel Timeseries" width="300"></a> | [website](https://examples.holoviz.org/gallery/multichannel_timeseries/1_large_multichan.html), [notebook](https://github.com/holoviz-topics/examples/blob/main/multichannel_timeseries/1_large_multichan.ipynb) | For timeseries datasets larger than available RAM. Utilizes a multi-resolution data-pyramid approach.
| Time Lapse Microscopy | miniscope imaging | <a href="https://github.com/holoviz-topics/examples/blob/main/timelapse_microscopy/thumbnails/timelapse_microscopy.png"><img src="https://github.com/holoviz-topics/examples/blob/main/timelapse_microscopy/thumbnails/timelapse_microscopy.png" alt="Time Lapse Microscopy" width="300"></a> | [website](https://examples.holoviz.org/gallery/timelapse_microscopy/timelapse_microscopy.html), [notebook](https://github.com/holoviz-topics/examples/blob/main/timelapse_microscopy/timelapse_microscopy.ipynb) | Efficient visualization of deep 2D calcium imaging movies with, playback controls, 2D annotation, scale bar, and linked time views. |
| Volumetric Imaging | electron microscopy, histology | <a href="https://github.com/holoviz-topics/examples/blob/main/volumetric_imaging/thumbnails/volumetric_imaging.png"><img src="https://github.com/holoviz-topics/examples/blob/main/volumetric_imaging/thumbnails/volumetric_imaging.png" alt="Neuroglancer Notebook" width="300"></a> | [website](https://examples.holoviz.org/gallery/volumetric_imaging/volumetric_imaging.html), [notebook](https://github.com/holoviz-topics/examples/blob/main/volumetric_imaging/volumetric_imaging.ipynb) | Notebook-based workflow for visualizing 3D volumetric data in a [Neuroglancer](https://github.com/google/neuroglancer?tab=readme-ov-file) application|
| Streaming Timeseries | eeg, ephys | <a href="https://github.com/holoviz-topics/examples/blob/main/streaming_timeseries/thumbnails/streaming_timeseries.png"><img src="https://github.com/holoviz-topics/examples/blob/main/streaming_timeseries/thumbnails/streaming_timeseries.png" alt="Neuroglancer Notebook" width="300"></a> | [website](https://examples.holoviz.org/gallery/streaming_timeseries/streaming_timeseries.html), [notebook](https://github.com/holoviz-topics/examples/blob/main/streaming_timeseries/streaming_timeseries.ipynb) | Stream live from Lab Streaming Layer (LSL) data sources|

--- 

## **Workflows planned or in development**
| Title | Example Modality | Thumbnail | Info & Links | Description |
| --- | --- | --- | --- | --- |
| Waveform | ephys | <a href="./workflows/waveform_snippets/workflow_waveform.ipynb"><img src="./workflows/waveform_snippets/assets/230524_waveform.png" alt="Waveform" width="300"></a> | :warning:![Status](https://img.shields.io/badge/status-in%20progress-orange) <br>| Oscilloscope-style display of action potential waveform snippets |
| Spike Raster | ephys | <a href="./workflows/spike-raster/workflow_spike-raster.ipynb"><img src="./workflows/spike_raster/assets/230524_spike-raster.png" alt="Spike Raster" width="300"></a> | :warning:![Status](https://img.shields.io/badge/status-in%20progress-orange) <br>| Efficient visualization of large-scale neuronal spike time data, with a simple API, aggregate views of spike counts, and spike-level metadata management |


## **Wishlist Workflows**:
- ![status: idea](https://img.shields.io/badge/status-idea-blue) Multimodal - Neural imaging, timeseries, and behavior.
- ![status: idea](https://img.shields.io/badge/status-idea-blue) Spike Motif
- ![status: idea](https://img.shields.io/badge/status-idea-blue) MNE integration
- ![status: idea](https://img.shields.io/badge/status-idea-blue) Minian CNMF Temporal update parameter exploration app long timeseries
- ![status: idea](https://img.shields.io/badge/status-idea-blue) Linked electrode-array layout

## Dissemination
- Workflows will be shared with the broader scientific community as they are ready. The first round of workflows were released at the end of 2024. Completed workflows will be listed on the [HoloViz Examples Gallery](https://examples.holoviz.org/gallery/neuroscience.html), while select aspects will also go into the relevant Bokeh and HoloViz documentation pages.
- Workflow progress was be presented at the [CZI open science](https://chanzuckerberg.com/science/programs-resources/open-science/) conference in Boston, MA in June 2024. 
- If you have ideas for where our workflows could be promoted, please reach out! We would love it if there was also a central place for bioscience workflows, like the Geoscience community has with [Project Pythia](https://projectpythia.org/).
- Read about progress on our [Blog](https://github.com/holoviz-dev/blog/blob/main/posts/czi_r5/images/czi_r5.png)!

## Get Involved
- We are actively looking for opportunities to deliver tutorials, workshops, or other educational resources to help researchers in underrepresented communities effectively utilize our tools. Reach out on [Discord](https://discord.gg/rb6gPXbdAr) if you want to brainstorm some ideas!
- Visit the [Community page on HoloViz.org](https://holoviz.org/community.html) for more ways to join the conversation.
- If you want to contribute to the workflows or underlying libraries, read on for installation and contribution instructions.


## Who is behind this effort?

This work is a collaboration between developers and scientists, and some developer-scientists. While some contributions are visible through the GitHub repo, many other contributions are less visible yet equally important.

Funding:
- 2023 - 2024: Chan Zuckerberg Initiative. Learn more in the [grant announcement](https://blog.bokeh.org/announcing-czi-funding-for-bokeh-for-bioscience-5f74426c011a).

## Need to contact us?
- Project Lead: Dr. Demetris Roumis (@droumis on [Discord](https://discord.gg/X6Eq9CvZZn))
- HoloViz Director: Dr. James (Jim) Bednar (@jbednar on [Discord](https://discord.gg/X6Eq9CvZZn))
- Bokeh Director: Bryan Van de Ven (bryan@bokeh.org)

---

# Contributors
## Installation for individual workflows with Conda

### Prerequisites
Before installing the workflow environments, make sure you have Miniconda installed. If not, you can download and install it from the [official site]([https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/projects/miniconda/en/latest/index.html#quick-command-line-install)).

### Initial Installation Steps

1. **Clone the Repository**: Clone the `neuro` repository to your local machine.
    ```bash
    git clone https://github.com/holoviz-topics/neuro.git
    ```

2. **Navigate to Workflow**: Change to the directory of the workflow you're interested in.
    ```bash
    cd neuro/workflows/<workflow>
    ```

3. **Create Environment**: Use `conda` to create a new environment from the `environment.yml` file.
    ```bash
    conda env create -f environment.yml
    ```

4. **Activate Environment**: After the environment is created, activate it.
    ```bash
    conda activate <environment>
    ```


### Updating Workflow Environments

If you've already installed a workflow environment and the `environment.yml` file has been updated, follow these steps to update the environment:

1. **Update Repository**: Pull the latest changes from the repository.
    ```bash
    git pull
    ```

2. **Navigate to Workflow**: Go to the directory of the workflow you're interested in.
    ```bash
    cd neuro/workflows/<workflow>
    ```

3. **Update Environment**: Update the existing Conda environment based on the latest `environment.yml` file.
    ```bash
    conda env update -f environment.yml --prune
    ```

The `--prune` option will remove packages from the environment not present in the updated `environment.yml` file.


---
## Resources for Contributing

- **Task Management:** As workflows are developed and honed, performance and UI bottlenecks will be identified and addressed. Some improvements for the workflows themselves will be within this repo, but many improvements will be in the appropriate underlying libraries within the [HoloViz](https://github.com/holoviz/), [Bokeh](https://github.com/bokeh), or other GitHub Organizations. We will do our best to track the disparate tasks related to these efforts into this 
[project board](https://github.com/orgs/holoviz-topics/projects/1).
- **Communication:** 
  - [HoloViz Discord #neuro channel](https://discord.gg/X6Eq9CvZZn) for real-time chat (if archived, post on the General HoloViz Discord channel)
  - [holoviz-topics/neuro GitHub repo issue
    tracker](https://github.com/holoviz-topics/neuro/issues)
- **Repo Structure and dev patterns:** 
    ```
    /workflows
      /example1
        readme_example1.md
        workflow_example1.ipynb
        environment.yml
        /dev
            date_example-workflow_task.ipynb
    ```
  - Use `readme_<workflow>.md` for any essential workflow-specific info or links.
  - Maintain `workflow_<workflow>.ipynb` as the latest version of the workflow.
  - Each workflow should have an `environment.yml` with which to create a conda env
