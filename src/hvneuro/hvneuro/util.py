import requests
from tqdm import tqdm
from pathlib import Path
from urllib.parse import urlparse

def download_file(url: str, local_data_path: str) -> Path:
    """
    Download a file if it doesn't already exist.

    Parameters
    ----------
    url : str
        The URL where the file can be downloaded from.
    local_data_path : str
        The local directory where the file will be saved.

    Returns
    -------
    local_file_path : pathlib.Path
        The path where the file has been saved.
    """
    # Parse the URL to get the file name
    url_path = urlparse(url).path
    file_name = Path(url_path).name
    local_data_path = Path(local_data_path)
    # Create the local directory if it does not exist
    local_data_path.mkdir(parents=True, exist_ok=True)

    # Construct the full file path
    local_file_path = local_data_path / file_name

    # Check if the file already exists
    if not local_file_path.exists():
        print(f"Downloading {url} to {local_file_path}...")

        # Send a HTTP request to the URL of the file
        response = requests.get(url, stream=True)

        # Get the total size of the file
        total_size = int(response.headers.get('content-length', 0))

        # Use tqdm to show the download progress
        with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
            with open(local_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    # Write the chunks of the file
                    if chunk:
                        f.write(chunk)
                        # Update the progress bar
                        pbar.update(len(chunk))

    return local_file_path
