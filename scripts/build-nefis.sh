#!/usr/bin/env bash
# Build the 64-bit Linux C API only; the Python reader does not use Fortran.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
[[ $(uname -s) == Linux && $(getconf LONG_BIT) == 64 ]] || {
    echo "La compilación incluida requiere Linux de 64 bits." >&2; exit 1;
}
if [[ $# != 1 ]]; then
    echo "Uso: bash scripts/build-nefis.sh /ruta/nueva/libnefis.so" >&2
    exit 2
fi
output=$1
[[ ! -e $output && ! -L $output ]] || {
    echo "El destino ya existe: $output" >&2; exit 1;
}
build=$(mktemp -d)
trap 'test -z "${build:-}" || rm -r -- "$build"' EXIT
(cd "$repo/native" && sha256sum -c source.sha256)
tar -xzf "$repo/native/deltares-nefis-source.tar.gz" -C "$build"
component="$build/src/utils_lgpl/nefis/packages/nefis"
# config.h is included by gp.c on Linux. Neither gp.c nor the C API uses
# Fortran mangling; the upstream config defines it only for Fortran wrappers.
touch "$build/config.h"
flags=(-O2 -fPIC -D_FILE_OFFSET_BITS=64 -DPTR8 -Dlinux -DLINUX64 -D_IA64_ -D_LIB
       -I"$component/include" -I"$build/src/version_includes" -I"$build")
objects=()
for unit in c2c df er gp gt hs oc pt rt wl-xdr; do
    "${CC:-cc}" "${flags[@]}" -std=gnu99 -c "$component/src/$unit.c" -o "$build/$unit.o"
    objects+=("$build/$unit.o")
done
"${CXX:-c++}" "${flags[@]}" -c "$component/src/nefis_version.cpp" -o "$build/version.o"
"${CC:-cc}" -shared -Wl,--no-undefined -Wl,-soname,libnefis.so \
    -o "$build/libnefis.so" "${objects[@]}" "$build/version.o" -lm
mkdir -p -- "$(dirname -- "$output")"
cp -n -- "$build/libnefis.so" "$output"
