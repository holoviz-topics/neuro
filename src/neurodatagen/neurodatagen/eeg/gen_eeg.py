from __future__ import annotations

import numpy as np
from neurodsp.sim import sim_powerlaw


def generate_eeg_powerlaw(
    n_channels: int,
    n_seconds: float,
    fs: int,
    highpass: float = 2.0,
    exponent: float = -1,
    amplitude: float = 50.0,
    channel_prefix: str = "EEG",
    add_blink_artifacts: bool = True,
    correlated_noise_scale: float = 0.1,
    blink_scale: float = 0.05,
) -> tuple[np.ndarray, np.ndarray, list]:
    """
    Generate synthetic EEG data as a power-law time series, with a specified exponent.

    Parameters
    ----------
    n_channels (int): Number of EEG channels.
    n_seconds (float): Duration of the EEG data in seconds.
    fs (int): Sampling rate of the EEG data in Hz.
    highpass (float, optional):
        High-pass filter factor in Hz. Frequencies lower than this value
        will be attenuated. Should be greater than 0. Defaults to 2.0.
    exponent (float):
        Power law exponent. Defaults to `-1`, producing pink noise; a
        reasonable alternative is `-2`, producing brown noise.
    amplitude (float, optional):
        Amplitude scaling factor for the generated EEG data. Defaults to
        50.0 microvolts.
    channel_prefix (str, optional):
        Prefix for the channel names. Defaults to 'EEG'.
    add_blink_artifacts (bool, optional):
        Whether to add blink artifacts to the generated data. Defaults to True.
    correlated_noise_scale (float, optional):
        Scale factor for the correlated noise. Defaults to 0.2.
    blink_scale (float, optional):
        Scale factor for the blink artifacts. Defaults to 0.05.

    Returns
    -------
    data (np.ndarray):
        Synthetic EEG data as a NumPy array of shape 
        (n_channels, total_samples).
    time (np.ndarray):
        Time array as a NumPy array of shape (total_samples,).
    ch_names (list):
        List of strings of channel names like: '<channel_prefix> <Channel num>'

    """

    total_samples = int(n_seconds * fs)

    # Generate high-passed power law noise for each channel
    scaled_noise = np.empty((n_channels, total_samples))
    for ch in range(n_channels):
        pl_noise = sim_powerlaw(
            n_seconds, fs, exponent=exponent, f_range=(highpass, None)
        )
        scaled_noise[ch] = pl_noise * amplitude

    # Add channel correlations
    cov_matrix = np.eye(n_channels) + 0.5  # Identity matrix with some weighted correlation
    correlated_noise = np.random.multivariate_normal(np.zeros(n_channels), cov_matrix, size=total_samples).T
    correlated_noise *= amplitude / correlated_noise_scale  # Scale the correlated noise
    scaled_noise += correlated_noise

    # Add blink artifacts
    if add_blink_artifacts:
        blink_rate = 1 / 2  # Average rate of 1 blink every 2 seconds
        n_blinks = np.random.poisson(n_seconds * blink_rate)  # Number of blinks
        blink_times = np.random.choice(total_samples, n_blinks, replace=False)  # Random times
        for i in blink_times:
            blink_samples = np.random.normal(size=fs//10)  # Blink lasts 100 ms
            blink_samples *= np.hanning(len(blink_samples))  # Taper blink onset/offset
            blink_samples *= amplitude / blink_scale  # scaled by amplitude
            # pick a random half of the channels
            n_channels_to_blink = np.random.choice(n_channels, int(n_channels/2), replace=False)
            
            scaled_noise[n_channels_to_blink, i:i + len(blink_samples)] += blink_samples # apply to a quarter of the channels

    time = np.arange(total_samples) / fs
    # Check dimensions of the generated data
    # assert scaled_noise.shape == (n_channels, total_samples), "Incorrect dimensions for data"

    # Create channel names
    ch_names = create_channel_names(n_channels, channel_prefix)
    return scaled_noise, time, ch_names


def create_channel_names(n_channels: int, prefix: str = "EEG") -> list[str]:
    """Given the number of channels, return a list of strings like '<prefix> 1'"""
    return [f"{prefix} {i+1}" for i in range(n_channels)]
