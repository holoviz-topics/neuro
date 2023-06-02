import mne

mne.set_config('MNE_BROWSER_BACKEND', 'qt') # qt or matplotlib

sample_data_folder = mne.datasets.sample.data_path() # will save data to ~/mne-data unless `path` arg is specified
sample_data_folder

# unfiltered/full-resolution version is (sample_audvis_raw.fif) ~ 128 MB
sample_data_raw_file = (sample_data_folder / 'MEG' / 'sample' /
                        'sample_audvis_raw.fif')

raw = mne.io.read_raw_fif(sample_data_raw_file)

raw.plot(duration=10, n_channels=80, block=True) # launches GUI