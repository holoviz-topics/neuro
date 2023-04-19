import numpy as np
import pandas as pd


def sim_spikes(num_neurons, firing_rate, duration):
    """
    Simulates spike times for a given number of neurons, firing rate, and duration.

    Args:
    - num_neurons (int): Number of neurons to simulate
    - firing_rate (float): Firing rate of each neuron in Hz
    - duration (float): Duration of the spike trains in seconds

    Returns:
    - spikes_df (pandas DataFrame): Spiking data
    """

    # Calculate the expected number of spikes for each neuron
    expected_num_spikes = np.random.poisson(firing_rate * duration, size=num_neurons)

    # Generate spike times for all neurons at once using a uniform distribution
    spike_times = np.random.uniform(0, duration, size=sum(expected_num_spikes))

    # Assign spike times to each neuron based on their expected number of spikes
    neuron_ids = np.repeat(np.arange(1, num_neurons+1), expected_num_spikes)

    # Create a DataFrame of time and neuron cols, sorted by spike times
    spikes_df = pd.DataFrame({"time": spike_times, "neuron": neuron_ids})
    spikes_df.sort_values("time", inplace=True, ignore_index=True)

    return spikes_df
