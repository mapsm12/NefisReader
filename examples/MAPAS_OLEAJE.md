# Mapas: batimetría, altura de ola y vectores

[Ver las figuras en la web](https://mapsm12.github.io/NefisReader/docs/#mapas).
Los campos se generan para una **bahía ficticia**; no se ejecuta un
modelo y no se usan datos del Callao. El ejemplo recorre la cadena
completa: campos sintéticos → NEFIS `.dat/.def` → NetCDF →
mapas Matplotlib.

Con el entorno de NefisReader activado, desde el repositorio:

```bash
bash scripts/install.sh --extra analysis
caso="$(mktemp -d)"
python examples/crear_demo.py "$caso" --map
d3dnefis "$caso/wavm-bahia-sintetica.dat"
python examples/graficar_oleaje.py \
  "$caso/NETCDF_EXPORT/wavm-bahia-sintetica.nc" \
  --synthetic --outdir "$caso/figuras"
```

Se generan `batimetria_vectores.png` y `altura_isobatas.png`.
Los nombres `map_series__XP`, `YP`, `DEPTH`, `HSIGN`,
`TRANSP_X` y `TRANSP_Y` corresponden a los elementos exportados
(todos con el mismo prefijo `map_series__`). El script lee un
registro, convierte X/Y de m a km y el transporte de W/m a kW/m.
El largo de las flechas representa la magnitud del vector mediante
la escala dibujada; las flechas no son corrientes ni la dirección
náutica de procedencia de la ola.

Para probar un NetCDF propio, quita `--synthetic` y cambia la ruta
de entrada. Primero valida con el inventario que la malla sea plana,
los seis campos estén alineados, los ejes sean
`[registro, fila, columna]`, y que las convenciones de profundidad
positiva y componentes X/Y coincidan. La máscara seca del ejemplo es
`DEPTH <= 0`; si tu caso tiene otros sentinelas o una máscara
independiente, adapta el script antes de interpretar la figura.
