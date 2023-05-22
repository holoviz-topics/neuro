import numpy as np

def generate_eeg_brown(n_channels: int, n_seconds: float, fs: int,
                            highpass: float = 2.0, amplitude: float = 50.0) -> tuple[np.ndarray, np.ndarray, list]:
    """
    Generate synthetic EEG data with brown noise characteristics.

    Args:
        n_channels (int): Number of EEG channels.
        n_seconds (float): Duration of the EEG data in seconds.
        fs (int): Sampling rate of the EEG data in Hz.
        highpass (float, optional): High-pass filter factor in Hz. Frequencies lower than
            this value will be attenuated. Should be greater than 0. Defaults to 2.0.
        amplitude (float, optional): Amplitude scaling factor for the generated EEG data.
            Defaults to 50.0 microvolts.

    Returns:
        data (np.ndarray): Synthetic EEG data as a NumPy array of shape (n_channels, total_samples).
        time (np.ndarray): Time array as a NumPy array of shape (total_samples,).
        ch_names (list): List of strings of channel names like: EEG <Channel num>

    """
    from neurodsp.sim import sim_powerlaw

    total_samples = int(n_seconds * fs)

    # Generate high-passed brown noise for each channel
    scaled_noise = np.empty((n_channels, total_samples))
    for ch in range(n_channels):
        brown_noise = sim_powerlaw(n_seconds, fs, f_range=(highpass, None))
        scaled_noise[ch] = brown_noise * amplitude

    time = np.arange(total_samples) / fs

    # Check dimensions of the generated data
    assert scaled_noise.shape == (n_channels, total_samples), "Incorrect dimensions for scaled_noise array"

    # Create channel names
    ch_names = [f'EEG {i+1}' for i in range(n_channels)]

    return scaled_noise, time, ch_names