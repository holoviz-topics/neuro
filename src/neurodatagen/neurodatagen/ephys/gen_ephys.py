from __future__ import annotations 

from typing import Tuple
import numpy as np


def generate_action_potential(
    t: np.ndarray, gaussian_std_dev: float = 0.1, decay_rate: float = 5.0
) -> np.ndarray:
    """
    Generates an action potential signal given a time array, Gaussian standard deviation, and decay rate.

    Parameters
    ----------
    t : np.ndarray
        Time array.
    gaussian_std_dev : float, optional
        Standard deviation for the Gaussian upstroke. Default is 0.1.
    decay_rate : float, optional
        Decay rate for the exponential downstroke. Default is 5.0.

    Returns
    -------
    np.ndarray
        Action potential signal array.
    """

    # Create Gaussian for the upstroke
    upstroke = np.exp(-(t**2) / (2 * gaussian_std_dev**2))
    upstroke /= np.max(upstroke)  # Normalize

    # Create decaying exponential for the downstroke
    downstroke_start = np.argmax(upstroke)
    downstroke = np.exp(-np.linspace(0, decay_rate, len(t) - downstroke_start))
    downstroke /= downstroke[0]  # Normalize

    # Combine the upstroke and downstroke
    action_potential = np.concatenate((upstroke[:downstroke_start], downstroke))

    return action_potential


def generate_spike_timeseries(
    duration: float,
    sampling_rate: float = 30000,
    spike_rate_range: Tuple[float, float] = (0.1, 20),
    gaussian_std_dev: float = 0.1,
    decay_rate: float = 5.0,
    spike_dur: float = 0.001,
    amplitude: float = 100.0,
) -> np.ndarray:
    """
    Generates a spike time series with a random spike rate within a given range.

    Parameters
    ----------
    duration : float
        The total time duration of the time series.
    sampling_rate : float
        The sampling rate used for the time series. Default is 30000 Hz.
    spike_rate_range : Tuple[float, float]
        The range of possible spike rates. A random spike rate will be selected from this range.
        Default is (0.1, 20) Hz.
    gaussian_std_dev : float, optional
        Standard deviation for the Gaussian upstroke. Default is 0.1.
    decay_rate : float, optional
        Decay rate for the exponential downstroke. Default is 5.0.
    spike_dur : float, optional
        The duration of a single spike. Default is 0.001.
    amplitude : float, optional
        Amplitude scaling factor for the generated spike data. Default is 100.0 microvolts.

    Returns
    -------
    np.ndarray
        Spike time series.
    """
    time = np.arange(0, duration, 1 / sampling_rate)  # Time vector

    # Generate spike train using Poisson process
    spike_rate = np.random.uniform(
        *spike_rate_range
    )  # Average spike rate (spikes per second)
    spike_train = np.random.poisson(spike_rate / sampling_rate, len(time))

    # If there are no spikes (e.g. from very short duration and low spike rate), randomly pick a time for a spike
    if np.sum(spike_train) == 0:
        spike_train[np.random.randint(0, len(time))] = 1

    # Generate spike waveform
    spike_waveform = generate_action_potential(
        np.linspace(-1, 2, int(sampling_rate * spike_dur)), gaussian_std_dev, decay_rate
    )

    # Add action potential waveform at spike times
    spike_times = np.where(spike_train)[0]
    interspike_interval = np.diff(spike_times)  # calculate interspike intervals

    # Check if there's enough space between spikes for the action potential waveform; if so, keep the earlier spike
    valid_spike_times = [
        spike_times[i]
        for i in range(len(interspike_interval))
        if interspike_interval[i] >= len(spike_waveform)
    ]
    valid_spike_times.append(spike_times[-1])  # include the last spike

    spikes = np.zeros(len(time))
    for spike_time in valid_spike_times:
        if spike_time + len(spike_waveform) < len(
            spikes
        ):  # make sure not to go past the end of the array
            spikes[spike_time : spike_time + len(spike_waveform)] += (
                spike_waveform * amplitude
            )  # Adjust the amplitude to a reasonable range (in microvolts)

    return spikes


def generate_ephys_powerlaw(
    n_channels: int,
    n_seconds: float,
    fs: int = 30000,
    highpass: float = 2.0,
    exponent: float = -1,
    amplitude: float = 20.0,
) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Generate synthetic ephys data as power law time series at a specified exponent and poisson spikes.

    Parameters
    ----------
    n_channels : int
        Number of ephys channels.
    n_seconds : float
        Duration of the ephys data in seconds.
    fs : int, optional
        Sampling rate of the ephys data in Hz. Default is 30000.
    highpass : float, optional
        High-pass filter factor in Hz. Frequencies lower than this value will be attenuated.
        Should be greater than 0. Default is 2.0.
    exponent : float, optional
        Power law exponent. Default is -1, producing pink noise; a reasonable alternative is -2,
        producing brown noise.
    amplitude : float, optional
        Amplitude scaling factor for the generated ephys data. Default is 20.0 microvolts.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, list]
        Data: Synthetic ephys data as a NumPy array of shape (n_channels, total_samples).
        Time: Time array as a NumPy array of shape (total_samples,).
        Channel names: List of strings of channel names like ['1', '2', ].
    """

    from neurodsp.sim import (
        sim_powerlaw,
    )  # import here to avoid dependency for all ephys workflows

    total_samples = int(n_seconds * fs)

    # Generate high-passed power law noise for each channel
    ephys = np.empty((n_channels, total_samples))
    for ch in range(n_channels):
        pl_noise = (
            sim_powerlaw(n_seconds, fs, exponent=exponent, f_range=(highpass, None))
            * amplitude
        )
        spikes = generate_spike_timeseries(n_seconds, fs)

        # Combine LFP and spike waveform into a single trace
        ephys[ch] = pl_noise + spikes

    time = np.arange(total_samples) / fs

    # Check dimensions of the generated data
    assert ephys.shape == (
        n_channels,
        total_samples,
    ), f"Incorrect dimensions {ephys.shape} for data array {(n_channels, total_samples)}"

    # Create channel names
    ch_names = create_ephys_channel_names(n_channels)

    return ephys, time, ch_names


def create_ephys_channel_names(n_channels: int = None) -> list[str]:
    """
    Given the number of channels, return a list of channel names like ['1', '2', ...].

    Parameters
    ----------
    n_channels : int, optional
        Number of channels. Default is None.

    Returns
    -------
    list[str]
        List of channel names.
    """
    return [f"{i+1}" for i in range(n_channels)]
