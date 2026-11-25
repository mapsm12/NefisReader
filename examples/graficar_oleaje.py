"""Dibuja dos mapas de una exportación NEFIS WAVE plana con unidades verificadas."""

import argparse
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.path import Path as PlotPath
import numpy as np
from netCDF4 import Dataset


def read_fields(path, record):
    units = {"XP": "M", "YP": "M", "DEPTH": "M", "HSIGN": "M",
             "TRANSP_X": "W/M", "TRANSP_Y": "W/M"}
    with Dataset(path) as ds:
        fields = {}
        for key, unit in units.items():
            var = ds[f"map_series__{key}"]
            actual = re.sub(r"[\s\[\]]+", "", getattr(var, "units", "")).upper()
            if actual != unit:
                raise ValueError(f"{key}: se esperaba {unit}, se encontró {actual!r}")
            if var.ndim != 3 or not 0 <= record < var.shape[0]:
                raise ValueError(f"{key}: se espera [registro, fila, columna]; forma real {var.shape}")
            fields[key] = np.ma.asarray(var[record], dtype=float).filled(np.nan)
    if len({field.shape for field in fields.values()}) != 1:
        raise ValueError("Las variables no están alineadas en la misma malla.")
    if not all(np.isfinite(fields[key]).all() for key in ("XP", "YP")):
        raise ValueError("Hay coordenadas no finitas; recorta o corrige la malla antes de dibujar.")
    return fields


def draw(fields, destination, synthetic, language="es"):
    x, y = fields["XP"] / 1000, fields["YP"] / 1000
    depth, hs = fields["DEPTH"], fields["HSIGN"]
    u, v = fields["TRANSP_X"] / 1000, fields["TRANSP_Y"] / 1000
    wet = np.isfinite(depth) & (depth > 0)
    if not wet.any():
        raise ValueError("No hay celdas húmedas con DEPTH > 0.")
    spanish = [
        ("batimetria_vectores.png", "Batimetría y transporte de energía", depth, "Profundidad (m)", "Blues", True),
        ("altura_isobatas.png", "Altura significativa e isóbatas", hs, "Altura significativa (m)", "viridis", False),
    ]
    english = [
        ("bathymetry_vectors.png", "Bathymetry and energy transport", depth, "Depth (m)", "Blues", True),
        ("height_depth_contours.png", "Wave height and depth contours", hs, "Significant wave height (m)", "viridis", False),
    ]
    texts = {
        "es": ("BAHÍA SINTÉTICA · EJEMPLO DE POSPROCESO", "SALIDA NEFIS · EJEMPLO DE POSPROCESO",
               "Gris: tierra (DEPTH ≤ 0).", "Gris: celdas excluidas por DEPTH ≤ 0 o no finito."),
        "en": ("SYNTHETIC BAY · POST-PROCESSING EXAMPLE", "NEFIS OUTPUT · POST-PROCESSING EXAMPLE",
               "Grey: land (DEPTH ≤ 0).", "Grey: cells excluded for DEPTH ≤ 0 or non-finite DEPTH."),
    }
    sub_synthetic, sub_real, foot_synthetic, foot_real = texts[language]
    ink = "#142f40"
    for filename, title, values, unit, palette, arrows in spanish if language == "es" else english:
        fig, ax = plt.subplots(figsize=(7.5, 5.9), dpi=160)
        fig.subplots_adjust(left=0.12, right=0.84, bottom=0.17, top=0.86)
        fig.set_facecolor("#ffffff")
        ax.set_facecolor("#eeeeea")
        shown = np.ma.masked_where(~wet | ~np.isfinite(values) | (values < 0), values)
        if shown.count() == 0:
            raise ValueError(f"No hay valores válidos para {title}.")
        high = max(float(shown.max()), 0.001)
        ticks = MaxNLocator(nbins=6).tick_values(0, high)
        top = float(ticks[-1])
        levels = np.linspace(0, top, 21)
        image = ax.contourf(x, y, shown, levels=levels, cmap=palette, corner_mask=True)
        cb = fig.colorbar(image, ax=ax, pad=0.035, ticks=ticks)
        cb.set_label(unit, color=ink)
        shore = np.where(wet, 1, 0)
        if np.any(~wet):
            ax.contour(x, y, shore, levels=[0.5], colors=["#566570"], linewidths=1.0)
        bathy = [level for level in (10, 20, 40) if np.nanmin(depth) < level < np.nanmax(depth)]
        if bathy:
            lines = ax.contour(x, y, np.where(wet, depth, 0), levels=bathy,
                               colors=["#254653" if arrows else "#ecfbff"], linewidths=0.65, alpha=0.74)
            if not arrows:
                ax.clabel(lines, fmt="%g m", fontsize=8, inline=True)
        if arrows:
            good = wet & np.isfinite(u) & np.isfinite(v)
            speed = np.hypot(u[good], v[good])
            if speed.size and speed.max() > 0:
                step = tuple(slice(None, None, max(1, size // 13)) for size in x.shape)
                ref = float(MaxNLocator(nbins=5).tick_values(0, speed.max())[2])
                extent = float(np.ptp(x))
                if extent <= 0:
                    raise ValueError("El eje X no tiene extensión.")
                q = ax.quiver(x[step], y[step], np.ma.array(u, mask=~good)[step],
                              np.ma.array(v, mask=~good)[step], color="#ffc669", edgecolor=ink,
                              linewidth=0.35, width=0.0037, angles="xy", scale_units="xy",
                              scale=ref / (extent * 0.042))
                clip = ax.contourf(x, y, shore, levels=[0.5, 1.5], colors=["none"])
                paths = clip.get_paths() if hasattr(clip, "get_paths") else [
                    path for collection in clip.collections for path in collection.get_paths()
                ]
                if paths:
                    q.set_clip_path(PlotPath.make_compound_path(*paths), ax.transData)
                ax.quiverkey(q, 0.95, -0.145, ref, f"{ref:g} kW/m", labelpos="W",
                             coordinates="axes", color="#ffc669", labelcolor=ink)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X (km)", color=ink)
        ax.set_ylabel("Y (km)", color=ink)
        ax.tick_params(colors=ink)
        for spine in ax.spines.values():
            spine.set_color("#89a6b4")
        fig.text(0.12, 0.94, title, fontsize=18, fontweight="bold", color=ink)
        fig.text(0.12, 0.895, sub_synthetic if synthetic else sub_real, fontsize=9, color="#365f71")
        foot = foot_synthetic if synthetic else foot_real
        fig.text(0.12, 0.043, foot, fontsize=8.5, color="#365f71")
        fig.savefig(destination / filename, pil_kwargs={"optimize": True})
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog="Comprueba X/Y en metros, DEPTH positivo hacia abajo, y componentes X/Y en W/m antes de usar datos propios.")
    parser.add_argument("netcdf", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--record", type=int, default=0)
    parser.add_argument("--synthetic", action="store_true", help="Marca los mapas como bahía sintética.")
    parser.add_argument("--lang", choices=("es", "en"), default="es", help="Idioma de las etiquetas y los títulos.")
    args = parser.parse_args()
    fields = read_fields(args.netcdf, args.record)
    args.outdir.mkdir(parents=True, exist_ok=True)
    draw(fields, args.outdir, args.synthetic, args.lang)


if __name__ == "__main__":
    main()
