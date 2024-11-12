# Multichannel Streaming Application

![](./assets/streaming_header.png)

## Prerequisites

| What? | Why? |
| --- | --- |
| [Index: Intro, Workflows, Extensions](./index.ipynb) | For context and workflow selection/feature guidance |
| [Recommended Workflow](./multichan.ipynb) | For live downsampling with in-memory Pandas DataFrame |

## Overview

For an introduction, please visit the ['Index'](./index.ipynb) page. 

This tutorial guides you through building a multichannel timeseries streaming application, visualizing either CPU usage or an EEG data file as if it was streaming live over a network interface. The application shows how to create controls like selecting the data source and starting, pausing, and stoping the data stream.

### Key Software:
- **[LSL](https://github.com/sccn/labstreaminglayer)** and **[MNE-LSL](https://mne.tools/mne-lsl/stable/index.html)**: Widely used neuroscience, Lab Streaming Layer (LSL) helps with the collection of measurement time series in research experiments. Here, it is used via the MNE-LSL python package to set up a mock live stream from a file on disk.


## Imports and Configuration



```python
import abc
import time
import uuid
import numpy as np
import pandas as pd
import psutil

import holoviews as hv
from holoviews.streams import Buffer
import panel as pn
import param
from bokeh.palettes import Category20

import mne
from mne_lsl.datasets import sample
from mne_lsl.player import PlayerLSL
from mne_lsl.stream import StreamLSL

hv.extension('bokeh')
pn.extension()

```

## Creating Data Sources

We will create two data sources, and a python class to handle the management of each:
1. **CPU Usage:** Streams CPU usage percentages per core.
2. **EEG Usage:** Streams EEG data from a sample dataset.

Let's create a sort of recipe (abstract base class) to ensure that each data source class contains certain methods. We want the class to tell us its channel names, positions, sampling interval, as well as to start up the stream, generate some data, and stop the stream.


```python
class DataSource(abc.ABC):
    @abc.abstractmethod
    def get_channel_names(self):
        pass

    @abc.abstractmethod
    def get_channel_positions(self):
        pass
    
    @property
    @abc.abstractmethod
    def sampling_interval(self):
        pass
        
    @abc.abstractmethod
    def generate_data(self):
        pass
    
    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass
```

### CPU Usage Data Source
The `CPU_Usage` class streams CPU usage data using the `psutil` library. This acts as a sort of simple test bench for us to stream some real data and make sure the plotting application is working. Whenever `generate_data` is called, it will return a timestamped measurement of cpu usage across my computer's cores.


```python
class CPU_Usage(DataSource):  # Now inherits from DataSource
    def __init__(self, sampling_interval=0.25, buffer_size=5):
        # Get total number of logical CPU cores
        self.num_cores = psutil.cpu_count(logical=True)
        
        self._sampling_interval = sampling_interval
        self.streaming = False
        
        # Create channel names for each CPU core
        self.channel_names = [f'CPU_{i}' for i in range(self.num_cores)]
        self._channel_positions = None  # No physical positions for CPU cores
        self.buffer_size = buffer_size
    
    @property
    def sampling_interval(self):
        return self._sampling_interval
    
    def get_channel_names(self):
        return self.channel_names
    
    def get_channel_positions(self):
        return self._channel_positions
    
    def start(self):
        self.streaming = True
    
    def stop(self):
        self.streaming = False
    
    def generate_data(self):
        if not self.streaming:
            return pd.DataFrame(columns=['time'] + self.channel_names)
            
        # Get CPU usage for each core
        cpu_percent = psutil.cpu_percent(percpu=True)
        if cpu_percent:
            timestamp = pd.Timestamp.now()
            data = {'time': [timestamp]}
            for ch, usage in zip(self.channel_names, cpu_percent):
                data[ch] = usage
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=['time'] + self.channel_names)
```

### LSL File Stream Data Source
The `LSL_EEG_File_Stream` class streams EEG data via a mock `LSL` live stream from a saved file, using utilities from the `mne` and `mne_lsl` libraries.

This class is a bit more involved than the last and requires us to handle the stream setup (start) and teardown (stop) in a particular way, according to the [PlayerLSL](https://mne.tools/mne-lsl/stable/generated/api/mne_lsl.player.PlayerLSL.html) and [StreamLSL](https://mne.tools/mne-lsl/stable/generated/api/mne_lsl.stream.StreamLSL.html#mne_lsl.stream.StreamLSL) docs. However, the idea is the same, when `generate_data` is called, it will return timestamped dataframe of the next block of channel measurements.



```python
class LSL_EEG_File_Stream(DataSource):
    def __init__(self, fname, picks='eeg'):
        # Generate unique identifier for this stream instance
        self.source_id = uuid.uuid4().hex
        self.fname = fname
        self.name = f"MNE-LSL-{self.source_id}"
        
        self.chunk_size = 20
        
        # Set up LSL streaming components
        self.player = PlayerLSL(
            self.fname,
            chunk_size=self.chunk_size,
            source_id=self.source_id,
            name=self.name
        )
        
        self.stream = StreamLSL(
            bufsize=2,
            name=self.name,
            source_id=self.source_id,
        )
        
        self._sampling_interval = 0.02  # 20ms update rate
        self.streaming = False
        self.picks = picks
        self.reference = "average"
        
        # Set up channel names based on picks
        if self.picks == 'eeg':
            ch_type_indices = mne.channel_indices_by_type(self.player.info)['eeg']
            self.channel_names = [self.player.ch_names[i] for i in ch_type_indices]
        else:
            self.channel_names = self.picks
            
        # Get channel positions from standard 10-05 montage
        montage = mne.channels.make_standard_montage("standard_1005")
        positions = montage.get_positions()['ch_pos']
        
        # Store positions for channels present in the montage
        self.channel_positions = []
        for ch in self.channel_names:
            if ch in positions:
                pos = positions[ch]
                self.channel_positions.append({
                    'xpos': pos[0],
                    'ypos': pos[1],
                    'ch': ch,
                })
    
    def get_channel_names(self):
        return self.channel_names
    
    def get_channel_positions(self):
        return self.channel_positions
        
    @property
    def sampling_interval(self):
        return self._sampling_interval
        
    def start(self):
        if not self.streaming:
            self.player.start()
            # Allow time for stream initialization
            time.sleep(0.1)
            
            try:
                self.stream.connect(timeout=5.0)
            except RuntimeError as e:
                print("Failed to connect to LSL stream")
                self.player.stop()
                raise
                
            self.stream.pick(self.picks)
            if self.reference:
                self.stream.set_eeg_reference(self.reference)
            self.streaming = True
    
    def stop(self):
        if self.streaming:
            self.stream.disconnect()
            self.player.stop()
            self.streaming = False
    
    def generate_data(self):
        if not self.streaming:
            return pd.DataFrame(columns=['time'] + self.channel_names)
        
        # Collect all new samples since last call
        data, ts = self.stream.get_data(
            self.stream.n_new_samples / self.stream.info["sfreq"],
            picks=self.channel_names
        )
        
        if data.size > 0:
            new_data = pd.DataFrame({'time': ts})
            for i, ch in enumerate(self.channel_names):
                new_data[ch] = data[i]
            return new_data
        else:
            return pd.DataFrame(columns=['time'] + self.channel_names)
```

## Building the Streaming Application
The StreamingApp class below handles the user interface and streaming logic, integrating the data sources with interactive controls. Comments are included for each part of the code that might need additional context.


```python
class StreamingApp(param.Parameterized):
    def __init__(self, data_sources, notebook=False, buffer_length_samples=10000):
        # param.Parameterized enables reactive updates between components
        super().__init__()
        self.data_sources = data_sources
        self.notebook = notebook
        self.initial_time = None  # Used to normalize timestamps relative to stream start

        # Create mappings for the data source selector dropdown
        self.data_source_names = [type(ds).__name__ for ds in data_sources]
        self.data_source_instances = {type(ds).__name__: ds for ds in data_sources}
        self.data_source = self.data_source_names[0]  # Default selection

        # Sets up channel names and their color mapping based on the selected data source
        self.update_channel_names()
        
        self.buffer_length = buffer_length_samples
        # Buffer stores the most recent data points in a circular fashion
        self.buffer = Buffer(data=self.initial_data(), length=self.buffer_length)
        
        # Stream control attributes
        self.streaming = False
        self.paused = False
        self.task = None        # Will store the periodic callback for data updates
        self.data_generator = None  # Reference to active data source instance
        
        # Initialize UI components
        self.create_widgets()
        self.create_layout()

    def update_channel_names(self):
        data_source_instance = self.data_source_instances[self.data_source]
        self.channel_names = data_source_instance.get_channel_names()
        
        # Create a consistent color mapping that works for any number of channels
        palette = Category20[20]
        self.color_mapping = {
            ch: palette[i % len(palette)] 
            for i, ch in enumerate(self.channel_names)
        }
        
        self.current_sampling_interval = data_source_instance.sampling_interval
        
        # Reset buffer when channel configuration changes
        if hasattr(self, 'buffer'):
            self.buffer.clear()
            self.buffer.data = self.initial_data()
    
    def initial_data(self):
        # Create empty DataFrame with time and channel columns
        return pd.DataFrame({'time': [], **{ch: [] for ch in self.channel_names}})
    
    def create_widgets(self):
        # Data source selection dropdown
        self.data_source_widget = pn.widgets.Select(
            name='Data Source',
            options=self.data_source_names,
            value=self.data_source
        )
        self.data_source_widget.param.watch(self.on_data_source_change, 'value')
    
        # Stream control radio buttons with custom styling for active state
        self.radio_group = pn.widgets.RadioButtonGroup(
            name='Stream Control',
            options=['Start', 'Pause', 'Stop'],
            value='Stop',
            button_type='default',
            sizing_mode='stretch_width',
            stylesheets=["""
                :host(.solid) .bk-btn.bk-btn-default.bk-active {
                    background-color: #b23c3c;
                }
            """]
        )
        self.radio_group.param.watch(self.handle_state_change, 'value')

    def on_data_source_change(self, event):
        # Stop any existing stream before switching data sources
        self.stop_stream()
        self.data_source = event.new
        self.update_channel_names()
        
        # Reset visualization with empty plots
        self.main_streaming_pane.object = self.bare_stream_plot()
        self.position_pane.object = self.bare_pos_plot()
    
    def handle_state_change(self, event):
        # Route radio button selections to appropriate stream control methods
        if event.new == 'Start':
            self.start_stream()
        elif event.new == 'Pause':
            self.pause_stream()
        elif event.new == 'Stop':
            self.stop_stream()
    
    def create_layout(self):
        # Initialize main visualization panes with empty plots
        self.position_pane = pn.pane.HoloViews(self.bare_pos_plot())
        self.main_streaming_pane = pn.pane.HoloViews(self.bare_stream_plot())
    
        if self.notebook:
            # Notebook layout: Sidebar and main plot side by side
            self.layout = pn.Row(
                pn.Column(
                    self.data_source_widget,
                    self.radio_group,
                    self.position_pane,
                    width=300,
                ),
                self.main_streaming_pane,
                align='start',
            )
        else:
            # Standalone app layout: Using Panel's FastListTemplate
            sidebar = pn.Column(
                pn.WidgetBox(
                    self.data_source_widget,
                    self.radio_group,
                ),
                self.position_pane,
                sizing_mode='stretch_width',
            )
            self.template = pn.template.FastListTemplate(
                main=[self.main_streaming_pane],
                sidebar=[sidebar],
                title="Multi-Channel Streaming App",
                theme="dark",
                accent="#2e008b",
            )


    def start_stream(self):
        if not self.streaming:
            # Use context manager to show loading state while setting up stream
            with self.main_streaming_pane.param.update(loading=True):
                # print('starting stream')
                self.streaming = True
                self.paused = False
                
                # Initialize data generator and visualization
                self.data_generator = self.data_source_instances[self.data_source_widget.value]
                self.position_pane.object = self.create_position_plot()
                self.data_generator.start()
                self.buffer.clear()
                self.initial_time = None  # Reset initial time when starting new stream
                
                # Set up dynamic plotting with the buffer as the data stream
                self.main_streaming_pane.object = hv.DynamicMap(
                    self.create_streaming_plot, 
                    streams=[self.buffer]
                )
                
                # Start periodic data collection
                sampling_interval_ms = int(self.data_generator.sampling_interval * 1000)
                self.task = pn.state.add_periodic_callback(
                    self.stream_data, 
                    period=sampling_interval_ms, 
                    count=None
                )
        
        # Resume from paused state
        elif self.streaming and self.paused:
            self.paused = False
            if self.task is None:
                sampling_interval_ms = int(self.data_generator.sampling_interval * 1000)
                self.task = pn.state.add_periodic_callback(
                    self.stream_data, 
                    period=sampling_interval_ms, 
                    count=None
                )
    
    def pause_stream(self):
        # print('pause stream')
        if self.task:
            self.task.stop()
            self.task = None
        self.paused = True
    
    def stop_stream(self):
        # print('stop stream')
        if self.streaming:
            # Clean up streaming resources
            self.streaming = False
            self.paused = False
            if self.task:
                self.task.stop()
                self.task = None
            if self.data_generator is not None:
                self.data_generator.stop()
                
            # Reset UI and internal state
            self.radio_group.value = 'Stop'
            self.main_streaming_pane.object = self.bare_stream_plot()
            self.buffer.clear()
            self.buffer.data = self.initial_data()
            self.data_generator = None
            self.initial_time = None
    
    def stream_data(self):
        if not self.streaming or self.paused:
            return
        # Panel's unlocked context manager prevents callback deadlocks
        with pn.io.unlocked():
            new_data_df = self.data_generator.generate_data()
            if not new_data_df.empty:
                self.buffer.send(new_data_df)

    def create_streaming_plot(self, data):
        overlays = {}
        
        if not data.empty and 'time' in data.columns:
            # Store first timestamp to normalize all times relative to stream start
            if self.initial_time is None:
                self.initial_time = data['time'].iloc[0]
            
            data = data.copy()  # Create copy to avoid modifying the buffer's data
            data['time'] = (data['time'] - self.initial_time).round(2)
        
        # Create a curve for each channel's data
        for ch in self.channel_names:
            if ch in data.columns and not data[ch].dropna().empty:
                curve = hv.Curve(
                    (data['time'], data[ch]), 
                    'time', 'channel', 
                    label=ch
                ).opts(
                    line_width=2,
                    color=self.color_mapping[ch],
                    subcoordinate_y=True,  # Enables multiple y-axes
                )
                overlays[ch] = curve
                
        if overlays:
            # Combine all channel curves into a single plot
            ndoverlay = hv.NdOverlay(overlays).apply.opts(
                show_legend=False,
                responsive=True,
                min_height=600,
                framewise=True,  # Ensures proper axis scaling
                title='',
                xlabel='Time (s)',
                ylabel='Amplitude',
            )
            return ndoverlay
        else:
            return self.empty_stream_plot()
    
    def create_position_plot(self):
        channel_positions = self.data_generator.get_channel_positions()
        if channel_positions:
            # Create DataFrame with channel positions and colors
            df = pd.DataFrame(self.data_generator.channel_positions)
            df['clr'] = df['ch'].apply(lambda x: self.color_mapping.get(x, 'grey'))
            
            # Create interactive scatter plot of channel positions
            points = hv.Points(
                df, ['xpos', 'ypos'], 
                vdims=['ch', 'clr']
            ).opts(
                color='clr', 
                size=20, 
                alpha=.5, 
                tools=['hover'], 
                marker='circle'
            )
            
            # Add channel labels to the plot
            labels = hv.Labels(
                df, ['xpos', 'ypos'], 'ch'
            ).opts(
                text_color='black', 
                text_font_size='8pt'
            )
            
            # Combine points and labels
            plot = (points * labels).opts(
                xaxis=None, yaxis=None, axiswise=True,
                height=300, responsive=True, shared_axes=False,
                title='Channel Position'
            )
            return plot
        return self.bare_pos_plot()
    
    def bare_stream_plot(self, min_height=600):
        # Create an empty plot with basic styling
        curve = hv.Curve([]).opts(
            yaxis='bare', 
            xaxis='bare', 
            min_height=600, 
            responsive=True
        )
        return curve
    
    def empty_stream_plot(self):
        # Create empty curves for each channel
        empty_curves = {
            ch: hv.Curve([]).relabel(ch).opts(subcoordinate_y=True) 
            for ch in self.channel_names
        }
        ndoverlay = hv.NdOverlay(empty_curves).opts(
            legend_position='right',
            responsive=True,
            min_height=600,
            title=''
        )
        return ndoverlay
    
    def bare_pos_plot(self):
        # Create an empty position plot with basic styling
        points = hv.Points([]).opts(
            xaxis=None, 
            yaxis=None, 
            axiswise=True,
            height=300, 
            responsive=True, 
            shared_axes=False,
            title='Channel Position'
        )
        return points
    
    def create_servable_app(self):
        # Return appropriate layout based on context
        if self.notebook:
            return self.layout.servable()
        else:
            return self.template.servable()
```

### Running the Application
Instantiate the data sources and create the application.


```python
data_source_cpu_usage = CPU_Usage()

# display a subset of eeg channels with 'picks'
picks=['F4', 'F7', 'FC5', 'FC2', 'T7', 'CP2', 'CP6', 'P4', 'P7', 'O1', 'O2']
data_source_eeg_usage = LSL_EEG_File_Stream(
    sample.data_path() / "sample-ant-raw.fif",
    picks=picks,
)

app = StreamingApp(data_sources=[data_source_eeg_usage, data_source_cpu_usage], notebook=True)
app.create_servable_app()
```

## debug.. check the data using mne visualization


```python
raw = mne.io.read_raw_fif(sample.data_path() / "sample-ant-raw.fif", preload=True)
raw.set_eeg_reference("average")

with mne.viz.use_browser_backend('matplotlib'):
    raw.plot(duration=3, picks=picks, show_scrollbars=False,)
```


```python
## yea things don't look right. I think I should not be using time from initial time and instead just use the timestamps from the data file as they are.. and then fix whatever is going on with the data display
```

## Using the Application
- **Select Data Source:** Use the dropdown to select data source.
- **Control Streaming:**
  - Click **Start** to begin streaming data from the selected source.
  - Click **Pause** to temporarily halt data updates without stopping the stream.
  - Click **Stop** to stop data updates and the data source itself.
- **Switching Data Sources:**
  - When you select a different data source, the app automatically stops the current data source before starting the new one.

## Conclusion
We've built a real-time multichannel streaming application that can handle different data sources, including EEG data and CPU usage and that can be extended and customized for various real-time data streaming needs.

## What Next?
- Customization: Modify the application to include additional data sources or customize the visualization options.
- Data Analysis: Extend the application to include data analysis features such as filtering, feature extraction, or event detection.
- Deployment: Change `notebook=False` in the last code cell and deploy the application as a standalone web app using `panel serve streaming.ipynb --show`. The standalone web app styling looks like this:
![](./assets/streaming_standalone.png)

## Related Resources

| What? | Why? |
| --- | --- |
|[MNE-Python Docs](https://mne.tools/stable/index.html)|	For more information on EEG data handling and analysis |


```python

```
