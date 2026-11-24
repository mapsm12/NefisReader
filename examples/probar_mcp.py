"""Prueba el transporte stdio con las parejas de ejemplo ya convertidas."""

import argparse
import asyncio
from pathlib import Path
import sys

import numpy as np
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(root):
    server = StdioServerParameters(command=sys.executable,
                                   args=["-m", "nefisreader.mcp_server", "--root", str(root.resolve())])
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = {tool.name for tool in (await session.list_tools()).tools}
        assert {"inspect_nefis", "sample_nefis", "inspect_netcdf", "sample_netcdf"} <= tools

        async def call(name, **kwargs):
            result = await session.call_tool(name, kwargs)
            if result.isError:
                raise RuntimeError(result.content)
            return result.structuredContent

        inventory = await call("inspect_nefis", path="wavm-demo-2d.def")
        hs = next(item for item in inventory["elements"] if item["name"] == "HSIGN")
        assert hs["raw_shape"] == [2, 3, 4]
        out = await call("sample_nefis", path="wavm-demo-2d.dat", group="map-series",
                         element="HSIGN", start=[1, 1, 2], count=[1, 1, 2])
        np.testing.assert_allclose(out["values"], [[[1.62, 1.63]]])

        nc = "NETCDF_EXPORT/trim-demo-3d.nc"
        flow = await call("inspect_netcdf", path=nc)
        u = next(item for item in flow["variables"] if item["name"] == "map_series__U1")
        assert u["shape"] == [2, 3, 3, 4]
        window = dict(start=[1, 0, 1, 2], count=[1, 3, 1, 1])
        a = await call("sample_netcdf", path=nc, variable=u["name"], **window)
        b = await call("sample_nefis", path="trim-demo-3d.dat", group="map-series", element="U1", **window)
        np.testing.assert_allclose(np.ravel(a["values"]), [1.012, 1.112, 1.212])
        np.testing.assert_array_equal(a["values"], b["values"])

        invalid = await session.call_tool("inspect_netcdf", {"path": "../outside.nc"})
        assert invalid.isError and "fuera" in str(invalid.content)
        print("MCP stdio: inventarios, recortes 2D y 3D, paridad NEFIS/NetCDF y acceso acotado: OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    asyncio.run(check(parser.parse_args().root))
