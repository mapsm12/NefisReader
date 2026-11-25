# NefisReader v0.1 — Delft3D 4 NEFIS to NetCDF

[English site](https://mapsm12.github.io/NefisReader/) ·
[Español](README.md) · [Bahasa Indonesia](https://mapsm12.github.io/NefisReader/docs/id.html) ·
[简体中文](https://mapsm12.github.io/NefisReader/docs/zh.html)

NefisReader is an open-source Python package for reading Delft3D 4
NEFIS `.dat/.def` pairs and exporting numerical fields to NetCDF-4.
It includes the `d3dnefis` command, a Python API, and an optional
local MCP server. You do not need Delft3D or MATLAB to read the files.

## Install on Linux

Use Python 3.9+ on Linux x86-64 and an internet connection to install the
Python dependencies. The installer sets up the included NEFIS library
inside the Python environment; no `sudo` required. If the prebuilt
library does not load, the installer attempts to build it from source
using a C and a C++ compiler.

```bash
git clone https://github.com/mapsm12/NefisReader.git
cd NefisReader
python3 -m venv .venv
source .venv/bin/activate
bash scripts/install.sh
d3dnefis examples/data
python examples/leer_mallas.py \
  examples/data/NETCDF_EXPORT/wavm-demo-2d.nc \
  examples/data/NETCDF_EXPORT/trim-demo-3d.nc --record 1 --layer 2
```

The synthetic WAVE example shows significant wave height on a
horizontal grid. The synthetic FLOW example shows a velocity layer,
vertical section, and profile. To inspect your own model outputs
without exporting them, use `d3dnefis /path/to/run --inventory`.
Conversion puts results in `NETCDF_EXPORT/` by default. The output
preserves raw dimensions and values; it does not reconstruct CF
coordinates, model time, or the geometry of staggered grids.

## Reproduce the maps

The [map gallery](https://mapsm12.github.io/NefisReader/docs/#mapas)
shows bathymetry with energy-transport vectors and significant
wave height with depth contours. The bay is synthetic; no wave
simulation or observations are involved.

```bash
bash scripts/install.sh --extra analysis
case_dir="$(mktemp -d)"
python examples/crear_demo.py "$case_dir" --map
d3dnefis "$case_dir/wavm-bahia-sintetica.dat"
python examples/graficar_oleaje.py \
  "$case_dir/NETCDF_EXPORT/wavm-bahia-sintetica.nc" \
  --synthetic --lang en --outdir "$case_dir/figures"
```

For your own gridded WAVE output, first verify co-located fields,
X/Y in metres, positive-down depth, and energy transport in W/m.
Adapt the wet/dry mask to your model before interpreting the result.

## MCP

Requires Python 3.10 or later. The server is local, read-only, and
limited to the directory passed with `--root`. It inventories
variables and reads small slices from NEFIS or NetCDF.

```bash
bash scripts/install.sh --extra mcp
codex mcp add nefisreader -- "$(command -v nefisreader-mcp)" --root /absolute/path/to/runs
codex mcp list
```

Start a new Codex session after registration. Other MCP clients can
launch the same executable in stdio mode with `--root` and the absolute
directory as arguments. Data returned by the tools can reach the
provider of the MCP client, so only allow files you intend to share.
See the [detailed MCP guide in Spanish](MCP.md) for tool arguments.

## Licence and support

The project's own code is [MIT-licensed](LICENSE).
Deltares' NEFIS library retains its own [source, licence and notices](native/README.md).
NefisReader is independent and is not endorsed by Deltares.

If you find it useful, click **Star** at the top of the GitHub
repository. If you'd like to donate, [get in touch](https://github.com/mapsm12/NefisReader/issues/new?title=NefisReader%20donation%20inquiry).
Please don't share payment details in that public issue.
