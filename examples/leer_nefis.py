"""Inventario y lectura directa de un registro, sin crear NetCDF."""
import argparse
from pathlib import Path

from nefisreader import NefisFile, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dat", type=Path)
    parser.add_argument("--def-file", type=Path)
    parser.add_argument("--nefis-lib", type=Path)
    parser.add_argument("--group", default="map-series")
    parser.add_argument("--element", default="HSIGN")
    args = parser.parse_args()

    with NefisFile(args.dat, args.def_file or args.dat.with_suffix(".def"), args.nefis_lib) as nf:
        info = inventory(nf)
        for g in info["groups"]:
            print(g["name"], g["group_shape"], [e["name"] for e in g["elements"]])
        group = next((g for g in nf.groups() if g.name == args.group), None)
        cell = next((c for c in nf.cells() if group and c.name == group.cell_name), None)
        if cell is None or args.element not in cell.elements:
            parser.exit(2, "Selecciona un grupo y elemento del inventario mostrado.\n")
        if group.shape and nf.group_shape(group)[0] < 1:
            parser.exit(2, "El grupo no contiene registros.\n")
        elm = nf.element(args.element)
        array = nf.read(group, elm, start=0, count=1)
        print(f"{group.name}/{elm.name}: shape={array.shape}, dtype={array.dtype}, "
              f"unit={elm.unit!r}, description={elm.description!r}")


if __name__ == "__main__":
    main()
