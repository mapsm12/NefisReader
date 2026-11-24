"""Lee un plano WAVE y un corte/perfil FLOW de los NetCDF del demo.

En salidas propias verifica el orden de ejes antes de reutilizar los índices.
"""

import argparse
from pathlib import Path

import numpy as np
from netCDF4 import Dataset


def fixed_numeric(ds, name, rank):
    var = ds[name]
    if var.ndim != rank:
        raise ValueError(f"{name}: se esperan {rank} ejes verificados, se obtuvo {var.shape}")
    var.set_auto_maskandscale(False)
    return var


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wave", type=Path)
    parser.add_argument("flow", type=Path)
    parser.add_argument("--record", type=int, default=0)
    parser.add_argument("--layer", type=int, default=1)
    args = parser.parse_args()
    with Dataset(args.wave) as ds:
        hs = fixed_numeric(ds, "map_series__HSIGN", 3)  # demo: registro, fila, columna
        plane = hs[args.record, :, :]
        print("WAVE: HSIGN [registro, fila, columna]", hs.shape, hs.units)
        print(plane)
    with Dataset(args.flow) as ds:
        u = fixed_numeric(ds, "map_series__U1", 4)  # demo: registro, capa, fila, columna
        v = fixed_numeric(ds, "map_series__V1", 4)
        layer = u[args.record, args.layer, :, :]
        section = u[args.record, :, 1, :]
        profile = np.column_stack([u[args.record, :, 1, 2], v[args.record, :, 1, 2]])
        print("FLOW: U1 [registro, capa, fila, columna]", u.shape, u.units)
        print("Plano de una capa:\n", layer)
        print("Corte vertical en fila 1:\n", section)
        print("Perfil en (fila=1, columna=2); columnas U1 y V1:\n", profile)


if __name__ == "__main__":
    main()
