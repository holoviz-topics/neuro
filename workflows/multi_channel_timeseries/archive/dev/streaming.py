# # %% Checkpoint 2 WORKING

# import numpy as np
# import pandas as pd
# import holoviews as hv
# import panel as pn
# import param
# from holoviews.streams import Buffer

# hv.extension('bokeh')
# pn.extension()

# class StreamingApp(param.Parameterized):
#     n_channels = param.Integer(default=5, bounds=(1, None))

#     def __init__(self, duration=10, sampling_interval=0.1, n_channels=5, notebook=False):
#         super().__init__(n_channels=n_channels)
#         self.duration = duration
#         self.sampling_interval = sampling_interval
#         self.notebook = notebook
#         self.channel_names = [f'Channel_{i+1}' for i in range(n_channels)]
#         self.buffer_length = int(self.duration / self.sampling_interval) + 1
#         self.streaming = False
#         self.paused = False
#         self.task = None

#         # Initialize the buffer here to avoid AttributeError
#         self.buffer = Buffer(data=self.initial_data(), length=self.buffer_length)

#         self.create_widgets()
#         self.create_layout()

#     def initial_data(self):
#         # No initial data
#         return pd.DataFrame({'time': [], **{ch: [] for ch in self.channel_names}})

#     # Removed the update_title method since we're not dynamically updating the title

#     def create_widgets(self):
#         self.radio_group = pn.widgets.RadioButtonGroup(
#             name='Stream Control',
#             options=['Start', 'Pause', 'Stop'],
#             value='Stop',
#             button_type='default',
#             sizing_mode='stretch_width',
#             # Style the active button color
#             stylesheets=[ """
#             :host(.solid) .bk-btn.bk-btn-default.bk-active {
#                 background-color: #b23c3c;
#             }
#             """]
#         )
#         self.radio_group.param.watch(self.handle_state_change, 'value')

#     def handle_state_change(self, event):
#         if event.new == 'Start':
#             self.start_stream()
#         elif event.new == 'Pause':
#             self.pause_stream()
#         elif event.new == 'Stop':
#             self.stop_stream()

#     def create_layout(self):
#         # Start with a blank plot
#         self.plot_pane = pn.pane.HoloViews(self.blank_bare_plot())
#         if self.notebook:
#             self.layout = pn.Column(
#                 self.radio_group,
#                 self.plot_pane,
#                 align='center',
#             )
#         else:
#             sidebar = pn.Column(
#                 pn.WidgetBox(
#                     self.radio_group,
#                 ),
#                 align='center',
#                 sizing_mode='stretch_width',
#             )
#             self.template = pn.template.FastListTemplate(
#                 main=[self.plot_pane],
#                 sidebar=[sidebar],
#                 title="Multi-Channel Streaming App",
#                 theme="dark",
#                 accent="#2e008b",
#             )

#     def start_stream(self):
#         if not self.streaming:
#             self.streaming = True
#             self.paused = False
#             self.current_time = 0
#             self.spike_added = {ch: False for ch in self.channel_names}
#             self.buffer.clear()
#             # Replace the plot with the live streaming plot
#             self.plot_pane.object = self.create_streaming_plot()
#             # Start the periodic callback
#             self.task = pn.state.add_periodic_callback(
#                 self.stream_data, period=int(self.sampling_interval * 1000), count=None
#             )
#         else:
#             self.paused = False
#             if self.task is None:
#                 # Restart the periodic callback if it was stopped
#                 self.task = pn.state.add_periodic_callback(
#                     self.stream_data, period=int(self.sampling_interval * 1000), count=None
#                 )

#     def pause_stream(self):
#         if self.task:
#             self.task.stop()
#             self.task = None
#         self.paused = True
#         print('pause')

#     def stop_stream(self):
#         self.streaming = False
#         self.paused = False
#         if self.task:
#             self.task.stop()
#             self.task = None
#         self.radio_group.value = 'Stop'
#         print('stop')
#         self.plot_pane.object = self.blank_bare_plot()

