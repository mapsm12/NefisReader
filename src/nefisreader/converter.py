#!/usr/bin/env python3
"""Conversor NEFIS (.dat/.def) a NetCDF, sin MATLAB.

Requiere: Python >=3.9, numpy, netCDF4 y una biblioteca NEFIS compatible
(nefis.so o libnefis.so de una instalación compatible). Este programa conserva los
valores crudos NEFIS; no pretende aplicar la semántica hidrodinámica de D3D.
"""

from __future__ import annotations

import argparse
import ctypes as ct
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


END_DATA_GROUPS = {-6022, -6021}
END_CELLS = {-6025, -6026}


class NefisError(RuntimeError):
    pass


def _text(value: bytes) -> str:
    return value.decode("latin-1", errors="replace").strip()


def _safe(value: str, used: set[str] | None = None) -> str:
    result = re.sub(r"[^0-9A-Za-z_]", "_", value.strip()).strip("_") or "unnamed"
    if result[0].isdigit():
        result = "v_" + result
    if used is not None:
        original, number = result, 2
        while result in used:
            result = f"{original}_{number}"
            number += 1
        used.add(result)
    return result


def _np_type(nefis_type: str, item_size: int) -> np.dtype:
    if nefis_type == "REAL" and item_size in (4, 8):
        return np.dtype("f4" if item_size == 4 else "f8")
    if nefis_type == "INTEGER" and item_size in (1, 2, 4, 8):
        return np.dtype(f"i{item_size}")
    # NEFIS LOGICAL is stored as a four-byte Fortran logical in Delft3D.
    # NetCDF has no portable logical type, so preserve its raw 0/1 values.
    if nefis_type == "LOGICAL" and item_size in (1, 2, 4, 8):
        return np.dtype(f"i{item_size}")
    if nefis_type == "CHARACTE":
        return np.dtype(f"S{item_size}")
    raise NefisError(f"Tipo NEFIS no soportado: {nefis_type!r}, {item_size} bytes")


@dataclass(frozen=True)
class Element:
    name: str
    nefis_type: str
    item_size: int
    quantity: str
    unit: str
    description: str
    shape: tuple[int, ...]

    @property
    def dtype(self) -> np.dtype:
        return _np_type(self.nefis_type, self.item_size)


@dataclass(frozen=True)
class Cell:
    name: str
    nbytes: int
    elements: tuple[str, ...]


@dataclass(frozen=True)
class Group:
    name: str
    cell_name: str
    shape: tuple[int, ...]
    order: tuple[int, ...]


