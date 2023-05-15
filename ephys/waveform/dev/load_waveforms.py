import pandas as pd

def load_waveform_templates(wfpath = './waveforms.csv'):
    waveforms = pd.read_csv(wfpath, index_col = 'uid')
    wf = waveforms.drop(['organoid'], axis = 1, inplace=False)
    wf.columns = wf.columns.astype('int')
    return wf