#     def create_streaming_plot(self):
#         # Create the streaming plot using DynamicMap
#         def create_plot(data):
#             overlays = {}
#             for ch in self.channel_names:
#                 if ch in data.columns and not data[ch].dropna().empty:
#                     # Set the label to match the key
#                     curve = hv.Curve((data['time'], data[ch]), label=ch).opts(
#                         line_width=2,
#                         subcoordinate_y=True,
#                     )
#                     overlays[ch] = curve
#             if overlays:
#                 ndoverlay = hv.NdOverlay(overlays).apply.opts(
#                     legend_position='right',
#                     responsive=True,
#                     min_height=600,
#                     xlim=(0, self.duration),
#                     framewise=True,
#                     title='',
#                 )
#                 return ndoverlay
#             else:
#                 return self.blank_stream_plot()

#         dmap = hv.DynamicMap(create_plot, streams=[self.buffer])
#         return dmap

#     def blank_bare_plot(self):
#         return hv.Curve([]).opts(yaxis='bare', xaxis='bare', responsive=True)

#     def blank_stream_plot(self):
#         # Create an empty NdOverlay with the expected keys and labels
#         empty_curves = {ch: hv.Curve([]).relabel(ch).opts(subcoordinate_y=True,) for ch in self.channel_names}
#         ndoverlay = hv.NdOverlay(empty_curves).opts(
#             legend_position='right',
#             responsive=True,
#             min_height=600,
#             title=''  # Set a static title
#         )
#         return ndoverlay

#     def stream_data(self):
#         if not self.streaming or self.paused:
#             return
#         with pn.io.unlocked():
#             if self.current_time > self.duration:
#                 self.pause_stream()
#                 return

#             new_data = {'time': [self.current_time]}
#             for ch in self.channel_names:
#                 amplitude = np.sin(2 * np.pi * self.current_time / self.duration) * \
#                             (1 + np.random.normal(0, 0.1))
#                 # Optionally add a spike in the middle
#                 if not self.spike_added[ch] and 0.48 * self.duration <= self.current_time <= 0.52 * self.duration:
#                     amplitude += np.random.uniform(1.8, 1.9)
#                     self.spike_added[ch] = True
#                 new_data[ch] = amplitude

#             new_data_df = pd.DataFrame(new_data)
#             self.buffer.send(new_data_df)
#             self.current_time += self.sampling_interval

#     def create_servable_app(self):
#         if self.notebook:
#             return self.layout
#         else:
#             return self.template.servable()

# # Create and serve the streaming app
# app = StreamingApp(duration=10, sampling_interval=0.1, n_channels=5, notebook=False)
# app.create_servable_app()

# %% Checkpoint 2.1

# import numpy as np
# import pandas as pd
# import holoviews as hv
# import panel as pn
# import param
# from holoviews.streams import Buffer

# hv.extension('bokeh')
# pn.extension()

# import numpy as np
# import pandas as pd

# class HV_Sim_Live:
#     def __init__(self, duration, sampling_interval, n_channels, channel_names):
#         self.duration = duration
#         self.sampling_interval = sampling_interval
#         self.n_channels = n_channels
#         self.channel_names = channel_names
#         self.current_time = 0
#         self.spike_added = {ch: False for ch in self.channel_names}
    
#     def generate_data(self):
#         new_data = {'time': [self.current_time]}
#         for ch in self.channel_names:
#             amplitude = np.sin(2 * np.pi * self.current_time / self.duration) * \
#                         (1 + np.random.normal(0, 0.1))
#             # Optionally add a spike in the middle
#             if not self.spike_added[ch] and 0.48 * self.duration <= self.current_time <= 0.52 * self.duration:
#                 amplitude += np.random.uniform(1.8, 1.9)
#                 self.spike_added[ch] = True
#             new_data[ch] = amplitude
#         self.current_time += self.sampling_interval
#         return pd.DataFrame(new_data)


# class StreamingApp(param.Parameterized):
#     n_channels = param.Integer(default=5, bounds=(1, None))
#     data_source = param.ObjectSelector(default=None, objects=[])