class NefisFile:
    """Pequeña envoltura ctypes sobre la API pública C de NEFIS."""

    def __init__(self, dat_file: Path, def_file: Path, library: Path | None = None):
        self.dat_file = Path(dat_file)
        self.def_file = Path(def_file)
        self.library_path = self._find_library(library)
        self.lib = ct.CDLL(str(self.library_path), mode=ct.RTLD_GLOBAL)
        self.fd = ct.c_int(0)
        self._groups: list[Group] | None = None
        self._cells: list[Cell] | None = None
        self._elements: dict[str, Element] = {}

    @staticmethod
    def _find_library(library: Path | None) -> Path:
        if library is not None:
            path = library.expanduser().resolve()
            if not path.is_file():
                raise NefisError(f"No existe la biblioteca indicada: {path}")
            return path
        candidates = []
        env_library = os.environ.get("NEFIS_LIB")
        if env_library:
            candidates.append(Path(env_library))
        prefix = os.environ.get("DELFT3D_HOME")
        if prefix:
            candidates.extend(Path(prefix) / directory / name
                              for directory in ("lib", "lib64", "lib/delft3d", "bin")
                              for name in ("nefis.so", "libnefis.so"))
        candidates.append(Path(sys.prefix) / "lib" / "nefisreader" / "libnefis.so")
        for candidate in candidates:
            candidate = candidate.expanduser().resolve()
            if candidate.is_file():
                return candidate
        shown = ", ".join(str(x) for x in candidates if x)
        raise NefisError("No se encontró libnefis.so. Ejecute bash scripts/install.sh "
                         "desde el repositorio o use --nefis-lib / NEFIS_LIB. " + shown)

    def _error_text(self) -> str:
        buf = ct.create_string_buffer(1025)
        try:
            # Las versiones de Delft3D usan nefis_error; algunas exportan Neferr.
            fn = getattr(self.lib, "nefis_error", None) or getattr(self.lib, "Neferr")
            fn(0, ct.byref(buf))
            return _text(buf.value)
        except Exception:
            return "sin descripción de la biblioteca NEFIS"

    def _check(self, rc: int, operation: str) -> None:
        if rc:
            raise NefisError(f"{operation}: NEFIS devolvió {rc}: {self._error_text()}")

    def open(self) -> "NefisFile":
        if not self.dat_file.is_file() or not self.def_file.is_file():
            raise NefisError(f"Falta la pareja NEFIS: {self.dat_file} / {self.def_file}")
        create = self.lib.Crenef
        create.argtypes = [ct.POINTER(ct.c_int), ct.c_char_p, ct.c_char_p,
                           ct.c_char, ct.c_char]
        create.restype = ct.c_int
        rc = create(
            ct.byref(self.fd), os.fsencode(self.dat_file), os.fsencode(self.def_file),
            b"N", b"r",
        )
        self._check(rc, "Crenef")
        return self

    def close(self) -> None:
        if self.fd is not None:
            rc = self.lib.Clsnef(ct.byref(self.fd))
            self.fd = None
            self._check(rc, "Clsnef")

    def __enter__(self) -> "NefisFile":
        return self.open()

    def __exit__(self, *_: object) -> None:
        self.close()

    def groups(self) -> list[Group]:
        if self._groups is not None:
            return self._groups
        groups: list[Group] = []
        while True:
            data_name, definition = ct.create_string_buffer(17), ct.create_string_buffer(17)
            function = self.lib.Inqfst if not groups else self.lib.Inqnxt
            rc = function(ct.byref(self.fd), data_name, definition)
            if rc in END_DATA_GROUPS:
                break
            self._check(rc, "Inqfst/Inqnxt")
            cell_name = ct.create_string_buffer(17)
            ndim = ct.c_int(5)
            dims, order = np.ones(5, dtype="i4"), np.ones(5, dtype="i4")
            rc = self.lib.Inqgrp(ct.byref(self.fd), definition, cell_name,
                                 ct.byref(ndim), dims.ctypes, order.ctypes)
            self._check(rc, f"Inqgrp({_text(definition.value)})")
            groups.append(Group(_text(data_name.value), _text(cell_name.value),
                                tuple(int(x) for x in dims[:ndim.value]),
                                tuple(int(x) for x in order[:ndim.value])))
        self._groups = groups
        return groups

    def cells(self) -> list[Cell]:
        if self._cells is not None:
            return self._cells
        cells: list[Cell] = []
        while True:
            cell_name, capacity, nbytes = ct.create_string_buffer(b" " * 16), 256, ct.c_int(0)
            count = ct.c_int(capacity)
            element_names = ((ct.c_char * 17) * capacity)()
            function = self.lib.Inqfcl if not cells else self.lib.Inqncl
            rc = function(ct.byref(self.fd), ct.byref(cell_name), ct.byref(count),
                          ct.byref(nbytes), ct.byref(element_names))
            if rc in END_CELLS:
                break
            self._check(rc, "Inqfcl/Inqncl")
            cells.append(Cell(_text(cell_name.value), nbytes.value,
                              tuple(_text(element_names[i].value) for i in range(count.value))))
        self._cells = cells
        return cells

    def element(self, name: str) -> Element:
        if name in self._elements:
            return self._elements[name]
        element_name = (ct.c_char * 17)()
        element_name.value = name.encode()
        element_type = ct.create_string_buffer(b" " * 9)
        item_size, ndim = ct.c_int(0), ct.c_int(5)
        quantity, unit, description = (ct.c_char * 17)(), (ct.c_char * 17)(), (ct.c_char * 65)()
        quantity.value, unit.value, description.value = b" " * 16, b" " * 16, b" " * 64
        dimensions = np.ones(5, dtype="i4")
        rc = self.lib.Inqelm(ct.byref(self.fd), ct.byref(element_name), ct.byref(element_type),
                             ct.byref(item_size), ct.byref(quantity), ct.byref(unit),
                             ct.byref(description), ct.byref(ndim), dimensions.ctypes)
        self._check(rc, f"Inqelm({name})")
        element = Element(name, _text(element_type.value), item_size.value, _text(quantity.value),
                          _text(unit.value), _text(description.value),
                          tuple(int(x) for x in dimensions[:ndim.value]))
        self._elements[name] = element
        return element

    def group_length(self, group: Group) -> int:
        name, maximum = ct.create_string_buffer(group.name.encode(), 17), ct.c_int(-1)
        rc = self.lib.Inqmxi(ct.byref(self.fd), ct.byref(name), ct.byref(maximum))
        self._check(rc, f"Inqmxi({group.name})")
        return maximum.value

    def group_shape(self, group: Group) -> tuple[int, ...]:
        return tuple(self.group_length(group) if size == 0 else size for size in group.shape)

    def read(self, group: Group, element: Element, start: int = 0, count: int | None = None) -> np.ndarray:
        full_shape = self.group_shape(group)
        if group.shape:
            if count is None:
                count = full_shape[0] - start
            selected_shape = (count,) + full_shape[1:]
            indices = np.ones((len(group.shape), 3), dtype="i4")
            indices[:, 1] = np.asarray(full_shape, dtype="i4")
            indices[0] = (start + 1, start + count, 1)
            order = np.arange(1, len(group.shape) + 1, dtype="i4")
        else:
            selected_shape, indices, order = (), np.empty((0, 3), dtype="i4"), np.empty(0, dtype="i4")
        result_shape = selected_shape + tuple(reversed(element.shape))
        from math import prod
        size = prod(result_shape)
        byte_count = size * element.item_size
        if byte_count > np.iinfo(np.int32).max:
            raise NefisError(f"{group.name}/{element.name}: bloque >= 2 GiB; reduzca --block-records")
        values = np.empty(size, dtype=element.dtype)
        buffer_size = ct.c_int(byte_count)
        group_name, element_name = ct.create_string_buffer(group.name.encode()), ct.create_string_buffer(element.name.encode())
        rc = self.lib.Getelt(ct.byref(self.fd), ct.byref(group_name), ct.byref(element_name),
                             indices.ctypes, order.ctypes, ct.byref(buffer_size), values.ctypes)
        self._check(rc, f"Getelt({group.name}/{element.name})")
        return values.reshape(result_shape)


