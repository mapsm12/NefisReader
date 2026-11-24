"""Local, read-only MCP tools for trusted Delft3D files."""

from __future__ import annotations

import argparse
from math import prod
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from netCDF4 import Dataset

from .converter import NefisFile, inventory

MAX_VALUES = 256
MAX_INSPECT = 50
MAX_NEFIS_BLOCK_BYTES = 32 * 1024**2
_IO = Lock()  # Native NEFIS and netCDF libraries are not generally thread-safe.


def _page(offset: int, limit: int) -> slice:
    if offset < 0 or not 1 <= limit <= MAX_INSPECT:
        raise ValueError(f"Use offset >= 0 y limit entre 1 y {MAX_INSPECT}.")
    return slice(offset, offset + limit)


def _allowed_file(root: Path, path: str, suffixes: tuple[str, ...]) -> Path:
    candidate = root / path
    if candidate.suffix.lower() not in suffixes:
        raise ValueError(f"Extensión esperada: {', '.join(suffixes)}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("La ruta está fuera del directorio autorizado.")
    if not resolved.is_file() or resolved.suffix.lower() not in suffixes:
        raise ValueError("No se encontró un archivo compatible dentro del directorio autorizado.")
    return resolved


def _pair(root: Path, path: str) -> tuple[Path, Path]:
    requested = Path(path)
    if requested.suffix.lower() == ".def":
        requested = requested.with_suffix(".dat")
    dat = _allowed_file(root, str(requested), (".dat",))
    definition = _allowed_file(root, str(requested.with_suffix(".def")), (".def",))
    return dat, definition


def _value(value):
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, np.ndarray):
        return _value(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_value(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if value is None or isinstance(value, (str, int, float, bool)) else str(value)


def _window(shape: tuple[int, ...], start: list[int], count: list[int]) -> tuple[slice, ...]:
    if len(start) != len(shape) or len(count) != len(shape):
        raise ValueError("Indique start y count para cada eje, en el orden informado.")
    if any(s < 0 or n < 1 or s + n > size for s, n, size in zip(start, count, shape)):
        raise ValueError("Ventana fuera de los límites de la variable.")
    if prod(count) > MAX_VALUES:
        raise ValueError(f"La muestra no puede superar {MAX_VALUES} valores.")
    return tuple(slice(s, s + n) for s, n in zip(start, count))


def build_server(root: Path):
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("--root debe ser una carpeta.")
    server = FastMCP("NefisReader")
    readonly = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

    @server.tool(annotations=readonly, structured_output=True)
    def inspect_nefis(path: str, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Inventaría elementos de una pareja NEFIS .dat/.def. Rutas relativas a --root."""
        page = _page(offset, limit)
        dat, definition = _pair(root, path)
        with _IO, NefisFile(dat, definition) as reader:
            groups = inventory(reader)["groups"]
        items = []
        for group in groups:
            for element in group["elements"]:
                items.append(dict(element, group=group["name"],
                                  raw_shape=group["group_shape"] + element["shape"][::-1]))
        return {"path": str(dat.relative_to(root)), "total": len(items),
                "offset": offset, "elements": items[page]}

    @server.tool(annotations=readonly, structured_output=True)
    def sample_nefis(path: str, group: str, element: str, start: list[int], count: list[int]) -> dict[str, Any]:
        """Lee una ventana numérica de NEFIS sin convertir. Usa el orden raw_shape del inventario."""
        dat, definition = _pair(root, path)
        with _IO, NefisFile(dat, definition) as reader:
            info = next((item for item in reader.groups() if item.name == group), None)
            cell = next((item for item in reader.cells() if info and item.name == info.cell_name), None)
            if cell is None or element not in cell.elements:
                raise ValueError("Grupo o elemento no encontrado; primero use inspect_nefis.")
            metadata = reader.element(element)
            if metadata.dtype.kind not in "iuf":
                raise ValueError("Solo se admiten elementos numéricos reales.")
            group_shape = reader.group_shape(info)
            shape = group_shape + metadata.shape[::-1]
            selection = _window(shape, start, count)
            # Getelt devuelve elementos completos. Acotar el bloque real, no solo la salida.
            block_shape = (count[0],) + shape[1:] if group_shape else shape
            if prod(block_shape) * metadata.item_size > MAX_NEFIS_BLOCK_BYTES:
                raise ValueError("Bloque NEFIS >32 MiB; convierta y use sample_netcdf.")
            if group_shape:
                slab = reader.read(info, metadata, start=start[0], count=count[0])
                selection = (slice(None),) + selection[1:]
            else:
                slab = reader.read(info, metadata)
            values = _value(np.asarray(slab[selection]))
        return {"group": group, "element": element, "shape": shape, "units": metadata.unit,
                "start": start, "count": count, "values": values}

    @server.tool(annotations=readonly, structured_output=True)
    def inspect_netcdf(path: str, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Lista variables raíz, dimensiones, unidades y metadatos NEFIS de un NetCDF local."""
        page = _page(offset, limit)
        nc = _allowed_file(root, path, (".nc", ".nc4"))
        with _IO, Dataset(str(nc)) as data:
            names = list(data.variables)
            variables = []
            for name in names[page]:
                var = data.variables[name]
                attributes = {key: _value(var.getncattr(key)) for key in
                              ("units", "long_name", "nefis_group", "nefis_element")
                              if key in var.ncattrs()}
                variables.append({"name": name, "shape": var.shape, "axes": var.dimensions,
                                  "dtype": str(var.dtype), "attributes": attributes})
        return {"path": str(nc.relative_to(root)), "total": len(names),
                "offset": offset, "variables": variables}

    @server.tool(annotations=readonly, structured_output=True)
    def sample_netcdf(path: str, variable: str, start: list[int], count: list[int]) -> dict[str, Any]:
        """Lee hasta 256 valores numéricos crudos; start usa base cero, count uno por eje."""
        nc = _allowed_file(root, path, (".nc", ".nc4"))
        with _IO, Dataset(str(nc)) as data:
            if variable not in data.variables:
                raise ValueError("Variable no encontrada; primero use inspect_netcdf.")
            var = data.variables[variable]
            if not isinstance(var.dtype, np.dtype) or var.dtype.kind not in "iuf":
                raise ValueError("Solo se admiten variables numéricas reales de tamaño fijo.")
            selection = _window(var.shape, start, count)
            var.set_auto_maskandscale(False)
            var.set_auto_chartostring(False)
            values = _value(np.asarray(var[selection]))
            units = _value(getattr(var, "units", None))
            axes, shape = var.dimensions, var.shape
        return {"variable": variable, "axes": axes, "shape": shape, "units": units,
                "start": start, "count": count, "values": values,
                "note": "Valores crudos: sin reescalado ni máscara; NaN/Inf se representan como null."}

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Carpeta de datos autorizada (solo lectura).")
    args = parser.parse_args()
    try:
        import mcp  # noqa: F401
    except ImportError:
        parser.exit(2, "Instale con Python >=3.10: bash scripts/install.sh --extra mcp\n")
    build_server(args.root).run(transport="stdio")


if __name__ == "__main__":
    main()