#     def __init__(self, duration=10, sampling_interval=0.1, n_channels=5, notebook=False):
#         super().__init__(n_channels=n_channels)
#         self.duration = duration
#         self.sampling_interval = sampling_interval
#         self.notebook = notebook
#         self.channel_names = [f'Channel_{i+1}' for i in range(n_channels)]
#         self.buffer_length = int(self.duration / self.sampling_interval) + 1
#         self.streaming = False
#         self.paused = False
#         self.task = None

#         # Initialize the buffer here to avoid AttributeError
#         self.buffer = Buffer(data=self.initial_data(), length=self.buffer_length)

#         # Available data sources
#         self.available_data_sources = {
#             'HV_Sim_Live': HV_Sim_Live
#             # Add more data sources here if needed
#         }
#         self.data_source = 'HV_Sim_Live'  # Default selection

#         self.create_widgets()
#         self.create_layout()

#     def initial_data(self):
#         # No initial data
#         return pd.DataFrame({'time': [], **{ch: [] for ch in self.channel_names}})

#     def create_widgets(self):
#         # Dropdown widget for selecting data source
#         self.data_source_selector = pn.widgets.Select(
#             name='Data Source',
#             options=list(self.available_data_sources.keys()),
#             value=self.data_source
#         )

#         self.radio_group = pn.widgets.RadioButtonGroup(
#             name='Stream Control',
#             options=['Start', 'Pause', 'Stop'],
#             value='Stop',
#             button_type='default',
#             sizing_mode='stretch_width',
#             # Style the active button color
#             stylesheets=[ """
#             :host(.solid) .bk-btn.bk-btn-default.bk-active {
#                 background-color: #b23c3c;
#             }
#             """]
#         )
#         self.radio_group.param.watch(self.handle_state_change, 'value')

#     def handle_state_change(self, event):
#         if event.new == 'Start':
#             self.start_stream()
#         elif event.new == 'Pause':
#             self.pause_stream()
#         elif event.new == 'Stop':
#             self.stop_stream()

#     def create_layout(self):
#         # Start with a blank plot
#         self.plot_pane = pn.pane.HoloViews(self.blank_bare_plot())
#         if self.notebook:
#             self.layout = pn.Column(
#                 self.data_source_selector,
#                 self.radio_group,
#                 self.plot_pane,
#                 align='center',
#             )
#         else:
#             sidebar = pn.Column(
#                 pn.WidgetBox(
#                     self.data_source_selector,
#                     self.radio_group,
#                 ),
#                 align='center',
#                 sizing_mode='stretch_width',
#             )
#             self.template = pn.template.FastListTemplate(
#                 main=[self.plot_pane],
#                 sidebar=[sidebar],
#                 title="Multi-Channel Streaming App",
#                 theme="dark",
#                 accent="#2e008b",
#             )

#     def start_stream(self):
#         if not self.streaming:
#             self.streaming = True
#             self.paused = False
#             self.current_time = 0
#             # Initialize the selected data source
#             data_source_class = self.available_data_sources[self.data_source_selector.value]
#             self.data_generator = data_source_class(
#                 duration=self.duration,
#                 sampling_interval=self.sampling_interval,
#                 n_channels=self.n_channels,
#                 channel_names=self.channel_names
#             )
#             self.buffer.clear()
#             # Replace the plot with the live streaming plot
#             self.plot_pane.object = self.create_streaming_plot()
#             # Start the periodic callback
#             self.task = pn.state.add_periodic_callback(
#                 self.stream_data, period=int(self.sampling_interval * 1000), count=None
#             )
#         else:
#             self.paused = False
#             if self.task is None:
#                 # Restart the periodic callback if it was stopped
#                 self.task = pn.state.add_periodic_callback(
#                     self.stream_data, period=int(self.sampling_interval * 1000), count=None
#                 )

#     def pause_stream(self):
#         if self.task:
#             self.task.stop()
#             self.task = None
#         self.paused = True

#     def stop_stream(self):
#         self.streaming = False
#         self.paused = False
#         if self.task:
#             self.task.stop()
#             self.task = None
#         self.radio_group.value = 'Stop'
#         self.plot_pane.object = self.blank_bare_plot()

