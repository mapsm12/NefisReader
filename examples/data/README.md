# Parejas NEFIS de ejemplo

Son archivos **sintéticos** generados por
[`crear_demo.py --grids`](../crear_demo.py); no son mediciones ni
salidas de la tesis. El ejemplo WAVE usa nombres y estructura de
variables comprobados al leer una corrida real del Callao. El
ejemplo FLOW enseña la lectura de capas; no sustituye la geometría ni
las convenciones del archivo `trim` de una corrida real.

| Pareja | Variables | Orden del array que devuelve el lector |
|---|---|---|
| `wavm-demo-2d.dat/.def` | `HSIGN`, `RTP`, `DIR`, `XP`, `YP` | registro, fila, columna: `(2, 3, 4)` |
| `trim-demo-3d.dat/.def` | `U1`, `V1` | registro, capa, fila, columna: `(2, 3, 3, 4)` |

Para regenerar las parejas en otro directorio:
`python examples/crear_demo.py /ruta/a/demo --grids`.
Para extraer un plano, corte y perfil, usa
[`leer_mallas.py`](../leer_mallas.py).

### Aplicarlo a la corrida del Callao

Con tu pareja real `wavm-test00-grid_callao.dat/.def`, puedes consultar
el registro de altura sin convertir primero:

```bash
d3dnefis /ruta/corrida/wavm-test00-grid_callao.dat --inventory
python examples/leer_nefis.py /ruta/corrida/wavm-test00-grid_callao.dat \
  --group map-series --element HSIGN
```

En la corrida usada para comprobar el lector, `HSIGN`, `RTP`, `DIR`,
`DEPTH`, `XP/YP` y `TRANSP_X/Y` tienen forma cruda `(1, 301, 201)`.
El primer eje es un registro; esto corresponde a un campo horizontal,
no a un volumen con capas. En FLOW, revisa la posición de cada variable
en la malla escalonada y la coordenada vertical antes de combinar
componentes o convertir un índice de capa en metros.
