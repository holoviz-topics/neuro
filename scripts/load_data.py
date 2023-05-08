import pandas as pd


def load_waveform_templates():
    mypath = '../../data/waveforms.csv'
    waveforms = pd.read_csv(mypath, index_col = 'uid')
    wf = waveforms.drop(['organoid'], axis = 1, inplace=False)
    wf.columns = wf.columns.astype('int')
    return wf