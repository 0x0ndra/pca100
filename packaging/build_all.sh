#!/usr/bin/env bash
set -euo pipefail
DIR="$(dirname "$0")"
bash "$DIR/build_app.sh"
bash "$DIR/notarize.sh"
bash "$DIR/make_dmg.sh"
echo "==> Done. Ship the DMG in dist/"
