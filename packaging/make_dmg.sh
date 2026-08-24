#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP="$REPO/dist/PCA-100.app"
VERSION="$(cd "$REPO/backend" && uv run python -c 'import pca; print(pca.__version__)')"
DMG="$REPO/dist/PCA-100-$VERSION.dmg"
# Note: matched by SHA-1 hash, not name — same identity used to sign the .app
# in build_app.sh. See the comment there.
IDENTITY="${CODESIGN_IDENTITY:?set CODESIGN_IDENTITY to your Developer ID hash}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
rm -f "$DMG"
hdiutil create -volname "PCA-100" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
codesign --force --timestamp --sign "$IDENTITY" "$DMG"
codesign --verify --verbose=2 "$DMG"
echo "built $DMG"
