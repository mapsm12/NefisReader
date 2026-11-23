# NefisReader — Delft3D 4 NEFIS a NetCDF con Python

Versión instalable del conversor `d3dnefis` de Miguel Andrade Pereira
([@mapsm12](https://github.com/mapsm12)). Lee parejas NEFIS `.dat` + `.def`
mediante la API C de la biblioteca NEFIS con Python y `ctypes`, y exporta
los campos numéricos a NetCDF-4. No requiere MATLAB ni volver a ejecutar
Delft3D. El flujo probado es Delft3D 4-WAVE en Linux x86-64.

## 1. Instalación

Se necesita Python 3.9 o posterior, NumPy, netCDF4 y una **biblioteca NEFIS
compatible con el Python y el sistema operativo**. Este repositorio no
incluye ni instala binarios Delft3D. Si no tienes la biblioteca, consulta
la [instalación oficial de Delft3D 4](https://oss.deltares.nl/web/delft3d/get-started)
y las [instrucciones de compilación de Deltares](https://github.com/Deltares/Delft3D/blob/main/doc/development.md)
para obtener los binarios correspondientes.

```bash
git clone https://github.com/mapsm12/NefisReader.git
cd NefisReader
conda env create -f environment.yml
conda activate nefisreader
python -m pip install .
d3dnefis --help
```

Alternativa, con Python y pip: `python -m venv .venv`,
`source .venv/bin/activate` y `python -m pip install '.[analysis]'`.
No hace falta instalar el extra de análisis si solo quieres convertir.

En Linux, localiza la biblioteca en tu propia instalación:

```bash
find /ruta/al/Delft3D4 -type f -iname '*nefis*.so*'
export NEFIS_LIB=/ruta/al/Delft3D4/lib/nefis.so
ldd "$NEFIS_LIB"  # Si aparecen «not found», carga el entorno de tu instalación.
```

Se busca en este orden: `--nefis-lib`, `NEFIS_LIB`, y rutas comunes bajo
`DELFT3D_HOME` (`lib`, `lib64`, `lib/delft3d`, `bin`). Usa
`--nefis-lib /ruta/...` para escoger una biblioteca sin exportar variables.
No apuntes a un ejecutable ni mezcles bibliotecas de compilaciones distintas.
No se afirma compatibilidad con bibliotecas Windows/macOS.

## 2. Inventariar y convertir

```bash
# Inspección de las parejas y sus grupos: no escribe NetCDF.
d3dnefis /ruta/a/corrida --inventory --json

# Convierte la corrida. También puedes invocar d3dnefis dentro del directorio.
d3dnefis /ruta/a/corrida

# Una pareja concreta y destino nuevo.
d3dnefis /ruta/a/corrida/wavm-caso.dat --output ./oleaje.nc

# Varios archivos de un caso, salida separada y menor memoria por bloque.
d3dnefis /ruta/a/corrida --outdir ./resultados --block-records 4
```

Al indicar un directorio la búsqueda es no recursiva. Cada archivo
`foo.dat` requiere `foo.def`; también puedes pasar `foo.def` o indicar
`--def-file` con una sola entrada. La salida predeterminada es
`corrida/NETCDF_EXPORT/foo.nc`. Si ya existe, se omite; usa `--force`
solo si quieres reemplazarla expresamente. No ejecutes dos conversiones
al mismo destino. El código de retorno 2 señala errores detectados;
`--json` añade información al resumen de consola, no produce JSON puro.

## 3. Leer y graficar en Python

- [Lectura directa e inventario NEFIS](examples/leer_nefis.py):
  `python examples/leer_nefis.py /ruta/wavm-caso.dat`.
- [Inspeccionar y graficar NetCDF WAVE](examples/leer_netcdf.py):
  `python examples/leer_netcdf.py oleaje.nc --plot altura.png --record 0`.

```python
import xarray as xr

with xr.open_dataset("oleaje.nc", decode_times=False, mask_and_scale=False) as ds:
    print(ds.sizes)
    print(list(ds.data_vars))
    for name in ("map_series__HSIGN", "map_series__DEPTH", "map_series__RTP"):
        if name in ds:
            print(name, ds[name].shape, ds[name].attrs)
```

El NetCDF conserva **valores crudos**: cada variable tiene sus propias
dimensiones (dimensiones del grupo seguidas por las dimensiones del
elemento en orden invertido). Los atributos conservan grupo, celda,
elemento, tipo y las unidades/descripciones cuando están disponibles.
No es una conversión CF y no reconstruye coordenadas, calendario, datum,
máscara, dirección ni malla escalonada. No se exportan campos CHARACTER.
Antes de interpretar una variable, verifica metadatos, ejes, unidades y
sentinelas contra la corrida. Para WAVE, `HSIGN` es el campo típico de
altura significativa, pero `XP/YP` pueden venir en otro grupo. Para FLOW
hay que inspeccionar sus propios grupos y geometría; no se aplica el
ejemplo de WAVE automáticamente. Los archivos ya NetCDF de Delft3D FM
o tablas de SWAN directo no son entradas de este conversor.

## Pruebas

`python -m pip install '.[test]'` y `python -m pytest -q`.
Las pruebas unitarias no necesitan bibliotecas o datos Delft3D. Para
probar tu instalación de extremo a extremo usa una pareja **de tu
propiedad**, primero con `--inventory` y luego hacia un destino nuevo;
verifica los valores y las formas. Los datos y binarios usados en la
comprobación local no se distribuyen en el repositorio.

La licencia de tu biblioteca y la de tus datos se gestionan por separado.
Este repositorio no redistribuye código ni binarios de Deltares.