#     def create_streaming_plot(self):
#         # Create the streaming plot using DynamicMap
#         def create_plot(data):
#             overlays = {}
#             for ch in self.channel_names:
#                 if ch in data.columns and not data[ch].dropna().empty:
#                     # Set the label to match the key
#                     curve = hv.Curve((data['time'], data[ch]), label=ch).opts(
#                         line_width=2,
#                         subcoordinate_y=True,
#                     )
#                     overlays[ch] = curve
#             if overlays:
#                 ndoverlay = hv.NdOverlay(overlays).apply.opts(
#                     legend_position='right',
#                     responsive=True,
#                     min_height=600,
#                     xlim=(0, self.duration),
#                     framewise=True,
#                     title='',
#                 )
#                 return ndoverlay
#             else:
#                 return self.blank_stream_plot()

#         dmap = hv.DynamicMap(create_plot, streams=[self.buffer])
#         return dmap

#     def blank_bare_plot(self):
#         return hv.Curve([]).opts(yaxis='bare', xaxis='bare', responsive=True)

#     def blank_stream_plot(self):
#         # Create an empty NdOverlay with the expected keys and labels
#         empty_curves = {ch: hv.Curve([]).relabel(ch).opts(subcoordinate_y=True,) for ch in self.channel_names}
#         ndoverlay = hv.NdOverlay(empty_curves).opts(
#             legend_position='right',
#             responsive=True,
#             min_height=600,
#             title=''  # Set a static title
#         )
#         return ndoverlay

#     def stream_data(self):
#         if not self.streaming or self.paused:
#             return
#         with pn.io.unlocked():
#             if self.current_time > self.duration:
#                 self.pause_stream()
#                 return

#             # Use the data generator to get new data
#             new_data_df = self.data_generator.generate_data()
#             self.buffer.send(new_data_df)
#             self.current_time = self.data_generator.current_time

#     def create_servable_app(self):
#         if self.notebook:
#             return self.layout
#         else:
#             return self.template.servable()

# # Create and serve the streaming app
# app = StreamingApp(duration=10, sampling_interval=0.1, n_channels=5, notebook=False)
# app.create_servable_app()

# %% 2.2
# import numpy as np
# import pandas as pd
# import holoviews as hv
# import panel as pn
# import param
# import psutil  # Make sure to import psutil
# from holoviews.streams import Buffer

# hv.extension('bokeh')
# pn.extension()

# # Include HV_Sim_Live class from earlier
# class HV_Sim_Live:
#     def __init__(self, duration, sampling_interval, n_channels, channel_names):
#         self.duration = duration
#         self.sampling_interval = sampling_interval
#         self.n_channels = n_channels
#         self.channel_names = channel_names
#         self.current_time = 0
#         self.spike_added = {ch: False for ch in self.channel_names}
    
#     def generate_data(self):
#         new_data = {'time': [self.current_time]}
#         for ch in self.channel_names:
#             amplitude = np.sin(2 * np.pi * self.current_time / self.duration) * \
#                         (1 + np.random.normal(0, 0.1))
#             # Optionally add a spike in the middle
#             if not self.spike_added[ch] and 0.48 * self.duration <= self.current_time <= 0.52 * self.duration:
#                 amplitude += np.random.uniform(1.8, 1.9)
#                 self.spike_added[ch] = True
#             new_data[ch] = amplitude
#         self.current_time += self.sampling_interval
#         return pd.DataFrame(new_data)

# # New data source class HV_CPU_Usage
# class HV_CPU_Usage:
#     def __init__(self, channel_names):
#         self.channel_names = channel_names  # Names of CPU cores
#         self.num_cores = len(channel_names)
    
#     def generate_data(self):
#         cpu_percent = psutil.cpu_percent(percpu=True)
#         timestamp = pd.Timestamp.now()
#         data = {'time': [timestamp]}
#         for ch, usage in zip(self.channel_names, cpu_percent):
#             data[ch] = usage
#         return pd.DataFrame(data)

# class StreamingApp(param.Parameterized):
#     n_channels = param.Integer(default=5, bounds=(1, None))
#     # Removed the data_source_selector parameter to avoid conflict
    