def inventory(nefis: NefisFile) -> dict[str, object]:
    cells = {cell.name: cell for cell in nefis.cells()}
    result: list[dict[str, object]] = []
    for group in nefis.groups():
        cell = cells.get(group.cell_name)
        elements = [] if cell is None else [nefis.element(name).__dict__ for name in cell.elements]
        result.append({"name": group.name, "cell": group.cell_name, "group_shape": nefis.group_shape(group),
                       "order": group.order, "elements": elements})
    return {"dat_file": str(nefis.dat_file), "def_file": str(nefis.def_file), "nefis_library": str(nefis.library_path), "groups": result}


def export_netcdf(nefis: NefisFile, output: Path, block_records: int, compression: int) -> dict[str, object]:
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise NefisError("Falta netCDF4. Instale con: python -m pip install netCDF4") from exc
    cells = {cell.name: cell for cell in nefis.cells()}
    output.parent.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[dict[str, str]] = []
    with Dataset(output, "w", format="NETCDF4") as nc:
        nc.setncattr("title", "Exportación cruda de Delft3D NEFIS")
        nc.setncattr("source_dat", str(nefis.dat_file))
        nc.setncattr("source_def", str(nefis.def_file))
        nc.setncattr("nefis_library", str(nefis.library_path))
        nc.setncattr("history", "Creado por d3dnefis.py; las dimensiones son crudas y pueden requerir interpretación Delft3D.")
        used_names: set[str] = set()
        for group in nefis.groups():
            cell = cells.get(group.cell_name)
            if cell is None:
                skipped.append({"group": group.name, "reason": f"celda {group.cell_name} no encontrada"})
                continue
            group_shape = nefis.group_shape(group)
            for element_name in cell.elements:
                element = nefis.element(element_name)
                if element.nefis_type == "CHARACTE":
                    skipped.append({"group": group.name, "element": element.name, "reason": "campo CHARACTER (no exportado en esta versión)"})
                    continue
                variable_name = _safe(f"{group.name}__{element.name}", used_names)
                shape = group_shape + tuple(reversed(element.shape))
                dimensions = tuple(f"{variable_name}_d{i + 1}" for i in range(len(shape)))
                for dimension, length in zip(dimensions, shape):
                    nc.createDimension(dimension, int(length))
                variable = nc.createVariable(variable_name, element.dtype, dimensions, zlib=True, complevel=compression)
                variable.setncattr("nefis_group", group.name)
                variable.setncattr("nefis_cell", group.cell_name)
                variable.setncattr("nefis_element", element.name)
                variable.setncattr("nefis_type", element.nefis_type)
                variable.setncattr("nefis_element_shape", json.dumps(element.shape))
                if element.quantity:
                    variable.setncattr("quantity", element.quantity)
                if element.unit:
                    variable.setncattr("units", element.unit)
                if element.description:
                    variable.setncattr("long_name", element.description)
                first_dimension = group_shape[0] if group_shape else 1
                for start in range(0, first_dimension, max(1, block_records)):
                    count = min(max(1, block_records), first_dimension - start)
                    values = nefis.read(group, element, start=start if group_shape else 0,
                                        count=count if group_shape else None)
                    index = (slice(start, start + count),) + (slice(None),) * (values.ndim - 1) if group_shape else (...,)
                    variable[index] = values
                written.append(variable_name)
    return {"output": str(output), "variables_written": written, "skipped": skipped}


