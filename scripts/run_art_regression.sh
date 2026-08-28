#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
mkdir -p tests/.art-regression

python_bin="${PYTHON_BIN:-python3}"
if ! command -v "$python_bin" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    python_bin=python
  else
    echo "Python not found. Set PYTHON_BIN to a Python with Pillow and NumPy." >&2
    exit 2
  fi
fi

"$python_bin" scripts/generate_gold_fixtures.py
"$python_bin" -m unittest discover -s tests -p 'test_*.py' -v
"$python_bin" scripts/validate_anchor_pack.py --json tests/.art-regression/anchor-pack.json
"$python_bin" scripts/motion_audit.py \
  tests/gold/motion/walk_0.png \
  tests/gold/motion/walk_1.png \
  tests/gold/motion/walk_2.png \
  --json tests/.art-regression/motion.json
"$python_bin" scripts/palette_audit.py tests/gold/palette \
  --json tests/.art-regression/palette.json

echo "Art regression: PASS"
echo "Release gate note: run 'python scripts/validate_anchor_pack.py --strict' after approved Gold Anchors are added."
