#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
# Note: matched by SHA-1 hash, not name — the keychain's cert CN drops the
# diacritic in the operator's first name entirely (renders as "Ondej
# Vlasek"), and matching by name string is fragile across locales/encodings.
IDENTITY="${CODESIGN_IDENTITY:?set CODESIGN_IDENTITY to your Developer ID hash}"
ENTITLEMENTS="$REPO/packaging/entitlements.plist"

echo "==> Frontend build"
(cd frontend && npm ci && npm run build)

echo "==> PyInstaller"
rm -rf build dist
(cd backend && uv run pyinstaller --clean --noconfirm ../packaging/PCA-100.spec --distpath ../dist --workpath ../build)

APP="$REPO/dist/PCA-100.app"
echo "==> Codesign (hardened runtime, deep)"
# Note: this has failed once with a transient errSecInternalComponent error
# during --deep signing of a large bundle; a plain retry of this command
# resolved it with no config change.
codesign --force --deep --options runtime --timestamp \
  --entitlements "$ENTITLEMENTS" --sign "$IDENTITY" "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "built $APP"
