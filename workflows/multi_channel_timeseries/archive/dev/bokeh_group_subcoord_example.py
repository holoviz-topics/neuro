from bokeh.io import show, output_notebook
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
import numpy as np

# output_notebook()

# Define the data
x = np.linspace(0, 10*np.pi, 200)
groups = ['A', 'B', 'C']
data = {}
j = 0.5

# Prepare data for plotting
for group in groups:
    for i in range(2):
        yvals = j * np.sin(x + i*np.pi/2)
        data[f'{group}{i}_x'] = x
        data[f'{group}{i}_y'] = yvals
        j += 1

source = ColumnDataSource(data=data)

# Create the main figure
p = figure(width=800, height=600, title="Grouped Curves with Subplots")

# Subplot creation using subplot functionality
for i, group in enumerate(groups):
    for j in range(2):
        key = f'{group}{j}'
        # Each group will have its own y_range within the subplot
        y_range = Range1d(start=-10, end=10)  # Customize this range as needed

        # Create subplots within the main figure
        subplot = p.subplot(
            x_source=Range1d(start=0, end=10*np.pi),
            y_source=y_range,
            x_target=p.x_range,
            y_target=Range1d(start=i*20 + j*10, end=i*20 + (j+1)*10 - 1),  # This spaces out each group's plots
        )

        subplot.line(x=f'{key}_x', y=f'{key}_y', source=source, color="navy", alpha=0.5)

# Customize the main figure as needed
p.yaxis.visible = False  # Hide the main y-axis as we're using subplots for y-values

# show(p)