#     def __init__(self, duration=10, sampling_interval=0.1, n_channels=5, notebook=False):
#         super().__init__(n_channels=n_channels)
#         self.duration = duration
#         self.sampling_interval = sampling_interval
#         self.notebook = notebook

#         # Initialize available data sources
#         self.available_data_sources = {
#             'HV_Sim_Live': HV_Sim_Live,
#             'HV_CPU_Usage': HV_CPU_Usage,
#             # Add more data sources here if needed
#         }
#         self.data_source = 'HV_Sim_Live'  # Default selection

#         # Initialize channel names based on the default data source
#         self.channel_names = []
#         self.update_channel_names()

#         self.buffer_length = int(self.duration / self.sampling_interval) + 1
#         self.streaming = False
#         self.paused = False
#         self.task = None

#         # Initialize the buffer here after channel names are set
#         self.buffer = Buffer(data=self.initial_data(), length=self.buffer_length)

#         self.create_widgets()
#         self.create_layout()

#     def update_channel_names(self):
#         if self.data_source == 'HV_Sim_Live':
#             self.channel_names = [f'Channel_{i+1}' for i in range(self.n_channels)]
#         elif self.data_source == 'HV_CPU_Usage':
#             self.num_cores = psutil.cpu_count(logical=True)
#             self.channel_names = [f'CPU_{i}' for i in range(self.num_cores)]
#         else:
#             self.channel_names = []
#         # Update buffer with new channel names if buffer is initialized
#         if hasattr(self, 'buffer'):
#             self.buffer.clear()
#             self.buffer.data = self.initial_data()

#     def initial_data(self):
#         # No initial data
#         return pd.DataFrame({'time': [], **{ch: [] for ch in self.channel_names}})

#     def create_widgets(self):
#         # Dropdown widget for selecting data source
#         self.data_source_widget = pn.widgets.Select(
#             name='Data Source',
#             options=list(self.available_data_sources.keys()),
#             value=self.data_source
#         )
#         # Watch for changes in the data source selector
#         self.data_source_widget.param.watch(self.on_data_source_change, 'value')

#         self.radio_group = pn.widgets.RadioButtonGroup(
#             name='Stream Control',
#             options=['Start', 'Pause', 'Stop'],
#             value='Stop',
#             button_type='default',
#             sizing_mode='stretch_width',
#             # Style the active button color
#             stylesheets=[ """
#             :host(.solid) .bk-btn.bk-btn-default.bk-active {
#                 background-color: #b23c3c;
#             }
#             """]
#         )
#         self.radio_group.param.watch(self.handle_state_change, 'value')

#     def on_data_source_change(self, event):
#         self.stop_stream()
#         self.data_source = event.new
#         self.update_channel_names()
#         # Update the plot
#         self.plot_pane.object = self.blank_bare_plot()

#     def handle_state_change(self, event):
#         if event.new == 'Start':
#             self.start_stream()
#         elif event.new == 'Pause':
#             self.pause_stream()
#         elif event.new == 'Stop':
#             self.stop_stream()

#     def create_layout(self):
#         # Start with a blank plot
#         self.plot_pane = pn.pane.HoloViews(self.blank_bare_plot())
#         if self.notebook:
#             self.layout = pn.Column(
#                 self.data_source_widget,
#                 self.radio_group,
#                 self.plot_pane,
#                 align='center',
#             )
#         else:
#             sidebar = pn.Column(
#                 pn.WidgetBox(
#                     self.data_source_widget,
#                     self.radio_group,
#                 ),
#                 align='center',
#                 sizing_mode='stretch_width',
#             )
#             self.template = pn.template.FastListTemplate(
#                 main=[self.plot_pane],
#                 sidebar=[sidebar],
#                 title="Multi-Channel Streaming App",
#                 theme="dark",
#                 accent="#2e008b",
#             )

