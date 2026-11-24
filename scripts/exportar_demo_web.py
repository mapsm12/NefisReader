"""Genera el recurso estático de la web desde los NetCDF sintéticos del demo."""

import argparse
import json
from pathlib import Path

from netCDF4 import Dataset


def data(path, variables, shape):
    with Dataset(path) as ds:
        result = {}
        for key in variables:
            var = ds[f"map_series__{key}"]
            if var.shape != shape:
                raise ValueError(f"{key}: tamaño esperado {shape}, obtenido {var.shape}")
            var.set_auto_maskandscale(False)
            result[key] = {"shape": var.shape, "units": var.units, "values": var[:].tolist()}
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netcdf_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cases = {
        "wave": data(args.netcdf_dir / "wavm-demo-2d.nc", ("HSIGN", "RTP", "DIR", "XP", "YP"), (2, 3, 4)),
        "flow": data(args.netcdf_dir / "trim-demo-3d.nc", ("U1", "V1"), (2, 3, 3, 4)),
    }
    text = "// Generado desde las parejas sintéticas; regenerar con scripts/exportar_demo_web.py.\n"
    args.output.write_text(text + "const NEFIS_DEMO = " + json.dumps(cases, allow_nan=False, indent=2) + ";\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
