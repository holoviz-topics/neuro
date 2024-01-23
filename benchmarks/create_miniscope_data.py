# Create and save datasets for benchmarking

# Use env: create_miniscope_data_env.yml

# %%
from neurodatagen.ca_imaging import simulate_miniscope_data

MINISCOPE_DATA_PATH = "~/data/image-stacks/miniscope/"
# %% image stack datasets - simulation of miniscope data

# Generate the data
param_dict = {
    "10frames": {
        "NCELL": 50,
        "HEIGHT": 512,
        "WIDTH": 512,
        "FRAME": 10,
        "CHK_SIZE": 200,
    },
    "100frames": {
        "NCELL": 50,
        "HEIGHT": 512,
        "WIDTH": 512,
        "FRAME": 100,
        "CHK_SIZE": 200,
    },
    "1000frames": {
        "NCELL": 50,
        "HEIGHT": 512,
        "WIDTH": 512,
        "FRAME": 1_000,
        "CHK_SIZE": 200,
    },
    "10000frames": {
        "NCELL": 50,
        "HEIGHT": 512,
        "WIDTH": 512,
        "FRAME": 10_0000,
        "CHK_SIZE": 200,
    },
}

for k, v in param_dict.items():
    simulate_miniscope_data(
        ncell=v["NCELL"],
        dims={"height": v["HEIGHT"], "width": v["WIDTH"], "frame": v["FRAME"]},
        arr_name=k,
        chk_size=v["CHK_SIZE"],
    ).to_zarr(
        f"{MINISCOPE_DATA_PATH}/miniscope_sim_{k}.zarr",
        mode="w",
        consolidated=True,
    )

# %%