#     def start_stream(self):
#         if not self.streaming:
#             self.streaming = True
#             self.paused = False
#             self.current_time = 0
#             # Initialize the selected data source
#             data_source_class = self.available_data_sources[self.data_source_widget.value]
#             if self.data_source_widget.value == 'HV_Sim_Live':
#                 self.data_generator = data_source_class(
#                     duration=self.duration,
#                     sampling_interval=self.sampling_interval,
#                     n_channels=self.n_channels,
#                     channel_names=self.channel_names
#                 )
#             elif self.data_source_widget.value == 'HV_CPU_Usage':
#                 self.data_generator = data_source_class(
#                     channel_names=self.channel_names
#                 )
#             self.buffer.clear()
#             # Replace the plot with the live streaming plot
#             self.plot_pane.object = self.create_streaming_plot()
#             # Start the periodic callback
#             self.task = pn.state.add_periodic_callback(
#                 self.stream_data, period=int(self.sampling_interval * 1000), count=None
#             )
#         else:
#             self.paused = False
#             if self.task is None:
#                 # Restart the periodic callback if it was stopped
#                 self.task = pn.state.add_periodic_callback(
#                     self.stream_data, period=int(self.sampling_interval * 1000), count=None
#                 )

#     def pause_stream(self):
#         if self.task:
#             self.task.stop()
#             self.task = None
#         self.paused = True

#     def stop_stream(self):
#         self.streaming = False
#         self.paused = False
#         if self.task:
#             self.task.stop()
#             self.task = None
#         self.radio_group.value = 'Stop'
#         self.plot_pane.object = self.blank_bare_plot()

#     def create_streaming_plot(self):
#         # Create the streaming plot using DynamicMap
#         def create_plot(data):
#             overlays = {}
#             for ch in self.channel_names:
#                 if ch in data.columns and not data[ch].dropna().empty:
#                     # Set the label to match the key
#                     curve = hv.Curve((data['time'], data[ch]), label=ch).opts(
#                         line_width=2,
#                         subcoordinate_y=True,
#                     )
#                     overlays[ch] = curve
#             if overlays:
#                 ndoverlay = hv.NdOverlay(overlays).apply.opts(
#                     legend_position='right',
#                     responsive=True,
#                     min_height=600,
#                     xlim=(None, None) if self.data_source_widget.value == 'HV_CPU_Usage' else (0, self.duration),
#                     framewise=True,
#                     title='',
#                 )
#                 return ndoverlay
#             else:
#                 return self.blank_stream_plot()

#         dmap = hv.DynamicMap(create_plot, streams=[self.buffer])
#         return dmap

#     def blank_bare_plot(self):
#         return hv.Curve([]).opts(yaxis='bare', xaxis='bare', responsive=True)

#     def blank_stream_plot(self):
#         # Create an empty NdOverlay with the expected keys and labels
#         empty_curves = {ch: hv.Curve([]).relabel(ch).opts(subcoordinate_y=True,) for ch in self.channel_names}
#         ndoverlay = hv.NdOverlay(empty_curves).opts(
#             legend_position='right',
#             responsive=True,
#             min_height=600,
#             title=''  # Set a static title
#         )
#         return ndoverlay

#     def stream_data(self):
#         if not self.streaming or self.paused:
#             return
#         with pn.io.unlocked():
#             if self.data_source_widget.value == 'HV_Sim_Live':
#                 if self.current_time > self.duration:
#                     self.pause_stream()
#                     return
#             # Use the data generator to get new data
#             new_data_df = self.data_generator.generate_data()
#             self.buffer.send(new_data_df)
#             if self.data_source_widget.value == 'HV_Sim_Live':
#                 self.current_time = self.data_generator.current_time

#     def create_servable_app(self):
#         if self.notebook:
#             return self.layout
#         else:
#             return self.template.servable()

# # Create and serve the streaming app
# app = StreamingApp(duration=100, sampling_interval=0.1, n_channels=5, notebook=False)
# app.create_servable_app()

# %% 2.3
import numpy as np
import pandas as pd
import holoviews as hv
import panel as pn
import param
import psutil
import abc
from holoviews.streams import Buffer

hv.extension('bokeh')
pn.extension()

# Base DataSource class
class DataSource(abc.ABC):
    @abc.abstractmethod
    def get_channel_names(self):
        pass

    @abc.abstractmethod
    def generate_data(self):
        pass

    @property
    @abc.abstractmethod
    def sampling_interval(self):
        pass

