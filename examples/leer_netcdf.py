"""Inspecciona un NetCDF crudo; opcionalmente grafica HSIGN de WAVE."""
import argparse

import numpy as np
import xarray as xr


def find(ds, element, preferred_group="map-series"):
    matches = [(name, v) for name, v in ds.data_vars.items()
               if v.attrs.get("nefis_element") == element]
    preferred = [(name, v) for name, v in matches if v.attrs.get("nefis_group") == preferred_group]
    found = preferred or matches
    if len(found) != 1:
        raise ValueError(f"No se identificó {element} sin ambigüedad: {[n for n, _ in found]}")
    return found[0][1]


def section(v, record):
    if v.ndim == 3:
        if not 0 <= record < v.shape[0]:
            raise ValueError(f"Registro {record} no disponible en {v.name}: {v.shape}")
        v = v.isel({v.dims[0]: record})
    a = np.asarray(v.values)
    if a.ndim != 2:
        raise ValueError(f"Se esperaba (registro,y,x) o (y,x), no {a.shape}: {v.name}")
    return a


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("nc")
    p.add_argument("--record", type=int, default=0)
    p.add_argument("--plot")
    p.add_argument("--missing", type=float, action="append", default=[],
                   help="Valor de relleno de HSIGN conocido para tu caso; repetible")
    args = p.parse_args()
    with xr.open_dataset(args.nc, decode_times=False, mask_and_scale=False) as ds:
        for key, v in ds.data_vars.items():
            print(key, v.shape, v.attrs.get("units", ""), v.attrs.get("long_name", ""))
        if not args.plot:
            return
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        v = find(ds, "HSIGN")
        h = section(v, args.record).astype(float)
        for missing in args.missing:
            h[h == missing] = np.nan
        h[h < 0] = np.nan  # Altura negativa no física; no inferir máscara costera.
        x, y = (section(find(ds, e), args.record) for e in ("XP", "YP"))
        if x.shape != h.shape or y.shape != h.shape:
            raise ValueError(f"Mallas no coinciden: {x.shape}, {y.shape} y {h.shape}")
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(h)
        # Puntos, no interpolación ni asignación automática de CRS.
        fig, ax = plt.subplots()
        im = ax.scatter(x[valid], y[valid], c=h[valid], s=4)
        ax.set(xlabel="XP (coordenada nativa)", ylabel="YP (coordenada nativa)",
               title=f"Altura significativa · registro {args.record}")
        ax.set_aspect("equal")
        fig.colorbar(im, ax=ax, label=v.attrs.get("units", "unidad no declarada"))
        fig.savefig(args.plot, dpi=160, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()
