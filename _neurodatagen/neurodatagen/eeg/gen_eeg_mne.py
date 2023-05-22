
import numpy
import mne


def generate_eeg_sine_mne(duration: float = 10, n_channels: int = 100, fs: float = 1000) -> mne.io.RawArray:
    """
    Simulate EEG data using noisy sine waves and output to MNE RawArray
    For now, hard-coding the noise amplitude scaling and eeg data scaling.

    Parameters:
        duration (float): Duration of the simulated data in seconds.
        n_channels (int): Number of EEG channels.
        fs (float): Sampling frequency in Hz.

    Returns:
        mne.io.RawArray: Simulated EEG data as a `mne.io.RawArray` object.

    """

    # Calculate the number of samples based on duration and sampling frequency
    n_samples = int(duration * fs)

    # Create a time vector for the EEG data
    times = np.arange(n_samples) / fs

    # Generate synthetic EEG data using sine waves
    data = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        # Generate a random frequency for each channel
        freq = np.random.uniform(4, 30)
        # Generate a sine wave for the channel
        sine_wave = np.sin(2 * np.pi * freq * times)
        # Add the sine wave to the channel's data
        data[ch] = sine_wave

    # Add noise to the data to make it slightly more realistic
    noise_amplitude = 0.2  # Adjust this parameter to control the noise level
    noise = np.random.normal(scale=noise_amplitude, size=(n_channels, n_samples))
    data += noise
    
    # There is some correction in mne happening for 'eeg' 'ch_type' data that scales it up..
    # I think the data is going from Volts to microvolts when returned with raw.get_data()...
    # so scale the data down to Volts first:
    data = data * 1e-5

    # Create a channel names list
    ch_names = [f'EEG {i+1}' for i in range(n_channels)]

    # Create an info object
    info = mne.create_info(ch_names=ch_names, sfreq=fs, ch_types='eeg')

    # Create a `mne.io.RawArray` object
    raw = mne.io.RawArray(data, info)

    return raw