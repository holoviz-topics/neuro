from __future__ import annotations

import numpy as np


def create_noisy_waveforms(
    spike_waveform: np.ndarray,
    noise_std_percent: float = 50,
    num_spikes: int = 100
) -> list[np.ndarray]:
    """
    Generate a list of noisy spike waveforms based on a given input waveform.

    Parameters
    ----------
    spike_waveform : np.ndarray
        A 1D array-like object representing the spike waveform to be used as a template.
    noise_std_percent : float, optional
        The percentage of the standard deviation of the input waveform to use as the standard deviation
        of the normal distribution from which to generate noise for each noisy waveform.
        Default is 50.
    num_spikes : int, optional
        The number of noisy waveforms to generate.
        Default is 100.

    Returns
    -------
    list[np.ndarray]
        A list of length `num_spikes`, where each element is a 1D numpy array representing a noisy
        version of the input spike waveform.
    """

    real_data_std = np.std(spike_waveform)

    # Compute the noise standard deviation as a percentage of the real data standard deviation
    noise_std = (noise_std_percent / 100) * real_data_std

    # Generate random noise with the same shape as the spike waveform and num_spikes
    noise = np.random.normal(
        scale=noise_std, size=(num_spikes, spike_waveform.shape[0])
    )

    # Add the noise to the spike waveform
    noisy_spike_waveform = spike_waveform + noise

    return noisy_spike_waveform
