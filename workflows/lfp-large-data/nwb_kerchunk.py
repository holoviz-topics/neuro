# Process an NWB file using kerchunk.hdf.SingleHdf5ToZarr and then do some bespoke manipulation.

import fsspec
import h5py
import kerchunk.hdf
import kerchunk.utils
import numcodecs
import numpy as np
import re
import ujson
import warnings
import zarr


def _create_zarr_file(ntime, nchannel, lfp_dtype, lfp_compression_type, lfp_compression_level,
                      time_dtype, time_compression_type, time_compression_level, chunk_size):
    shape = (ntime, nchannel)
    refs = {}
    root = zarr.open_group(refs, mode="w")

    # LFP data
    lfp_data = root.create_dataset(
        name="lfp",
        shape=shape,
        chunks=(chunk_size["time"], chunk_size["channel"]),
        dtype=lfp_dtype,
        compressor=_get_compressor(lfp_compression_type, lfp_compression_level),
        #fill_value=-9999.0,
    )
    lfp_data.attrs["_ARRAY_DIMENSIONS"] = ["time", "channel"]

    # Time coordinates, filled in later.
    time_data = root.create_dataset(
        name="time",
        chunks=chunk_size["time"],
        shape=ntime,
        dtype=time_dtype,
        compressor=_get_compressor(time_compression_type, time_compression_level),
    )
    time_data.attrs["_ARRAY_DIMENSIONS"] = ["time"]

    # Channel coordinates are integers starting at zero.
    channel = np.arange(nchannel, dtype=np.uint32)
    coord = root.create_dataset(
        name="channel",
        shape=nchannel,
        dtype=channel.dtype,
    )
    coord[:] = channel
    coord.attrs["_ARRAY_DIMENSIONS"] = ["channel"]

    return time_data, refs


def _get_compressor(compression_type, compression_level):
    if compression_type == "gzip":
        return numcodecs.Zlib(compression_level)
    else:
        return None


def _get_kerchunk_refs(probe_id, probe_nwb_filename, refs):
    so = dict(anon=True, default_fill_cache=False, default_cache_type='first')

    # Getting all the chunk references from the NWB file here, then filtering them.
    # Can I just read the ones I am interested in?
    with fsspec.open(probe_nwb_filename, **so) as f:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            h5chunks = kerchunk.hdf.SingleHdf5ToZarr(f, probe_nwb_filename)
            probe_refs = h5chunks.translate()

    probe_refs = probe_refs["refs"]

    # Extract refs of interest which are lfp data and optionally time.
    # Do not want .zarray and .zattrs as they are created by zarr.create_dataset above.
    prefix = f"acquisition/probe_{probe_id}_lfp/probe_{probe_id}_lfp_data"
    match = re.compile(f"{prefix}/data/([^\.].*)")
    for k, v in probe_refs.items():
        if m := match.match(k):
            chunk_indices = m.group(1)
            refs[f"lfp/{chunk_indices}"] = v


def _get_sizes(probe_id: int, probe_nwb_filename: str):
    f = h5py.File(probe_nwb_filename, "r")
    lfp = f[f"acquisition/probe_{probe_id}_lfp/probe_{probe_id}_lfp_data/data"]
    ntime, nchannel = lfp.shape

    lfp_dtype = lfp.dtype
    lfp_compression_type = lfp.compression
    lfp_compression_level = lfp.compression_opts

    time = f[f"acquisition/probe_{probe_id}_lfp/probe_{probe_id}_lfp_data/timestamps"]
    time_dtype = time.dtype
    time_compression_type = time.compression
    time_compression_level = time.compression_opts

    chunk_size = dict(time=lfp.chunks[0], channel=lfp.chunks[1])
    f.close()

    return ntime, nchannel, lfp_dtype, lfp_compression_type, lfp_compression_level, \
        time_dtype, time_compression_type, time_compression_level, chunk_size


def _load_and_store(probe_id, probe_nwb_filename, time2d_data, refs):
    f = h5py.File(probe_nwb_filename, "r")
    time = f[f"acquisition/probe_{probe_id}_lfp/probe_{probe_id}_lfp_data/timestamps"]
    time2d_data[:] = time[:]
    f.close()

    # LFP data kept in original files, referenced chunkwise from kerchunk-created JSON file
    _get_kerchunk_refs(probe_id, probe_nwb_filename, refs)

    refs = kerchunk.utils.consolidate(refs)
    return refs


def nwb_kerchunk(probe_id: int, probe_nwb_filename: str, output_json_filename: str) -> None:
    """
    Read an NWB file containing a single probe's LFP data and create a
    kerchunked JSON file that references the chunks of the original file.
    """
    ntime, nchannel, lfp_dtype, lfp_compression_type, lfp_compression_level, time_dtype, \
        time_compression_type, time_compression_level, chunk_size = _get_sizes(probe_id, probe_nwb_filename)

    time2d_data, refs = _create_zarr_file(
        ntime, nchannel, lfp_dtype, lfp_compression_type, lfp_compression_level,
        time_dtype, time_compression_type, time_compression_level, chunk_size)

    refs = _load_and_store(probe_id, probe_nwb_filename, time2d_data, refs)

    with open(output_json_filename, "w") as f:
        ujson.dump(refs, f)
