# Benchmarking

`hvneuro` uses [Playwright for Python](https://playwright.dev/python/docs/intro) and [ASV](https://asv.readthedocs.io) for benchmarking. Playwright automates interaction with the web browser, ASV controls the benchmarking process so that it is statistically valid and repeatable.

## Installing ASV

Benchmarks must be run from a clone of the `hvneuro` github repo. ASV creates and uses isolated virtual environments for benchmarking, so the running of benchmarks needs to be performed from within a Python environment that has access to both `asv` and `virtualenv`. This could be a `conda`, `pyenv` or `venv` for example.

Example setup using `conda`:
```
conda create -n hvneuro_asv
conda activate hvneuro_asv
pip install asv virtualenv
```

# Running benchmarks

To run all benchmarks:
```
cd benchmarks
asv run
```

The first time this is run it creates a machine file to store information about your machine.  Then a virtual environment is created and each benchmark is run multiple times to obtain a statistically valid benchmark time.

The virtual environment contains `hvneuro` and its dependencies as defined in the top-level `pyproject.toml` file. It also contains `playwright`, the latest version of `chromium` as installed by `playwright`, and a particular branch of `bokeh` that contains extra code to record when the canvas is rendered. The latter is compiled by source and extra dependencies may be required for this to work on all test machines (to be determined).

# Viewing benchmark results

To list benchmark runs use
```
asv show
```

Initially this will just list the `hvneuro` commit that the benchmarks are run against. To display the benchmark timings for this commit use:
```
asv show <commit hash>
```
using enough of the commit hash to uniquely identify it.

ASV ships with its own simple webserver to interactively display the results in a webbrowser.  To use this:
```
asv publish
asv preview
```
and then open a web browser at the URL specified.

## Configuration

ASV configuration information is stored in `benchmarks/asv.conf.json`.  This includes a list of branches to benchmark.  If you are using a feature branch and wish to benchmark the code in that branch rather than `main`, edit `asv.conf.json` to change the line:
```
"branches": ["main"],
```
