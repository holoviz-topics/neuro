# Benchmarking

`hvneuro` uses [Playwright for Python](https://playwright.dev/python/docs/intro) and [ASV](https://asv.readthedocs.io) for benchmarking. Playwright automates interaction with the web browser, ASV controls the benchmarking process so that it is statistically valid and repeatable.

## Installing ASV

Benchmarks must be run from a clone of the `hvneuro` github repo. ASV creates and uses isolated virtual environments for benchmarking, so the running of benchmarks needs to be performed from within a Python environment that has access to both `asv` and `virtualenv`. This could be a `conda`, `pyenv` or `venv` for example.

Example setup using `conda`:
```
conda create -n hvneuro_asv python=3.11
conda activate hvneuro_asv
conda install -c conda-forge asv virtualenv "nodejs>=18"
```

# Running benchmarks

To run all benchmarks:
```
cd benchmarks
asv run -e
```

`-e` allows for stdout to be displayed.
Use `-v` for more verbose output from asv.

The first time this is run it creates a machine file to store information about your machine.  Then a virtual environment is created and each benchmark is run multiple times to obtain a statistically valid benchmark time.

The virtual environment contains `hvneuro` and its dependencies as defined in the top-level `pyproject.toml` file. It also contains `playwright`, the latest version of `chromium` as installed by `playwright`, and a particular branch of `bokeh` that contains extra code to record when the canvas is rendered. The latter is compiled by source and extra dependencies may be required for this to work on all test machines (to be determined).

The `-e` flag catches and displays stderr after the benchmark results. This should be free of errors but may contain some warnings.

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

## Debugging
Here are some thoughts on debugging benchmarks. So far when things go wrong it is usually due to communications or timeout issues, and everything just freezes making it difficult to debug. What I do is limit the set of `params` for the benchmark in question and turn off the browser `headless` mode, i.e. this change line in `base.py`:
```python
self._browser = playwright.chromium.launch(headless=True)
```
into
```python
self._browser = playwright.chromium.launch(headless=False)
```
Then run the benchmark in quick mode, e.g. something like `asv run -b Panel -e -q` and the browser will appear. If the benchmark is waiting for something to happen you can open the browser console to see what is going on. Sometimes adding extra timeouts to the benchmark helps, otherwise they can run too fast to really understand what is happening. 

To add an extra timeout, include the following in the base class before the playwright teardown:
```python
def playwright_teardown(self):
    self.page.wait_for_timeout(10000)
```

Futher, you may notices there is a lot of variation in timing.. You can record the individual timings using:
`asv run -b time_zoom --record-samples`
and then see them using something like:
`asv show 0388952c --details`
where the has comes from the output of `asv show`.