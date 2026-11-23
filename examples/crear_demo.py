"""Crea datos sintéticos, no resultados físicos ni una salida de Delft3D."""

import argparse
import ctypes as ct
import os
from pathlib import Path

from nefisreader.converter import NefisFile


def create_demo(directory: Path) -> Path:
    directory = directory.resolve()
    dat, definition = directory / "demo.dat", directory / "demo.def"
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
        call("Defelm", b"HSIGN", b"REAL", 4, b"height", b"m",
             b"Synthetic significant wave height", 1, (integer * 1)(3))
        call("Defcel2", b"DEMO_CELL", 1, (string * 1)(b"HSIGN"))
        dims = (integer * 5)(1, 1, 1, 1, 1)
        order = (integer * 5)(1, 2, 3, 4, 5)
        call("Defgrp", b"DEMO_GROUP", b"DEMO_CELL", 1, dims, order)
        call("Credat", b"map-series", b"DEMO_GROUP")
        call("Putelt", b"map-series", b"HSIGN", (integer * 15)(*([1] * 15)),
             order, (ct.c_float * 3)(0.5, 1.0, 1.5))
    finally:
        call("Clsnef")
    return dat


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(create_demo(parser.parse_args().directory))
