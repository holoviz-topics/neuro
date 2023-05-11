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
    spikes_df = pd.DataFrame({"time": spike_times, "neuron": pd.Categorical(neuron_ids)})
    spikes_df.sort_values("time", inplace=True, ignore_index=True)

    return spikes_df


def assign_groups(times, num_groups, sigma=1):
    """
    Bin an array of times into a number of groups controlled by num_groups parameter.
    
    Parameters:
    times (numpy.ndarray): An array of times to be binned into groups.
    num_groups (int): The number of groups to bin the times into.
    sigma (float): The standard deviation of the normal distribution used to assign
                   times to groups probabilistically. Default is 1.

    Returns:
    numpy.ndarray: An equally sized array of groups labeled with integers.
    """
    # Sort the array of times
    sorted_times = np.sort(times)

    # Calculate the bin width based on the number of groups
    bin_width = (sorted_times[-1] - sorted_times[0]) / num_groups

    # Calculate the center of each bin
    bin_centers = np.linspace(sorted_times[0] + bin_width/2, sorted_times[-1] - bin_width/2, num_groups)

    # Assign each time to a group probabilistically
    groups = np.zeros_like(sorted_times)
    for i, time in enumerate(sorted_times):
        # Calculate the distance to each bin center
        distances = np.abs(time - bin_centers)

        # Calculate the probability of assigning the time to each group
        probabilities = np.exp(-distances**2 / (2*sigma**2))

        # Normalize the probabilities so they sum to 1
        probabilities /= np.sum(probabilities)

        # Assign the time to a group based on the probabilities
        groups[i] = np.random.choice(range(num_groups), p=probabilities)

    # Sort the groups based on the original order of the times
    return groups[np.argsort(times)]


def create_noisy_waveforms(spike_waveform, noise_std_percent = 50, num_spikes = 100):
    """
    Generate a list of noisy spike waveforms based on a given input waveform.

    Parameters
    ----------
    spike_waveform : array-like
        A 1D array-like object representing the spike waveform to be used as a template.
    noise_std_percent : float
        The percentage of the standard deviation of the input waveform to use as the standard deviation
        of the normal distribution from which to generate noise for each noisy waveform. 
    num_spikes : int
        The number of noisy waveforms to generate.

    Returns
    -------
    list
        A list of length `num_spikes`, where each element is a 1D numpy array representing a noisy
        version of the input spike waveform.
    """

    real_data_std = np.std(spike_waveform)

    # compute the noise standard deviation as a percentage of the real data standard deviation
    noise_std = (noise_std_percent / 100) * real_data_std

    # generate random noise with the same shape as the spike waveform and num_spikes
    noise = np.random.normal(scale=noise_std, size=(num_spikes, spike_waveform.shape[0]))

    # add the noise to the spike waveform
    noisy_spike_waveform = spike_waveform + noise
    
    return noisy_spike_waveform

def simulate_eeg(duration=10, n_channels=100, sfreq=1000):
    """
    Simulate EEG data using the MNE toolbox as noisy sine waves.
    For now, hard-coding the noise amplitude scaling and eeg data scaling.

    Parameters:
        duration (float): Duration of the simulated data in seconds.
        n_channels (int): Number of EEG channels.
        sfreq (float): Sampling frequency in Hz.

    Returns:
        mne.io.RawArray: Simulated EEG data as a `mne.io.RawArray` object.

    """
    import mne

    # Calculate the number of samples based on duration and sampling frequency
    n_samples = int(duration * sfreq)

    # Create a time vector for the EEG data
    times = np.arange(n_samples) / sfreq

    # Generate synthetic EEG data using sine waves
    data = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        # Generate a random frequency for each channel
        freq = np.random.uniform(4, 30)
        # Generate a sine wave for the channel
        sine_wave = np.sin(2 * np.pi * freq * times)
        # Add the sine wave to the channel's data
        data[ch] = sine_wave

    # Add noise to the data to make it more realistic
    noise_amplitude = 0.2  # Adjust this parameter to control the noise level
    noise = np.random.normal(scale=noise_amplitude, size=(n_channels, n_samples))
    data += noise
    
    # There is some correction happening for 'eeg' 'ch_type' data that scales it up..
    # so scale the data down first:
    data = data * 1e-5

    # Create a channel names list
    ch_names = [f'EEG {i+1}' for i in range(n_channels)]

    # Create an info object
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')

    # Create a `mne.io.RawArray` object
    raw = mne.io.RawArray(data, info)

    return raw
