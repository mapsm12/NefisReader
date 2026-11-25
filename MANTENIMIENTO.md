# NefisReader v0.1 — uso y mantenimiento

NefisReader es un paquete Python instalable para leer parejas NEFIS
`.dat/.def` de Delft3D 4 y exportar sus variables numéricas crudas a
NetCDF-4. No instala ni ejecuta el modelo Delft3D. El explorador web
solo muestra extractos sintéticos y no acepta archivos locales.

- Repositorio: [mapsm12/NefisReader](https://github.com/mapsm12/NefisReader).
- Página pública: [mapsm12.github.io/NefisReader](https://mapsm12.github.io/NefisReader/).
- Versión del paquete: `0.1.0` (`v0.1` en la web). Sustituye la
  numeración de iteraciones previas de desarrollo (`0.2.0`, `0.3.0`)
  que quedaron en el historial de Git, sin una publicación previa etiquetada.
  No se distribuye mediante PyPI: se instala desde el repositorio.

## Instalar y verificar

```bash
git clone https://github.com/mapsm12/NefisReader.git
cd NefisReader
python3 -m venv .venv
source .venv/bin/activate
bash scripts/install.sh
python -c 'from importlib.metadata import version; print(version("NefisReader"))'
```

Linux x86-64 y Python 3.9+ para el lector. No requiere `sudo`, MATLAB
ni Delft3D instalado. Necesita acceso a las dependencias de Python y no
usa el binario privado del clúster. La biblioteca `libnefis.so` se instala
dentro del entorno.
Con Conda se puede usar `conda env create -f environment.yml`,
`conda activate nefisreader` y el mismo instalador. Para cambiar desde
una iteración previa, vuelve a ejecutar el instalador desde un clon
actualizado y verifica la versión con el comando anterior.

El instalador verifica el binario y lo carga; si no es compatible,
intenta compilar la biblioteca con un compilador C/C++. Para probar
explícitamente desde fuentes, usa un entorno nuevo con
`NEFIS_BUILD_FROM_SOURCE=1 bash scripts/install.sh`. No reemplaza una
biblioteca ya instalada. Consulta [la ficha nativa](native/README.md).

## Leer 2D y 3D, y usar el MCP

```bash
runs="$(mktemp -d)"
cp examples/data/*.dat examples/data/*.def "$runs/"
d3dnefis "$runs" --inventory
d3dnefis "$runs"
python examples/leer_mallas.py "$runs/NETCDF_EXPORT/wavm-demo-2d.nc" \
  "$runs/NETCDF_EXPORT/trim-demo-3d.nc" --record 1 --layer 2
```

`examples/leer_nefis.py` lee directamente desde la pareja;
`examples/leer_netcdf.py` abre o grafica el NetCDF con el extra
`analysis`. WAVE 2D muestra un plano por registro; FLOW espacial 3D
incluye capas. El orden en archivos reales debe comprobarse con los
metadatos del modelo. No se infieren coordenadas CF, máscaras, datum,
tiempos físicos ni geometría escalonada.

API Python mínima, usando las mismas parejas:

```python
from pathlib import Path
from nefisreader import NefisFile, inventory

dat = Path("examples/data/wavm-demo-2d.dat")
with NefisFile(dat, dat.with_suffix(".def")) as reader:
    summary = inventory(reader)
    print(summary["groups"])
```

Para el [MCP](MCP.md), Python 3.10+:

```bash
bash scripts/install.sh --extra mcp
python examples/probar_mcp.py "$runs"
codex mcp add nefisreader -- "$(command -v nefisreader-mcp)" --root /ruta/absoluta/a/tus/corridas
```

Reinicia Codex tras registrar el MCP. Usa una raíz persistente y acotada:
el servidor local solo inventaría y lee recortes de archivos autorizados.
La salida de las herramientas puede llegar al proveedor del cliente MCP.

## Actualizar la web y publicar cambios

1. Revisa el estado remoto y las modificaciones antes de editar. Los
   metadatos Python están en `pyproject.toml`, la portada en
   `docs/index.html` y el acceso principal en `index.html`.
2. GitHub Pages usa la rama `main` desde la raíz. El `index.html` de la
   raíz lleva a `/docs/`. La copia anterior de Sites quedó privada; no
   la uses como publicación. No hace falta iniciar sesión allí.
3. Para regenerar los valores web, convierte las parejas sintéticas y
   ejecuta `python scripts/exportar_demo_web.py "$runs/NETCDF_EXPORT" docs/demo-data.js`.
   No uses salidas reales como recurso público.
4. Ejecuta las pruebas unitarias (`python -m pip install '.[test]'`,
   `python -m pytest -q`) y el smoke test del MCP. Prueba la página
   con `python3 -m http.server 8000` y abre
   `http://localhost:8000/docs/`. Verifica en el navegador ambos
   ejemplos, el cambio de capa y la descarga CSV.
5. Publica en `main` con una sesión GitHub autorizada, verifica
   [Actions](https://github.com/mapsm12/NefisReader/actions) y la URL
   pública. No guardes tokens, llaves ni datos privados en el repositorio.

## Licencias y contacto

El código propio y los ejemplos sintéticos se ofrecen bajo
[MIT](LICENSE). La biblioteca NEFIS de Deltares conserva sus avisos y
los términos aplicables de LGPL-2.1; su fuente y script de compilación
están junto al binario. Véanse [AVISOS.md](AVISOS.md) y el archivo de
[procedencia nativa](native/README.md). No se redistribuyen modelos,
datos de la tesis ni software de terceros ajeno al conversor.

Si quieres apoyar el proyecto con una donación voluntaria,
[¡contáctame!](https://github.com/mapsm12/NefisReader/issues/new?title=Consulta%20sobre%20donaciones%20a%20NefisReader)
No publiques información personal ni de pago en un ticket.
