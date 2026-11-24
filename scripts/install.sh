#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python=${PYTHON:-python}
[[ $(uname -s) == Linux && $(getconf LONG_BIT) == 64 ]] || {
    echo "Instalador disponible para Linux de 64 bits." >&2; exit 1;
}
"$python" -c 'import sys; sys.exit("Se requiere Python 3.9 o posterior" if sys.version_info < (3, 9) else 0)'
install_target=$repo
if [[ ${1:-} == --extra ]]; then
    case "${2:-}" in
        mcp|mcp,analysis|analysis,mcp)
            "$python" -c 'import sys; sys.exit("El MCP requiere Python 3.10 o posterior" if sys.version_info < (3, 10) else 0)'
            ;;
        analysis) ;;
        *) echo "Use --extra mcp, --extra analysis o --extra mcp,analysis" >&2; exit 2 ;;
    esac
    install_target="$repo[$2]"
    shift 2
fi
prefix=$("$python" -c 'import sys; print(sys.prefix)')
if [[ -z ${CONDA_PREFIX:-} ]] && "$python" -c 'import sys; sys.exit(sys.prefix != sys.base_prefix)'; then
    echo "Activa primero un entorno virtual Python o Conda." >&2
    exit 1
fi
dest="$prefix/lib/nefisreader/libnefis.so"
binary="$repo/native/linux-x86_64/libnefis.so"
stage=$(mktemp -d)
trap 'test -z "${stage:-}" || rm -r -- "$stage"' EXIT
probe() {
    "$python" -c 'import ctypes, sys; print("API NEFIS disponible:", ctypes.CDLL(sys.argv[1]).Crenef.__name__)' "$1"
}
if [[ -L $dest ]]; then
    echo "No se reemplazará el enlace $dest." >&2; exit 1
elif [[ -f $dest ]]; then
    probe "$dest"
    printf 'Se conserva la biblioteca existente en %s\n' "$dest"
else
    if [[ ${NEFIS_BUILD_FROM_SOURCE:-0} == 1 || $(uname -m) != x86_64 ]] ||
       ! (cd "$repo/native" && sha256sum -c linux-x86_64.sha256) ||
       ! probe "$binary"; then
        binary="$stage/libnefis.so"
        bash "$repo/scripts/build-nefis.sh" "$binary"
        probe "$binary"
    fi
    mkdir -p -- "$(dirname -- "$dest")"
    cp -n -- "$binary" "$dest"
fi
"$python" -m pip install "$@" "$install_target"
probe "$dest"
printf 'Listo: %s/bin/d3dnefis --help\n' "$prefix"
