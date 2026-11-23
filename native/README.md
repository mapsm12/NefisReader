# Biblioteca NEFIS de Deltares

Este directorio contiene una compilación independiente de la API C de NEFIS
para Linux x86-64 y las fuentes correspondientes. No incluye los motores
Delft3D/SWAN ni bibliotecas privadas de un clúster.

- Proyecto original: [Deltares/Delft3D](https://github.com/Deltares/Delft3D).
- Revisión: [`5c22757c63ca3fd7a7440baaa3447c86414f5761`](https://github.com/Deltares/Delft3D/tree/5c22757c63ca3fd7a7440baaa3447c86414f5761/src/utils_lgpl/nefis).
- El archivo `deltares-nefis-source.tar.gz` incluye los archivos fuente y
  cabeceras del componente, las cabeceras de versión, `AUTHORS`, el
  `COPYING` original y el texto de LGPL-2.1. Los avisos de los archivos se
  preservan; la biblioteca se redistribuye bajo los términos aplicables
  de LGPL-2.1. La biblioteca mantiene la vinculación dinámica y se puede
  sustituir mediante `NEFIS_LIB` o `--nefis-lib`.
- Construcción: `bash scripts/build-nefis.sh /ruta/nueva/libnefis.so`.
  El script genera un `config.h` mínimo y no altera fuentes de Deltares.
  Solo compila la API C que usa este proyecto; no incluye los wrappers
  Fortran. Este binario se compiló con GCC 12.2 sobre Linux.
- Verificación: `(cd native && sha256sum -c source.sha256 && sha256sum -c linux-x86_64.sha256)`.