# HV_Sim_Live data source
class HV_Sin(DataSource):
    def __init__(self, duration=10, sampling_interval=0.1, n_channels=5):
        self.duration = duration
        self._sampling_interval = sampling_interval
        self.n_channels = n_channels
        self.channel_names = [f'Channel_{i+1}' for i in range(self.n_channels)]
        self.current_time = 0
        self.spike_added = {ch: False for ch in self.channel_names}

    def get_channel_names(self):
        return self.channel_names

    @property
    def sampling_interval(self):
        return self._sampling_interval

    def generate_data(self):
        if self.current_time > self.duration:
            return pd.DataFrame()  # Return empty DataFrame to indicate the end
        new_data = {'time': [self.current_time]}
        for ch in self.channel_names:
            amplitude = np.sin(12 * np.pi * self.current_time / self.duration) * \
                        (1 + np.random.normal(0, 0.1))
            if not self.spike_added[ch] and 0.48 * self.duration <= self.current_time <= 0.52 * self.duration:
                amplitude += np.random.uniform(1.8, 1.9)
                self.spike_added[ch] = True
            new_data[ch] = amplitude
        self.current_time += self.sampling_interval
        return pd.DataFrame(new_data)

# HV_CPU_Usage data source
class HV_CPU_Usage(DataSource):
    def __init__(self):
        self.num_cores = psutil.cpu_count(logical=True)
        self.channel_names = [f'CPU_{i}' for i in range(self.num_cores)]
        self._sampling_interval = 0.5  # Default sampling interval

    def get_channel_names(self):
        return self.channel_names

    @property
    def sampling_interval(self):
        return self._sampling_interval

    def generate_data(self):
        cpu_percent = psutil.cpu_percent(percpu=True)
        timestamp = pd.Timestamp.now()
        data = {'time': [timestamp]}
        for ch, usage in zip(self.channel_names, cpu_percent):
            data[ch] = usage
        return pd.DataFrame(data)

