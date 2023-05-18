import numpy as np

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