def _discover(sources: list[str], def_file: str | None) -> list[tuple[Path, Path]]:
    """Devuelve parejas NEFIS completas, sin recorrer directorios ajenos."""
    requested = [Path(source).expanduser() for source in sources] or [Path.cwd()]
    pairs: list[tuple[Path, Path]] = []
    seen: set[Path] = set()
    for requested_path in requested:
        if requested_path.is_dir():
            dat_files = sorted(requested_path.glob("*.dat"))
        elif requested_path.suffix.lower() == ".dat":
            dat_files = [requested_path]
        elif requested_path.suffix.lower() == ".def":
            dat_files = [requested_path.with_suffix(".dat")]
        else:
            raise NefisError(f"{requested_path}: indique un .dat, un .def o un directorio")
        for dat_file in dat_files:
            dat_file = dat_file.resolve()
            if dat_file in seen:
                continue
            matching_def = Path(def_file).expanduser().resolve() if def_file else dat_file.with_suffix(".def")
            if not matching_def.is_file():
                print(f"AVISO: se omite {dat_file.name}: falta {matching_def.name}", file=sys.stderr)
                continue
            seen.add(dat_file)
            pairs.append((dat_file, matching_def))
    if not pairs:
        raise NefisError("No se encontraron parejas .dat/.def en el directorio. "
                         "Ejecute d3dnefis dentro del caso o: d3dnefis /ruta/al/caso")
    return pairs


