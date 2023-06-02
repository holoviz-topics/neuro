from __future__ import annotations 

import pandas as pd
import os


def load_waveform_templates() -> pd.DataFrame:
    """
    Load waveform templates from a CSV file.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the waveform templates.
    """
    waveform_filename = "waveforms.csv"
    current_dir = os.path.dirname(__file__)  # Get the directory of the current module
    file_path = os.path.join(
        current_dir, waveform_filename
    )  # Create the absolute path to the file

    waveforms = pd.read_csv(file_path, index_col="uid")
    wf = waveforms.drop(["organoid"], axis=1, inplace=False)
    wf.columns = wf.columns.astype("int")
    return wf
