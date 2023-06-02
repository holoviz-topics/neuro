import numpy as np
import holoviews as hv

def plot_eeg(raw):
    """
    Plot stacked EEG traced

    Parameters:
        raw (mne.io.RawArray): The EEG data as a `mne.io.RawArray` object.

    Returns:
        holoviews.core.overlay.NdOverlay: The EEG plot.

    """
    data = raw.get_data()
    ch_names = raw.ch_names

    # Calculate the offset between channels to avoid visual overlap
    offset = np.max(np.abs(data)) * 2

    # Iterate over each channel and create Curve elements
    channel_curves = {}
    for i, channel_data in enumerate(data):
        channel_curves[ch_names[i]] = hv.Curve((raw.times, channel_data + (i * offset)), 'Time').opts(color='black', tools=['hover'])

    # Create mapping from yaxis location to ytick for each channel
    yticks = [(i * offset, channel_name) for i, channel_name in enumerate(ch_names)]

    # Create overlay of curves and apply opts
    eeg_viewer = hv.NdOverlay(channel_curves, kdims='Channel').opts(
        width=600, height=600, padding=.01, xlabel='Time', ylabel='Channel', yticks=yticks, show_legend=False)

    return eeg_viewer