class StreamingApp(param.Parameterized):
    def __init__(self, data_sources, notebook=False):
        super().__init__()
        self.data_sources = data_sources
        self.notebook = notebook

        # Create mappings from data source names to instances
        self.data_source_names = [type(ds).__name__ for ds in data_sources]
        self.data_source_instances = {type(ds).__name__: ds for ds in data_sources}
        self.data_source = self.data_source_names[0]  # Default selection

        self.update_channel_names()
        self.buffer_length = 1000  # Adjust as needed
        self.streaming = False
        self.paused = False
        self.task = None

        # Initialize the buffer here after channel names are set
        self.buffer = Buffer(data=self.initial_data(), length=self.buffer_length)

        self.create_widgets()
        self.create_layout()

    def update_channel_names(self):
        data_source_instance = self.data_source_instances[self.data_source]
        self.channel_names = data_source_instance.get_channel_names()
        # Update buffer with new channel names if buffer is initialized
        if hasattr(self, 'buffer'):
            self.buffer.clear()
            self.buffer.data = self.initial_data()

    def initial_data(self):
        # No initial data
        return pd.DataFrame({'time': [], **{ch: [] for ch in self.channel_names}})

    def create_widgets(self):
        # Dropdown widget for selecting data source
        self.data_source_widget = pn.widgets.Select(
            name='Data Source',
            options=self.data_source_names,
            value=self.data_source
        )
        # Watch for changes in the data source selector
        self.data_source_widget.param.watch(self.on_data_source_change, 'value')

        self.radio_group = pn.widgets.RadioButtonGroup(
            name='Stream Control',
            options=['Start', 'Pause', 'Stop'],
            value='Stop',
            button_type='default',
            sizing_mode='stretch_width',
            # Style the active button color
            stylesheets=[ """
            :host(.solid) .bk-btn.bk-btn-default.bk-active {
                background-color: #b23c3c;
            }
            """]
        )
        self.radio_group.param.watch(self.handle_state_change, 'value')

    def on_data_source_change(self, event):
        self.stop_stream()
        self.data_source = event.new
        self.update_channel_names()
        # Update the plot
        self.plot_pane.object = self.blank_bare_plot()

    def handle_state_change(self, event):
        if event.new == 'Start':
            self.start_stream()
        elif event.new == 'Pause':
            self.pause_stream()
        elif event.new == 'Stop':
            self.stop_stream()

    def create_layout(self):
        # Start with a blank plot
        self.plot_pane = pn.pane.HoloViews(self.blank_bare_plot())
        if self.notebook:
            self.layout = pn.Column(
                self.data_source_widget,
                self.radio_group,
                self.plot_pane,
                align='center',
            )
        else:
            sidebar = pn.Column(
                pn.WidgetBox(
                    self.data_source_widget,
                    self.radio_group,
                ),
                align='center',
                sizing_mode='stretch_width',
            )
            self.template = pn.template.FastListTemplate(
                main=[self.plot_pane],
                sidebar=[sidebar],
                title="Multi-Channel Streaming App",
                theme="dark",
                accent="#2e008b",
            )

    def start_stream(self):
        if not self.streaming:
            self.streaming = True
            self.paused = False
            # Get the selected data source instance
            self.data_generator = self.data_source_instances[self.data_source_widget.value]
            self.buffer.clear()
            # Replace the plot with the live streaming plot
            self.plot_pane.object = self.create_streaming_plot()
            # Start the periodic callback
            sampling_interval_ms = int(self.data_generator.sampling_interval * 1000)
            self.task = pn.state.add_periodic_callback(
                self.stream_data, period=sampling_interval_ms, count=None
            )
        else:
            self.paused = False
            if self.task is None:
                # Restart the periodic callback if it was stopped
                sampling_interval_ms = int(self.data_generator.sampling_interval * 1000)
                self.task = pn.state.add_periodic_callback(
                    self.stream_data, period=sampling_interval_ms, count=None
                )

    def pause_stream(self):
        if self.task:
            self.task.stop()
            self.task = None
        self.paused = True

    def stop_stream(self):
        self.streaming = False
        self.paused = False
        if self.task:
            self.task.stop()
            self.task = None
        self.radio_group.value = 'Stop'
        self.plot_pane.object = self.blank_bare_plot()

    def create_streaming_plot(self):
        # Create the streaming plot using DynamicMap
        def create_plot(data):
            overlays = {}
            for ch in self.channel_names:
                if ch in data.columns and not data[ch].dropna().empty:
                    # Set the label to match the key
                    curve = hv.Curve((data['time'], data[ch]), label=ch).opts(
                        line_width=2,
                        subcoordinate_y=True,
                    )
                    overlays[ch] = curve
            if overlays:
                ndoverlay = hv.NdOverlay(overlays).apply.opts(
                    legend_position='right',
                    responsive=True,
                    min_height=600,
                    # xlim=(None, None),
                    framewise=True,
                    title='',
                )
                return ndoverlay
            else:
                return self.blank_stream_plot()

        dmap = hv.DynamicMap(create_plot, streams=[self.buffer])
        return dmap

    def blank_bare_plot(self):
        return hv.Curve([]).opts(yaxis='bare', xaxis='bare', responsive=True)

    def blank_stream_plot(self):
        # Create an empty NdOverlay with the expected keys and labels
        empty_curves = {ch: hv.Curve([]).relabel(ch).opts(subcoordinate_y=True,) for ch in self.channel_names}
        ndoverlay = hv.NdOverlay(empty_curves).opts(
            legend_position='right',
            responsive=True,
            min_height=600,
            title=''
        )
        return ndoverlay

    def stream_data(self):
        if not self.streaming or self.paused:
            return
        with pn.io.unlocked():
            # Use the data generator to get new data
            new_data_df = self.data_generator.generate_data()
            self.buffer.send(new_data_df)

    def create_servable_app(self):
        if self.notebook:
            return self.layout
        else:
            return self.template.servable()


# Create data source instances
data_source_sin = HV_Sin(duration=60, sampling_interval=0.1, n_channels=5)
data_source_cpu_usage = HV_CPU_Usage()

# Create and serve the streaming app
app = StreamingApp(data_sources=[data_source_sin, data_source_cpu_usage], notebook=False)
app.create_servable_app()
