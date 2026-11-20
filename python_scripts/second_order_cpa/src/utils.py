import numpy as np
import os
import trsfile


def HW(v):
    return sum([int(b) for b in bin(v)[2:]])


def bytes_to_u64(v: list):
    n = (v[0] << 56) | \
        (v[1] << 48) | \
        (v[2] << 40) | \
        (v[3] << 32) | \
        (v[4] << 24) | \
        (v[5] << 16) | \
        (v[6] << 8) | \
        v[7]
    return int(n)


def load_trace_matrix(config, indexes):

    nt_s = config.nt_s
    nt_e = config.nt_e
    _dtype = config.data_type

    trs_path = config.path_to_traces
    fixed_group_offset = 100000

    T = np.zeros(
        (nt_e - nt_s, len(indexes)),
        dtype=_dtype
    )

    with trsfile.open(trs_path, "r") as trs:

        for j, i in enumerate(indexes):

            if i < 0 or i >= 100000:
                raise IndexError(
                    f"Invalid fixed-group trace index: {i}"
                )

            actual_index = fixed_group_offset + i

            tr = np.asarray(
                trs[actual_index].samples,
                dtype=_dtype
            )

            T[:, j] = tr[nt_s:nt_e]

    print("[INFO] Loaded matrix of traces: ", end="")
    print(
        f"shape {T.shape}, size "
        f"{T.size * T.itemsize} B or "
        f"{T.size * T.itemsize / (10**9):.4f} GB"
    )

    return T