def _default_output(dat_file: Path, outdir: str | None) -> Path:
    directory = Path(outdir).expanduser().resolve() if outdir else dat_file.parent / "NETCDF_EXPORT"
    return directory / f"{dat_file.stem}.nc"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convierte NEFIS Delft3D .dat/.def a NetCDF sin MATLAB.")
    parser.add_argument("sources", nargs="*", metavar="ARCHIVO_O_DIRECTORIO",
                        help=".dat, .def o directorio; sin argumentos convierte todas las parejas del directorio actual")
    parser.add_argument("--file", action="append", default=[], help="compatibilidad: archivo .dat NEFIS")
    parser.add_argument("--def-file", help="archivo .def; solo es válido con un único .dat")
    parser.add_argument("--nefis-lib", help="ruta a libnefis.so")
    parser.add_argument("--inventory", action="store_true", help="solo identifica las parejas y sus grupos")
    parser.add_argument("--output", help="NetCDF de salida; solo es válido con un único .dat")
    parser.add_argument("--outdir", help="directorio de salida; por defecto: NETCDF_EXPORT dentro de cada caso")
    parser.add_argument("--force", action="store_true", help="sobrescribe NetCDF existentes")
    parser.add_argument("--json", action="store_true", help="imprime el inventario/reporte detallado en JSON")
    parser.add_argument("--block-records", type=int, default=32, help="registros por bloque (por defecto: 32)")
    parser.add_argument("--compression", type=int, default=1, choices=range(10), metavar="0..9", help="compresión NetCDF")
    args = parser.parse_args(argv)
    if args.block_records < 1:
        parser.error("--block-records debe ser positivo")
    sources = args.sources + args.file
    if args.def_file and len(sources) > 1:
        parser.error("--def-file solo admite un archivo de entrada")
    if args.output and len(sources) > 1:
        parser.error("--output solo admite un archivo de entrada; use --outdir para varios")
    try:
        pairs = _discover(sources, args.def_file)
        if args.def_file and len(pairs) != 1:
            parser.error("--def-file solo admite exactamente una pareja NEFIS")
        if args.output and len(pairs) != 1:
            parser.error("--output solo admite exactamente una pareja NEFIS; use --outdir para varias")
        if not args.inventory:
            outputs = [(Path(args.output).expanduser() if args.output else
                        _default_output(dat, args.outdir)).resolve() for dat, _ in pairs]
            if any(path.suffix.lower() != ".nc" for path in outputs):
                raise NefisError("Las salidas deben terminar en .nc")
            if set(outputs) & {p for pair in pairs for p in pair}:
                raise NefisError("Una salida coincide con un archivo de entrada")
            if len(set(outputs)) != len(outputs):
                raise NefisError("Varias parejas producirían la misma salida: use destinos separados")
        print(f"NEFIS detectados: {len(pairs)} pareja(s)")
        failures = 0
        converted = 0
        skipped_existing = 0
        detailed: list[dict[str, object]] = []
        for number, (dat_file, def_file) in enumerate(pairs, start=1):
            try:
                with NefisFile(dat_file, def_file, Path(args.nefis_lib) if args.nefis_lib else None) as nefis:
                    if args.inventory:
                        item = inventory(nefis)
                        detailed.append(item)
                        numeric = sum(1 for group in item["groups"] for element in group["elements"]
                                      if element["nefis_type"] != "CHARACTE")
                        print(f"[{number}/{len(pairs)}] {dat_file.name}: {len(item['groups'])} grupos, {numeric} campos numéricos")
                        continue
                    output = Path(args.output).expanduser().resolve() if args.output else _default_output(dat_file, args.outdir)
                    if output.exists() and not args.force:
                        print(f"[{number}/{len(pairs)}] {dat_file.name}: OMITIDO (ya existe {output}; use --force)")
                        skipped_existing += 1
                        continue
                    print(f"[{number}/{len(pairs)}] {dat_file.name} -> {output}")
                    # Escribir primero a un archivo temporal evita reemplazar una
                    # salida válida si el trabajo se corta o falla a mitad de camino.
                    temporary_output = output.with_name(f".{output.name}.d3dnefis-{os.getpid()}.partial")
                    try:
                        if temporary_output.exists():
                            temporary_output.unlink()
                        report = export_netcdf(nefis, temporary_output, args.block_records, args.compression)
                        os.replace(temporary_output, output)
                    except BaseException:
                        if temporary_output.exists():
                            temporary_output.unlink()
                        raise
                    report["output"] = str(output)
                    detailed.append(report)
                    converted += 1
                    print(f"  OK: {len(report['variables_written'])} variables; {len(report['skipped'])} campos de texto omitidos")
            except (NefisError, OSError, ValueError) as exc:
                failures += 1
                print(f"[{number}/{len(pairs)}] ERROR en {dat_file.name}: {exc}", file=sys.stderr)
        if args.json:
            print(json.dumps(detailed, indent=2, ensure_ascii=False))
        if not args.inventory:
            print(f"Terminado: {converted} convertido(s), {skipped_existing} omitido(s), {failures} error(es).")
        return 2 if failures else 0
    except (NefisError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
