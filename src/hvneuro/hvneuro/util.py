from pathlib import Path
from urllib.parse import urlparse
import requests
from tqdm import tqdm
from typing import Union, List, Optional
import os

def download_file(url: str, data_dir: str, file_name: Optional[str] = None) -> Path:
    """
    Download a file if it doesn't already exist.

    Parameters
    ----------
    url : str
        The URL where the file can be downloaded from.
    data_dir : str
        The local directory where the file will be saved.
    file_name : Optional[str]
        The specific file name to save as (overrides the name from the URL).

    Returns
    -------
    data_dir : pathlib.Path
        The path where the file has been saved.
    """
    data_dir = os.path.expanduser(data_dir)
    data_dir = Path(data_dir)
    # Create the local directory if it does not exist
    data_dir.mkdir(parents=True, exist_ok=True)

    # If file_name is not provided, extract it from the URL
    if file_name is None:
        url_path = urlparse(url).path
        file_name = Path(url_path).name

    # Construct the full file path
    file_path = data_dir / file_name

    # Check if the file already exists
    if not file_path.exists():
        print(f"Downloading {url} to {file_path}...")

        # Send a HTTP request to the URL of the file
        response = requests.get(url, stream=True)

        # Get the total size of the file
        total_size = int(response.headers.get('content-length', 0))

        # Use tqdm to show the download progress
        with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    # Write the chunks of the file
                    if chunk:
                        f.write(chunk)
                        # Update the progress bar
                        pbar.update(len(chunk))
    else:
        print(f"{file_path} already exists. Skipping download.")
    return file_path

def download_files(input_data: Union[str, dict, List[str]], data_dir: str):
    """
    Download one or multiple files to a specified local directory.

    Parameters
    ----------
    input_data : Union[str, dict, List[str]]
        If a string is provided, it is treated as the URL of a single file to download.
        If a dictionary is provided, it maps URLs to corresponding filenames, and
        each file will be downloaded and saved with the specified name.
        If a list is provided, it should contain URLs of files to download, and
        each file will be saved with a name extracted from the URL.
    data_dir : str
        The local directory where the file(s) will be saved. If the directory does not
        exist, it will be created.

    """
    if isinstance(input_data, str):
        download_file(input_data, data_dir)
    elif isinstance(input_data, dict):
        for url, file_name in input_data.items():
            download_file(url, data_dir, file_name)
    elif isinstance(input_data, list):
        for url in input_data:
            download_file(url, data_dir)
    else:
        raise TypeError("input_data must be either a string, a dictionary, or a list.")


