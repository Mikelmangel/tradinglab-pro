#!/usr/bin/env bash
set -e
echo "TradingLab Pro v2.0 — Instalador"
for cmd in python3.12 python3.11 python3.10 python3; do
  if command -v $cmd &>/dev/null; then
    VER=$($cmd -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}')")
    MINOR=$(echo $VER | cut -d. -f2)
    [ "$MINOR" -ge 10 ] && { PYTHON=$cmd; break; }
  fi
done
[ -z "$PYTHON" ] && { echo "ERROR: Python 3.10+ requerido"; exit 1; }
cd "$(dirname "$0")/.."
$PYTHON installer/install.py
