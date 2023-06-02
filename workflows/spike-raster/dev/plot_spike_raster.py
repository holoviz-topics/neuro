import holoviews as hv

def plot_spike_raster(df, spiketime_col, neuron_col, spike_train_opts=None, overlay_opts=None):

    """
    Plot a spike raster

    Args:
    - data (pandas.DataFrame): DataFrame with columns for spike times and neuron IDs
    - spiketime_col (int): Column name into `data` for spike times
    - neuron_col (int): Column name into `data` for neuron ID
    - spike_train_opts (dict): plotting opts that applies to all hv.Spikes spiketrain elements
    - overlay_opts (dict): plotting opts that applies to the hv.NdOverlay element
    
    Returns:
    - hv.NdOverlay of hv.Spikes elements
    """


    default_spike_train_opts = {'color':'black',  'cmap':'glasbey_cool', 
                        'spike_length':.95, 'tools':['hover']}
    default_overlay_opts = {'ylabel':'Neuron', 'xlabel':'Time', 'show_grid':True, 
                         'padding':0.01, 'width':1000, 'height':500, 'show_legend':False}

    # If plot opts are not None, update the defaults
    if spike_train_opts is not None:
        default_spike_train_opts.update(spike_train_opts)
    if overlay_opts is not None:
        default_overlay_opts.update(overlay_opts)
        
    # group the DataFrame by the neuron ID col and sort the resulting groups by key
    spike_groups = sorted(df.groupby(neuron_col), key=lambda x: x[0])
    
    spikes_dict = {}
    for ineuron, ispikes in spike_groups:
        spikes_dict[ineuron] = hv.Spikes(ispikes).opts(position=ineuron-.5, **default_spike_train_opts)

    overlay = hv.NdOverlay(spikes_dict, kdims=default_overlay_opts['ylabel']).opts(yticks=spikes_dict.keys, **default_overlay_opts)
    
    return overlay