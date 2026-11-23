import numpy as np
import pytest
from netCDF4 import Dataset

from nefisreader import NefisError, NefisFile, export_netcdf
from nefisreader.converter import Cell, Element, Group, _discover, _np_type, main


def test_discovery_no_recursion_and_dedup(tmp_path):
    dat, deff = tmp_path / "wave.dat", tmp_path / "wave.def"
    for p in [dat, deff, tmp_path / "incomplete.dat"]:
        p.touch()
    assert _discover([str(tmp_path), str(dat), str(deff)], None) == [(dat, deff)]


def test_output_cannot_overwrite_input(tmp_path):
    for name in ("w.dat", "w.def"):
        (tmp_path / name).touch()
    assert main([str(tmp_path), "--force", "--output", str(tmp_path / "w.dat")]) == 2
    assert (tmp_path / "w.dat").read_bytes() == b""


def test_missing_explicit_library_does_not_fall_back(tmp_path, monkeypatch):
    p = tmp_path / "nefis.so"
    p.touch()
    monkeypatch.setenv("NEFIS_LIB", str(p))
    assert NefisFile._find_library(None) == p
    with pytest.raises(NefisError):
        NefisFile._find_library(tmp_path / "missing.so")


def test_unsupported_real_size():
    with pytest.raises(NefisError):
        _np_type("REAL", 3)


def test_synthetic_export(tmp_path):
    """Ejercita escritura de NetCDF y dimensiones sin llamar a una DLL."""
    class Synthetic:
        dat_file, def_file, library_path = "synthetic.dat", "synthetic.def", "synthetic"
        def cells(self): return [Cell("wave", 24, ("HSIGN",))]
        def groups(self): return [Group("map_series", "wave", (2,), (1,))]
        def group_shape(self, group): return group.shape
        def element(self, name): return Element(name, "REAL", 4, "", "m", "Synthetic", (3, 2))
        def read(self, group, element, start, count):
            return np.arange(start*6, (start+count)*6, dtype="f4").reshape(count, 2, 3)

    p = tmp_path / "test.nc"
    report = export_netcdf(Synthetic(), p, 1, 1)
    with Dataset(p) as ds:
        assert report["variables_written"] == ["map_series__HSIGN"]
        v = ds["map_series__HSIGN"]
        assert v.shape == (2, 2, 3)
        assert v.units == "m"
        np.testing.assert_array_equal(v[:], np.arange(12).reshape(2, 2, 3))
