# Waveform

![Status](https://img.shields.io/badge/status-in%20progress-orange)

## Summary
---

This waveform workflow will demonstrate oscilloscope-style display of action potential
waveform snippets.

- **Handling large datasets:** Benchmarking and providing solutions for large data
  handling challenges to ensure smooth performance.

- **Scale bar:** A visual reference for signal amplitude, aiding in the interpretation
  of the waveforms.

- **Waveform grouping:** Colored by source of signal


## Links:
---

- [Workflow demo](./workflow_ephys-viewer.ipynb)

- [Electrophysiology notes](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes)

- [All waveform workflow Issues/PRs](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*waveform*%22). *(Bulleted links below for feature-specific tasks)*


## Prioritized Tasks (Features/Bottlenecks)
---

- [`large-data-handling`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*large-data-handling*%22) (lead: `@ianthomas23`): Benchmark and solve large data handling
  - The unique challenge here is overlaying a very large number of lines

- [`scale-bar`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*scale-bar*%22)
  (lead: `@mattpap`)

- [`waveform-color-group`](https://github.com/orgs/holoviz-topics/projects/1/views/1?filterQuery=neuro-labels%3A%22*waveform-color-group*%22): coloring per neuron/unit/group with datashading and interactivity


**Wishlist/Ideas:**


## Primary Plot Specifications
---

**Axis specs:**
- x
  - type, label: continuous, `time`
  - typical resolution: 0.03 ms/sample (30 kHz)
  - typical extent: < 5 ms
- y
  - type, label: continuous, `time`
  - typical resolution: microvolts (uV)
  - typical extent: ~ 50-500 uV for extracellular, but varies up to ~ 1 mV
    depending on a number of factors.
  
## Data
---

### Format, size and other specs
- See Wiki > [Electrophysiology notes >
  Data](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes)

### Generated Data
- `neurodatagen.ephys`
  - `load_waveform_templates`: Load real waveform templates from file
  - `create_noisy_waveforms`: Generate a list of noisy spike waveforms based on a given input waveform template.
    ```python
    # Example usage:
    i_template = 100
    noise_std_percent = 70
    n_spikes = 1

    wf = load_waveform_templates()
    template_wf = wf.iloc[i_template]
    noisy_wf = create_noisy_waveforms(template_wf.values, noise_std_percent, n_spikes)

    ```
### Real Data
- See Wiki > [Electrophysiology notes > Real
  Data](https://github.com/holoviz-topics/neuro/wiki/Electrophysiology-notes#listssources-of-real-data)

## Future Directions
---

- Optimize for NWB 2.0 format
- Demonstrate biomedical/translational use-case
- Try streaming