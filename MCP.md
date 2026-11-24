# NefisReader como servidor MCP

Servidor local **stdio**, de solo lectura. Funciona con las parejas
`.dat/.def` y con NetCDF, sin puertos, API keys ni una instalación de
Delft3D. Usa el [SDK oficial de MCP, serie 1.x](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
La instalación de referencia se probó en Linux x86-64 con Python 3.12;
el extra MCP requiere Python 3.10 o posterior.

## Instalar y registrar en Codex

```bash
git clone https://github.com/mapsm12/NefisReader.git
cd NefisReader
python3 -m venv .venv
source .venv/bin/activate
bash scripts/install.sh --extra mcp

# Para empezar con los ejemplos incluidos:
RUNS="$(mktemp -d)"
cp examples/data/*.dat examples/data/*.def "$RUNS/"
d3dnefis "$RUNS"
python examples/probar_mcp.py "$RUNS"

# O usa la ruta absoluta de tu directorio de corridas en lugar de "$RUNS".
codex mcp add nefisreader -- "$(pwd)/.venv/bin/nefisreader-mcp" --root "$RUNS"
codex mcp list
```

Abre una sesión nueva de Codex después de registrarlo. Usa una carpeta
persistente si quieres que la configuración sobreviva a la limpieza de
`/tmp`. Si lo ejecutas con Conda, activa tu entorno y usa la ruta
que devuelve `command -v nefisreader-mcp`.

## Configuración stdio en otro cliente

Agrega esta entrada al objeto `mcpServers` del cliente, por ejemplo en
`claude_desktop_config.json` donde Claude Desktop esté disponible.
Sustituye ambas rutas. El cliente debe poder ejecutar el comando en el
equipo que aloja Python y los datos. Si tu cliente está en otra máquina,
puedes configurar un comando SSH stdio que no pida interacción y que
ejecute esta misma línea en Linux; no se publica un endpoint HTTP.

```json
{
  "mcpServers": {
    "nefisreader": {
      "command": "/ruta/absoluta/NefisReader/.venv/bin/nefisreader-mcp",
      "args": ["--root", "/ruta/absoluta/a/corridas"]
    }
  }
}
```

Consulta la [guía oficial de servidores locales de Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).
La prueba incluida usa el cliente oficial MCP por stdio, no la interfaz de Claude Desktop.

## Herramientas y ejemplos

| Herramienta | Qué hace |
|---|---|
| `inspect_nefis` | Inventaría un par `.dat/.def`: grupo, elemento, tipo, unidades y `raw_shape`. |
| `sample_nefis` | Lee un recorte por grupo y elemento directamente del par, sin crear NetCDF. |
| `inspect_netcdf` | Lista variables raíz, dimensiones, unidades y metadatos disponibles. |
| `sample_netcdf` | Lee un recorte numérico de una variable NetCDF. |

Los inventarios aceptan `offset` y `limit`. Para las muestras,
`start` y `count` tienen un valor por eje en el orden del inventario,
con índice inicial en cero. Las muestras devuelven hasta 256 valores
crudos. Para NEFIS se limita además el bloque interno a 32 MiB: si un
registro completo supera ese tamaño, usa el conversor y consulta el
NetCDF. El servidor no reescala, no aplica máscara y no infiere
coordenadas ni el significado de los ejes.

Dos llamadas que puedes pedirle a tu agente:

```text
sample_nefis(path="wavm-demo-2d.dat", group="map-series", element="HSIGN",
             start=[1,1,2], count=[1,1,2])
sample_netcdf(path="NETCDF_EXPORT/trim-demo-3d.nc", variable="map_series__U1",
              start=[1,0,1,2], count=[1,3,1,1])
```

En el ejemplo WAVE una altura 2D se almacena como
`[registro, fila, columna]`. En el FLOW sintético una velocidad
espacial 3D se almacena como `[registro, capa, fila, columna]`.
En tus corridas puede variar el orden. Un tercer eje no prueba por sí
solo que haya capas: puede ser el eje de registros.

**Acceso:** usa un `--root` pequeño con archivos de confianza; el
servidor rechaza rutas que resuelven fuera de esa carpeta. No ejecuta
comandos ni escribe archivos. Los resultados de las herramientas
llegan al cliente MCP y pueden enviarse al proveedor de ese cliente;
no configures rutas con datos que no quieras compartir. La
conversión a archivo se hace aparte con `d3dnefis`.
