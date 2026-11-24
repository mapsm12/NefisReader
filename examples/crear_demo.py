"""Crea datos sintéticos, no resultados físicos ni una salida de Delft3D."""

import argparse
import ctypes as ct
import os
from pathlib import Path

import numpy as np

from nefisreader.converter import NefisFile


def _write_pair(directory: Path, name: str, variables: dict) -> Path:
    directory = directory.resolve()
    dat, definition = directory / f"{name}.dat", directory / f"{name}.def"
    directory.mkdir(parents=True, exist_ok=True)
    if any(path.exists() or path.is_symlink() for path in (dat, definition)):
        raise FileExistsError("La pareja demo ya existe; usa otro directorio.")
    lib = ct.CDLL(str(NefisFile._find_library(None)))
    pointer, integer, string = ct.POINTER(ct.c_int), ct.c_int, ct.c_char_p
    signatures = {
        "Crenef": [pointer, string, string, ct.c_char, ct.c_char],
        "Defelm": [pointer, string, string, integer, string, string, string, integer, pointer],
        "Defcel2": [pointer, string, integer, ct.POINTER(string)],
        "Defgrp": [pointer, string, string, integer, pointer, pointer],
        "Credat": [pointer, string, string],
        "Putelt": [pointer, string, string, pointer, pointer, ct.c_void_p],
        "Clsnef": [pointer],
    }
    for name, types in signatures.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = types, integer
    fd = ct.c_int()

    def call(name, *args):
        code = getattr(lib, name)(ct.byref(fd), *args)
        if code:
            raise RuntimeError(f"{name}: error NEFIS {code}")

    call("Crenef", os.fsencode(dat), os.fsencode(definition), b"N", b"c")
    try:
        records = next(iter(variables.values()))[0].shape[0]
        for element, (data, quantity, units, description) in variables.items():
            assert data.dtype == np.float32 and data.flags.c_contiguous and data.shape[0] == records
            dims_element = data.shape[:0:-1]
            call("Defelm", element, b"REAL", 4, quantity, units, description,
                 len(dims_element), (integer * len(dims_element))(*dims_element))
        nvar = len(variables)
        call("Defcel2", b"DEMO_CELL", nvar, (string * nvar)(*variables))
        dims = (integer * 5)(records, 1, 1, 1, 1)
        order = (integer * 5)(1, 2, 3, 4, 5)
        call("Defgrp", b"DEMO_GROUP", b"DEMO_CELL", 1, dims, order)
        call("Credat", b"map-series", b"DEMO_GROUP")
        window = (integer * 15)(1, records, 1, *([1] * 12))
        for element, (data, *_) in variables.items():
            call("Putelt", b"map-series", element, window, order, data.ctypes.data_as(ct.c_void_p))
    finally:
        call("Clsnef")
    return dat


def create_demo(directory: Path) -> Path:
    return _write_pair(directory, "demo", {
        b"HSIGN": (np.array([[0.5, 1, 1.5]], dtype="f4"), b"height", b"m",
                   b"Synthetic significant wave height"),
    })


def create_grids(directory: Path) -> list[Path]:
    # Values encode the indices to make transpositions visible in tests.
    t, j, i = np.indices((2, 3, 4), dtype="f4")
    wave = _write_pair(directory, "wavm-demo-2d", {
        b"HSIGN": (0.5 + t + j / 10 + i / 100, b"height", b"m", b"Synthetic wave height"),
        b"RTP": (12 + t + i / 10, b"peak period", b"s", b"Synthetic peak period"),
        b"DIR": (240 + 10 * t + i, b"wave direction", b"degree", b"Synthetic direction angle"),
        b"XP": (100 * i, b"x coordinate", b"m", b"Synthetic east coordinate"),
        b"YP": (100 * j, b"y coordinate", b"m", b"Synthetic north coordinate"),
    })
    t, k, j, i = np.indices((2, 3, 3, 4), dtype="f4")
    flow = _write_pair(directory, "trim-demo-3d", {
        b"U1": ((1000 * t + 100 * k + 10 * j + i) / 1000,
                b"velocity", b"m/s", b"Synthetic velocity component"),
        b"V1": (-(1000 * t + 100 * k + 10 * j + i) / 1000,
                b"velocity", b"m/s", b"Synthetic second velocity component"),
    })
    return [wave, flow]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--grids", action="store_true", help="Genera ejemplos 2D y 3D.")
    args = parser.parse_args()
    for path in create_grids(args.directory) if args.grids else [create_demo(args.directory)]:
        print(path)
